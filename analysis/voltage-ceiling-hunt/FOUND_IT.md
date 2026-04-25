# GPU voltage ceiling: located

The 800 mV GPU rail ceiling is enforced by **autonomous hardware DVFS**, not
the kernel regulator framework. ftrace + kprobe diagnostics on the device
proved this end-to-end.

## Diagnostic path

Kprobes installed on the regulator framework entry points:

```
p:reg_set        regulator_set_voltage
p:reg_do_set     _regulator_do_set_voltage
p:reg_call_sel   _regulator_call_set_voltage_sel
p:reg_sel_regmap regulator_set_voltage_sel_regmap
p:rmap_update    regmap_update_bits_base
p:rmap_write     regmap_write
```

### Sanity check: debugfs override

`echo 850 > /sys/kernel/debug/DCDC_GPU/voltage` then `echo 800` traced as:

```
reg_sel_regmap: sel=272   (= 850 mV via 200 mV + (272-64)*3.125)
reg_sel_regmap: sel=256   (= 800 mV)
```

So debugfs writes go through `regulator_set_voltage_sel_regmap`. None of
the higher-level `regulator_set_voltage`, `_regulator_do_set_voltage`,
or `_regulator_call_set_voltage_sel` were called - debugfs deliberately
skips constraint validation. Confirmed.

### Mali OPP transition: pin GPU 384 -> 900 MHz

Trace captured during the transition (rail observed to go 700 -> 800 mV):

```
rmap_update: regulator_update_bits_base reg=0x140 mask=0x7 val=4
```

That is the ONLY regmap activity the kernel did. None of the regulator
framework primitives fired. The kernel did NOT write to the SC2730
DCDC_GPU vsel register at all during the OPP transition.

`reg=0x140 / mask=0x7 / val=4` decodes as: write OPP index 4 to bits 0-2
of GPU syscon offset 0x8c (the `dvfs_index_cfg` register documented in
the BootROM walkthrough). Note that the address shows as 0x140 because
the mali driver passes the Mali sub-block offset into the GPU syscon
which the kernel decodes via regmap.

### So what changed the SC2730 DCDC_GPU vsel register?

Direct SPI dump of SC2730 regs 0x1830-0x1880 before/after the same
transition shows:

```
1854: 0000fae0  (idle, sel=0xe0=224, voltage=700 mV)
1854: 0000fb00  (loaded, sel=0x100=256, voltage=800 mV)
```

So SC2730 register 0x1854 is the DCDC_GPU vsel, and SOMETHING wrote it
to 0x100 during the transition. Since the kernel did no regulator framework
calls, the write came over the autonomous I2C / control path from the
top DVFS controller (322a0000).

## The voltage-grade table

The top DVFS controller (`syscon@322a0000`) holds the per-grade vsel values
for the GPU rail at register offsets 0xe4 and 0xe8:

```
0xe4 = 0x0401e0e0  --  grades 0-2 packed as 9-bit fields at offsets 0/9/18
0xe8 = 0x00020110  --  grades 3-5
0xec = 0x0401e0e0  --  CPU? same value, paired
0xf0 = 0x00020100  --  CPU? similar to 0xe8
```

Decoded:

| Grade | Reg | Field | sel | Voltage |
|-------|-----|-------|-----|---------|
| 0 | 0xe4 | bits 0-8   | 0x0e0 = 224 | **700 mV** |
| 1 | 0xe4 | bits 9-17  | 0x0f0 = 240 | **750 mV** |
| 2 | 0xe4 | bits 18-26 | 0x100 = 256 | **800 mV** |
| 3 | 0xe8 | bits 0-8   | 0x110 = 272 | **850 mV (PRE-PROGRAMMED, UNUSED!)** |
| 4 | 0xe8 | bits 9-17  | 0x100 = 256 | 800 mV (duplicate of grade 2) |
| 5 | 0xe8 | bits 18-26 | 0x000 = 0   | 0 mV (uninitialised) |

The voltage formula matches what we observed empirically (grades 0/1/2
== rail voltages 700/750/800 we see at OPP 0, 1-2, 3-7).

**Grade 3 is pre-programmed to 850 mV but NO OPP slot uses it.**

## How OPP -> grade is mapped

GPU syscon registers 0x48-0x64 (`core_index0_map` ... `core_index7_map`)
are 8 slots. Each register has bits 14-16 holding a 3-bit grade index:

```
0x48 = 0x00300001  -> grade 0
0x4c = 0x00304002  -> grade 1
0x50 = 0x00304003  -> grade 1
0x54 = 0x00308004  -> grade 2
0x58 = 0x00308005  -> grade 2  (TOP OPP slot 4)
0x5c-0x64 same as 0x58
```

Stock OPP table maps slot 4 (the top OPP, freq 850 / 900 MHz) to grade 2
which is 800 mV. To get 850 mV at the top OPP, slot 4 needs to map to
grade 3 instead.

## Patch options

**Option A (minimal):** change GPU syscon reg 0x58 bits 14-16 from 0b010
to 0b011. One register write, one byte difference (0x00308005 -> 0x0030c005).
Only affects slot 4 (top OPP). Persists until reboot.

**Option B (table-side):** change top dvfs ctrl reg 0xe4 bits 18-26 from
0x100 to 0x110. Raises grade 2 voltage from 800 mV to 850 mV globally.
Affects every OPP slot mapped to grade 2 (slots 3-7), so OPPs 768/900 MHz
all get 850 mV.

Option A is cleaner. Both are a 4-byte register write.

## Applying the patch

Neither register is in `/dev/mem` reach (no /dev/mem on this device).
The GPU syscon and top dvfs ctrl are both behind regmap with read-only
debugfs interfaces. Three feasible routes:

1. **Kernel module patch**: a tiny .ko that does
   `syscon_regmap_lookup_by_phandle()` for the GPU syscon and
   `regmap_update_bits()` to set bits 14-16 of reg 0x58 to 3. Load via
   `insmod` after Mali probe finishes (so the stock value isn't
   overwritten by the boot-time programmer).

2. **Mali driver patch**: modify `mali_gondul.ko`'s `mali_clock_on` (which
   is the function we previously identified as iterating over
   core_indexN_map regs) to override the value for slot 4. Less surgical
   since it requires patching a vendor-shipped module and re-signing the
   vendor_boot.

3. **Pre-OPP-transition init.rc service**: keep the current debugfs
   `echo 850 > /sys/kernel/debug/DCDC_GPU/voltage` workaround. We already
   know this works (exp 028, 029) but it's a daemon-style override and
   the rail still drops on every Mali OPP transition until the next
   override write.

Option 1 is the cleanest minimal-impact patch. Estimated effort: a few
hours to write/build/sign + flash test.

## Who programs core_indexN_map at boot?

Not yet identified. The mali_gondul.ko `mali_platform_init` function only
calls `regmap_update_bits_base` once (at file offset 0x4287c per earlier
analysis), and that one call is for some other purpose (probably the
top_force_shutdown register). The `mali_clock_on` function does many
regmap writes including iterating a table at .data+0x1d80, but those go
to the regs we already documented (sw_dvfs_ctrl, freq_upd_cfg, ...).

So core_indexN_map values 0x00300001, 0x00304002 etc are probably
programmed by:
- SPL or uboot during early init (we already searched - no matches)
- Or another kernel module during probe (apsys-dvfs.ko, sprd-top-dvfs.ko)
- Or hardware default state baked into the SoC

Either way, the values are stable post-boot. A patch that runs after
Mali initialises and rewrites slot 4's grade index will achieve 850 mV
on the top OPP.

## Files

- `FOUND_IT.md` (this file) - write-up
- `README.md` - earlier (now outdated) hypothesis exploration
- (other artefacts from the earlier hunt, kept for provenance)

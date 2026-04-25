# Voltage-grade ceiling hunt: SPL vs UBoot

The OC investigation in `oc_test/` established that the GPU rail caps at
800 mV and CPU caps at ~1050 mV regardless of device-tree voltage
requests. The kernel-module RE in `kernel_rev/` and the BootROM
walkthrough in `analysis/bootrom/` ruled out the BootROM, the Mali
driver, and the SPRD HW DVFS modules as the source of the clamp.

This note records what we find when we sweep stock SPL and stock UBoot
for PMIC / DCDC / voltage references.

## Tooling

Both stock images are at `examples/` with the standard DHTB+SIMGHDR
header. To get the raw ARM64 code, strip 0x200 bytes:

```python
import struct
d = open('examples/uboot_stock.img','rb').read()
data_sz = struct.unpack('<I', d[0x30:0x34])[0]
open('uboot_stock_code.bin','wb').write(d[0x200:0x200+data_sz])
```

This yields:
- `spl_stock_code.bin` - 0xed50 bytes (60 KB)
- `uboot_stock_code.bin` - 0xda820 bytes (875 KB)

Both are AArch64. SPL entry is a simple branch + nop preamble; UBoot
entry is the standard `b 0x28 ; nop` early stub.

## SPL (splloader)

### Strings

The only PMIC-related ASCII string is `pmic id :`. No regulator names,
no DCDC strings, no `sc2730_*` symbols, no voltage strings.

### Voltage uV literals

| Value | Count | First offsets |
|-------|------:|---------------|
| 700000 | 0 | - |
| 800000 | 6 | 0xeb7f, 0xeba7, 0xebcf, 0xec6f, 0xec97 |
| 850000 | 0 | - |
| 1000000 | 3 | 0xd0fd, 0xd161, 0xd1ad |
| 1050000 | 0 | - |
| 1200000 | 1 | 0xd101 |

The cluster at 0xeb7f/eba7/ebcf (28-byte stride) is consistent with a
small lookup or DDR training table, not a full PMIC voltage grade table.

### SC2730 register addresses

Pattern `0x3212181c` (LE bytes `1c 18 12 32`) appears 9 times. This is
the SC2730 PMIC enable/status register seen via the SPI window. SPL
needs to enable the PMIC SPI / set DCDC enables to bring up the rest
of the SoC, but the breadth of code is small: SPL is responsible for
DDR init, eMMC bring-up, and load-and-verify of trustos / sml / uboot.
It does not run a full regulator framework.

### Conclusion - SPL

SPL touches the PMIC enable register and a couple of voltages around
800 mV / 1000 mV / 1200 mV (likely DDR or a coarse SoC core voltage).
It is **not** the source of the per-DCDC voltage grade table that
clamps vddgpu at 800 mV. SPL is too small for that, and the only
strings that reach into "PMIC" territory are 1 line.

## UBoot

### Strings - PMIC / regulator

UBoot is a different story. Direct hits:

```
sc2730_dcdc_get_voltage
sc2730_regulator_probe
sc2730_power_control_bind
sc2730_bind
pmic_lowpower_config
pmic2731_wa
pmic_efuse.c   (full path leak)
pmic node not exist!!!
pmic read fail, %d
pmic write fail, %d
regu_dcdc %p (%s) %d = %d %+dmv (trim=%d step=%duv);
regu_ldo %p (%s) %d = %d %+dmv (trim=%d step=%duv);
DCDC_CPU_DTM   DCDC_GPU_DTM   DCDC_CORE_DTM   DCDC_MODEM_DTM   DCDC_MEM_DTM   DCDC_MEMQ_DTM
DCDC_GEN0_DTM  DCDC_GEN1_DTM  DCDC_SRAM_DTM   DCDC_WPA_DTM
DCDC_CPU_CF    DCDC_GPU_CF    DCDC_MODEM_CF   DCDC_WPA_CF
DCDC_CPU_STBOP DCDC_GPU_STBOP DCDC_CORE_STBOP DCDC_MODEM_STBOP DCDC_SRAM_STBOP
DCDC_CPU_ZCD   DCDC_GPU_ZCD   DCDC_CORE_ZCD   DCDC_MODEM_ZCD   DCDC_MEM_ZCD
DCDC_MEMQ_ZCD  DCDC_GEN0_ZCD  DCDC_GEN1_ZCD   DCDC_WPA_ZCD     DCDC_SRAM_ZCD
DCDC          DCDC_CPU       DCDC_GPU         DCDC_CORE        DCDC_MODEM
DCDC_MEM      DCDC_MEMQ      DCDC_GEN0        DCDC_GEN1
```

Path leak from the binary:
```
/home/dell/code/work/sprd/T618/RG555/RG555_Android_user/bsp/bootloader/u-boot15/drivers/misc/pmic_efuse.c
```

So this is U-Boot v15.x with the upstream Spreadtrum sc2730_regulator
driver compiled in. UBoot is the layer that runs `sc2730_regulator_probe`
and walks the DCDC list.

### DCDC config table (0xb83ef onwards)

Repeating 16-byte entries. The aligned dump at 0xb8470 shows:

```
0xb8470: ff 01 00 00  58 02 00 00  02 00 00 00  00 00 00 00
         ^^^^^^^^^^^  ^^^^^^^^^^^  ^^^^^^^^^^^  ^^^^^^^^^^^
         mask=0x1ff   sel=0x258    op=0x02      pad=0
0xb8480: 35 0c 00 00  00 00 00 00  10 00 00 00  00 00 00 00
         ^^^^^^^^^^^               ^^^^^^^^^^^
         step=0xc35                flag=0x10
                                   (=3125 uV/step)
```

The step value `0xc35 = 3125` matches the SC2730 DCDC step we already
documented from `sc2730-regulator.ko` (kernel side). The `0x1ff` mask
(9 bits) matches the SC2730 DCDC vsel field width.

Surrounding entries reference register addresses in the
`0x32_12_18_xx` and `0x32_12_19_xx` ranges, which are SC2730 PMIC
registers seen via the SPI window mapped through the AP-side SPI
controller. Each table row describes a single MMIO write to the SC2730
chip with mask + value.

### UV literals - corrected with alignment check

Initial scan reported 12 occurrences of 800000 (0xc3500) clustered at
0xb847f-0xb87c7. **Re-running the same search with 4-byte alignment
constraint shows zero matches** for 800000, 850000, 700000, 750000
or 900000 across the entire uboot binary. The 12 "hits" were all
**misaligned** matches of the byte sequence `\x00\x35\x0c\x00`, which
is the natural placement of the constant `0x00000c35` (= 3125 = the
SC2730 DCDC step in uV) at u32 boundaries followed by a zero u32 at
the next boundary.

| Value | Aligned count | Notes |
|-------|--------------:|-------|
| 700000 | 0 | - |
| 750000 | 0 | - |
| 800000 | 0 | - |
| 850000 | 0 | - |
| 900000 | 0 | - |
| 1000000 | 1 | 0x87ae0 (single literal, isolated) |
| 1050000 | 0 | - |

So uboot does NOT hardcode 800 mV. The voltage targets for the various
DCDCs come from the device tree blob that uboot parses, not from
constants compiled into the binary.

### Re-analysed register-write table

The table at file offset 0xb83a0 is a 48-byte-stride array of register
init descriptors used by uboot during PMIC bring-up. A function at
text offset 0x46290 indexes into this array and OR-sets bit 0x40 in
some target register. The table contains many SC2730 SPI window
addresses (0x32_12_18_xx for DCDC region, 0x32_12_19_xx for LDOs/clk),
masks (`0x1ff` matching the 9-bit DCDC vsel field), step values
(`0xc35` = 3125 uV) and timing values, but NOT explicit voltage targets.

The presence of `0x32121894` (DCDC vsel?) plus the mask `0x1ff` plus
value `0x258` (= 600 selector) at one entry would correspond to
output_uV = 200000 + 600 * 3125 = **2075000 uV (2075 mV)**, which is
clearly wrong for any of the rails we care about. Values like `0x258`
and `0x320` may instead be timing or current-trim values, with the
voltage being read from DT and computed at runtime.

## Revised conclusion

Both the **uboot binary code** and the **uboot embedded device tree**
have been ruled out as the source of a hardcoded 800 mV ceiling on
the GPU rail. There is no compile-time 800 mV literal anywhere in the
uboot binary. Voltage targets are read from DT at runtime.

Re-examining the experimental evidence in `oc_test/CHANGELOG.md`:

- exp 022 with DT operating-points = 1000 mV: rail stayed at 800 mV.
- exp 028 with userspace `echo 850 > /sys/kernel/debug/DCDC_GPU/voltage`:
  rail held at 850 mV across Mali OPP transitions.

Both writes go through the same `ops->set_voltage_sel_regmap` callback
in the SC2730 regulator driver (verified in sc2730-regulator.ko
disassembly). The difference must be in what happens **before** that
callback is invoked - either a consumer-side constraint check that
clamps the request, or a regulator-state-tracking issue that says
"no change needed" when in fact the rail is currently below target.

This is now a **kernel-side** problem, not a uboot-side problem. The
right next step is to instrument the kernel's `regulator_set_voltage`
path (or trace it via ftrace events on the device) to see exactly
why Mali's request for 850 mV doesn't reach the SPI write. Candidate
mechanisms:

1. The SC2730 regulator's `regulator_constraints` were seeded by
   uboot DT to a smaller max than 1596 mV at handover (need to look
   at the kernel-side DT, not the uboot DT).
2. A constraint elsewhere in the consumer chain (gpu-supply graph)
   limits the aggregate max.
3. The Mali driver itself (or some PM framework code) caches a
   "current voltage" of 800 mV and short-circuits subsequent calls
   that ask for higher than current+something.

Patching uboot would not address any of those.

## Files

- `notes.md` - this file
- `spl_strings.txt` - all PMIC/voltage strings from SPL
- `uboot_strings.txt` - all PMIC/voltage strings from UBoot
- `uboot_dcdc_table_dump.txt` - aligned hex dump of the 16-byte-entry
  DCDC config table at uboot offset 0xb83ef onwards
- `uboot_uv_literals.txt` - all uV-magnitude integer hits in uboot
  with their offsets

These artefacts are starting points for the next pass; we have not
yet identified the per-DCDC entry in the table or the patch strategy.

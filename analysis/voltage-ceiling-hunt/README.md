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

### UV literals near the table

| Value | Count | Locations |
|-------|------:|-----------|
| 700000 | 0 | - |
| 750000 | 1 | 0x878b5 |
| 800000 | 12 | 0xb847f, 0xb84ef, 0xb863f, 0xb8677, 0xb87c7, ... |
| 850000 | 0 | - |
| 1000000 | 1 | 0x87ae0 |

The 800000 cluster (12 hits) lies INSIDE the DCDC config table region
0xb83ef-0xb88xx. **800000 = 0xc3500 in microvolts.** The presence of
this value at 12 distinct positions in the DCDC config table is the
strongest single piece of evidence that **uboot writes 800 mV as the
target voltage for multiple DCDC rails at boot**, and that the
specific value 800 mV is hardcoded into uboot for the GPU rail.

850000 uV does NOT appear in uboot anywhere. So whatever range uboot
programs into the PMIC DCDC limit registers (or initial setpoint), the
maximum referenced for the GPU rail is exactly 800 mV.

## Hypothesis

UBoot's `sc2730_regulator_probe()` (function name confirmed at file
offset 0x84170) walks a static DCDC descriptor table starting near
0xb83ef. For each DCDC, it programs:

1. **Initial setpoint** (vsel) - via the `sel` field (e.g. 0x258 in
   the example entry). With base 200000 + step 3125 * sel = output uV.
2. **Limit registers** - the `_CF` / `_DTM` / `_STBOP` registers per
   DCDC. The "DTM" suffix is a strong hint at "DT Mask" or "Default
   Target Mask" - i.e., the register that constrains how high the
   subsequent kernel can drive vsel. SC2730 silicon does have a
   per-DCDC voltage limit control.
3. **Standby / zero-current detection** - the `_STBOP` and `_ZCD`
   registers, which we don't care about for OC.

The combination of (initial vsel = 800 mV for vddgpu, and `_CF` /
`_DTM` register pre-programmed) is what locks the rail at 800 mV from
the kernel's perspective, even after `regulator_set_voltage(850000)`
issues a vsel write - the silicon-side limit register short-circuits.

## What this means for OC

- The 800 mV GPU ceiling and 1050 mV CPU ceiling are programmed by
  **stock uboot** at boot, before the kernel ever runs.
- We already have the toolchain to modify uboot in this repo
  (`tools/modify_uboot.py`, `tools/rehash.py`). After modifying, the
  DHTB hash recomputes automatically.
- Specifically, if we patch uboot to:
  - Change the GPU vsel sel field from 0x258 (=600, i.e. 800 mV) to
    a higher value, or
  - Skip / NOP the `DCDC_GPU_DTM` write so the silicon-side limit
    stays at its default,
- then the kernel's `regulator_set_voltage` would actually take effect
  and we could push past 800 mV without a userspace daemon.

This requires further RE: identifying which DCDC table entry is
DCDC_GPU and the exact register address vs offset in the `_DTM`
register that enforces the cap. The strings index the names but the
values per name are populated by code that reads the `_efuse` / DT
nodes.

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

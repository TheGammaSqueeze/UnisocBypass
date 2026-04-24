# UnisocBypass

Tools and analysis for bypassing Unisoc UMS512 (T618) firmware signature verification.

Developed and verified on the Anbernic RG Vita, which uses the Unisoc T618 SoC.

## What this does

Unisoc's UMS512 secure boot chain uses a proprietary DHTB + SIMGHDR signature format. The SPL (Secondary Program Loader) performs RSA-2048 signature verification on every image it loads (sml, trustos, uboot) and hangs in an infinite loop if any check fails. There is no unlock-state bypass in the SPL code.

However, the BootROM on this SoC only verifies the **DHTB SHA256 hash** (integrity check) when loading SPL from the eMMC boot partition. It does NOT verify the SIMGHDR RSA signature. This makes it possible to:

1. Patch SPL to NOP out all 4 RSA verify call sites
2. Update the DHTB hash to match the modified code
3. Flash the patched SPL to `mmcblk0boot0` via adb root
4. Subsequently flash any modified uboot/sml/trustos with just a hash update (no RSA re-signing needed)

## Chain of trust

```
BootROM (mask ROM)
  -> loads SPL from mmcblk0boot0
  -> checks DHTB SHA256 hash ONLY (integrity)
  -> does NOT verify SIMGHDR RSA signature
    -> SPL RSA-2048 verifies sml, trustos, uboot (4 call sites)
    -> SPL hangs in infinite loop on verification failure
      -> UBoot AVB verifies boot, vendor_boot, dtbo
      -> UBoot SKIPS AVB when bootloader is unlocked
```

After running `tools/patch_spl.py`:

```
BootROM loads patched SPL (DHTB hash valid)
  -> Patched SPL has all 4 verify calls NOPed to 0xD503201F
  -> Any sml, trustos, uboot passes verification (it is never actually checked)
    -> UBoot loads boot chain as before
```

## Quick start

Prerequisites:
- Python 3.6+
- `adb` with root access on the device
- Device already bootloader-unlocked (see "Prerequisites" below)

```bash
git clone git@github.com:TheGammaSqueeze/UnisocBypass.git
cd UnisocBypass

# 1. Back up current SPL and uboot from device
./scripts/backup.sh ./backups

# 2. Patch SPL (NOP verify calls + update hash)
python3 tools/patch_spl.py backups/mmcblk0boot0.bin patched_spl.img

# 3. Flash patched SPL to both eMMC boot partitions
./scripts/flash_spl.sh patched_spl.img

# 4a. Patch uboot for permanent unlock + AVB disabled + no SKIP VERIFY text/delay
python3 tools/patch_uboot_unlock.py backups/uboot_b.bin unlocked_uboot.img
./scripts/flash_uboot.sh unlocked_uboot.img

# 4b. Or modify uboot freely and rehash (see examples/uboot_modify_example.py)
# python3 tools/rehash.py my_modified_uboot.img
# ./scripts/flash_uboot.sh my_modified_uboot.img

adb reboot
```

## Repo layout

- `tools/` - Python tools for parsing, patching, and re-hashing DHTB images
- `scripts/` - Bash scripts for flashing and full workflow automation
- `docs/` - Detailed analysis documentation
- `examples/` - Stock and modified images for reference
- `analysis/` - SPL disassembly output and reverse-engineering notes
- `fdl/` - Unsigned FDL files for flashing on locked devices via `spd_dump`

## Documentation index

- [docs/WORKFLOW.md](docs/WORKFLOW.md) - step-by-step usage
- [docs/ANALYSIS.md](docs/ANALYSIS.md) - SPL RSA verify reverse-engineering
- [docs/CHAIN_OF_TRUST.md](docs/CHAIN_OF_TRUST.md) - boot-chain signing model
- [docs/DHTB_FORMAT.md](docs/DHTB_FORMAT.md) - DHTB header layout
- [docs/SIMGHDR_FORMAT.md](docs/SIMGHDR_FORMAT.md) - SIMGHDR signature block layout
- [docs/UBOOT_UNLOCK.md](docs/UBOOT_UNLOCK.md) - uboot permanent-unlock patch
- [docs/OC_FEASIBILITY.md](docs/OC_FEASIBILITY.md) - CPU/GPU overclock feasibility assessment
- [oc_test/CHANGELOG.md](oc_test/CHANGELOG.md) - OC/UV experiment log and comparison table
- [oc_test/COMPARISON.md](oc_test/COMPARISON.md) - per-experiment results vs stock baselines

## Overclocking

Once the patched SPL + uboot are installed, `vendor_boot.img` can be freely
modified and re-signed with just a DHTB hash update. This allows OC/UV
experiments by editing the DTB inside `vendor_boot`.

All experiments live in `oc_test/experiments/NNN-short-name/`:
- `modify.py` generates the modified DTS from a stock reference
- `modified.dts` is the produced DTS
- Three-mode bench (`cpu`, `gpu`, `both`) output in `cpu/`, `gpu/`, `both/`
- `REPORT.md` auto-generated with voltage evidence, thermal peaks, throughput, FPS
- `vendor_boot.img.signed.sha256` pins the exact image flashed

### Current baseline: exp 025

`oc_test/experiments/025-cpu2100-uv37.5-gpu900/` is the combined stable config:

| knob | change | verified in |
|------|--------|-------------|
| CPU LITTLE/BIG lower OPPs | UV -37.5 mV | exp 008, 014 (3x reproducibility) |
| CPU top OPP | 2002 -> 2100 MHz at stock 1050 mV | exp 019 both mode |
| GPU top OPP | 850 -> 900 MHz at stock 800 mV | exp 020 +17% FPS |
| Thermal trips | stock | exp 015, 017 showed raised trips crash |

Results (180 s per mode):

| mode | CPU MHz | GPU MHz | SoC pk | vs stock |
|------|--------:|--------:|-------:|----------|
| cpu | 2100 | 384 | 102.1 C | +18.6% CPU, -2.8 C |
| gpu | 1228 | 900 | 63.1 C | +17% FPS |
| both | 2100 | 472 | 105.0 C | -4.5% CPU, +1.1% FPS, -0.8 C |

### Known ceilings

DT overvolt requests above the hardware ceiling are silently ignored:
- CPU: cap ~1050 mV. Requests above (exp 019 tried 1075) still land at ~1009 mV.
- GPU: cap 800 mV. Requests above (exp 021 tried 850, exp 022 tried 1000) still land at 800 mV.

Adding `mali-supply` / `shadercores-supply` to the GPU DT node (exp 023, 024)
does not break the GPU ceiling. The Mali driver DOES read the DT voltage
correctly (`dmesg` shows `volt=850000`) but the rail still reads 800 mV.

A bypass path exists for the GPU: writing directly to
`/sys/kernel/debug/DCDC_GPU/voltage` calls `set_voltage_sel_regmap` directly
and succeeds. Not used in the baseline since it requires a userspace daemon
and has not been stability-tested long enough to ship.

Kernel module snapshots used for offline RE are committed to `kernel_rev/modules/`.

## Tools

| Tool | Purpose |
|------|---------|
| `tools/dhtb_parse.py` | Parse and display DHTB header + SIMGHDR fields from any signed Unisoc image |
| `tools/patch_spl.py` | Patch SPL: NOP all 4 RSA verify call sites and update DHTB/SIMGHDR hashes |
| `tools/rehash.py` | Recompute DHTB SHA256 + SIMGHDR data hash for any modified image |
| `tools/verify_image.py` | Check that a DHTB image has a valid hash (integrity test) |
| `tools/modify_uboot.py` | Replace strings in uboot and re-hash in one step |
| `tools/patch_uboot_unlock.py` | Patch uboot to permanently report unlocked, disable AVB, strip SKIP VERIFY text + delay |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup.sh` | Dump SPL (boot0/boot1) and uboot (_a/_b) from device |
| `scripts/flash_spl.sh` | Flash a patched SPL to both eMMC boot partitions |
| `scripts/flash_uboot.sh` | Flash a modified uboot to both slot partitions |
| `scripts/unpatch.sh` | Restore stock SPL from backup (recovery) |
| `scripts/full_workflow.sh` | End-to-end: backup, patch, flash everything |

## Prerequisites

You do **not** need an unlocked bootloader. The patched images work on both locked and unlocked devices, though the installation method differs.

**Option A - device already has adb root (unlocked or engineering build)**

Use `scripts/flash_spl.sh` and `scripts/flash_uboot.sh`, which write to eMMC via `adb shell dd`.

**Option B - stock locked device**

Use `spd_dump` with the included FDL files in `fdl/` to flash while the BootROM exploit (CVE-2022-38694) is active. See `fdl/README.md` for the exact command. No prior unlock is required.

After the patched SPL + patched uboot are installed (via either method), the device permanently reports as unlocked on every boot, and all downstream signature checks are skipped.

On first boot after switching from a locked stock state, Android detects the verified-boot-state change (green -> orange) and wipes userdata. This is standard Android behavior, not specific to these patches.

## Supported SoCs

Verified working on:
- UMS512 / T618 (Anbernic RG Vita)

The DHTB + SIMGHDR format and SPL verify-call pattern is shared across Unisoc T-series SoCs, so the same approach should work on:
- UMS312 / T310
- UMS9230 / T606, T612, T616
- UMS9620 / T820

For other SoCs you may need to adjust the SPL verify-call pattern detection in `tools/patch_spl.py` (it currently matches `bl / cbz w0 / mov w0, #5` which is the standard T618 sequence).

## Recovery if something goes wrong

If a patched SPL somehow fails to boot:

1. Power off the device completely
2. Hold volume down + connect USB to enter download mode
3. Use `spd_dump` with the CVE-2022-38694 exploit to flash the stock SPL back:
```bash
spd_dump --wait 300 exec_addr 0x3ee8 \
  fdl fdl1-dl.bin 0x5500 \
  fdl fdl2-dl.bin 0x9efffe00 \
  exec w splloader stock_spl.img w splloader_bak stock_spl.img poweroff
```

**Important:** Always keep a stock SPL backup. `scripts/backup.sh` creates one automatically.

## Credits

- NCC Group for the original CVE-2022-38694 BootROM vulnerability research: https://research.nccgroup.com/2022/09/02/theres-another-hole-in-your-soc-unisoc-rom-vulnerabilities/
- TomKing062 for the Unisoc unlock tool: https://github.com/TomKing062/CVE-2022-38694_unlock_bootloader

## License

MIT - see LICENSE file.

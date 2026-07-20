# UnisocBypass

Tools and analysis for bypassing Unisoc firmware signature verification to
unlock and modify the boot chain. The full SPL + uboot flow is developed and
verified on the Unisoc UMS512 (T618, Anbernic RG Vita); a signature-preserving
uboot path is also verified on the fused UMS9620 (T820), where the SPL cannot be
modified (see [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md)).

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
      -> when unlocked, boot/vendor_boot mismatches are tolerated, but AVB
         still runs and generates the dm-verity cmdline; dtbo goes through a
         TrustOS SMC that hard-fails on mismatch and must be correctly signed
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

# 5. (optional) If you modify an AVB-verified partition such as dtbo, re-sign it
#    so the bootloader accepts it (dtbo hard-fails on mismatch even when unlocked):
# python3 tools/avb_resign_partition.py --image dtbo.img --vbmeta vbmeta.img --keys-dir keys
#    then flash dtbo.img. See docs/AVB_RESIGN.md.
```

## Repo layout

- `tools/` - Python tools for parsing, patching, and re-hashing DHTB images
- `scripts/` - Bash scripts for flashing and full workflow automation
- `docs/` - Detailed analysis documentation
- `examples/` - Stock and modified images for reference
- `analysis/` - SPL disassembly + BootROM reverse-engineering notes
- `fdl/` - Unsigned FDL files for flashing on locked devices via `spd_dump`
- `oc/` - separate CPU/GPU overclock research, see [`oc/README.md`](oc/README.md)

## Documentation index

- [docs/WORKFLOW.md](docs/WORKFLOW.md) - step-by-step usage
- [docs/ANALYSIS.md](docs/ANALYSIS.md) - SPL RSA verify reverse-engineering
- [docs/CHAIN_OF_TRUST.md](docs/CHAIN_OF_TRUST.md) - boot-chain signing model
- [docs/DHTB_FORMAT.md](docs/DHTB_FORMAT.md) - DHTB header layout
- [docs/SIMGHDR_FORMAT.md](docs/SIMGHDR_FORMAT.md) - SIMGHDR signature block layout
- [docs/UBOOT_UNLOCK.md](docs/UBOOT_UNLOCK.md) - uboot permanent-unlock patch
- [docs/AVB_RESIGN.md](docs/AVB_RESIGN.md) - re-sign a modified dtbo/boot/vendor_boot so the bootloader accepts it
- [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md) - port to UMS9620/T820: silent unlocked boot via a signature-preserving uboot patch (the SPL cannot be modified on a fused T820)

CPU/GPU overclock and undervolt research is parked in [`oc/`](oc/) - kept
separate because it is not part of the firmware-signing-bypass story and
the practical performance gain turned out to be small.

## Tools

| Tool | Purpose |
|------|---------|
| `tools/dhtb_parse.py` | Parse and display DHTB header + SIMGHDR fields from any signed Unisoc image |
| `tools/patch_spl.py` | Patch SPL: NOP all 4 RSA verify call sites and update DHTB/SIMGHDR hashes (UMS512/T618) |
| `tools/patch_spl_ums9620.py` | Patch UMS9620/T820 SPL: neuter the verify dispatcher (0x045b4) and rehash. Reference / un-fused devices only; a fused T820 rejects a modified SPL (see [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md)) |
| `tools/magic_pack_ums9620.py` | Signature-preserving runtime patcher for UMS9620/T820 uboot (magic64 method): keep the signed payload, append shellcode + patch table (see [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md)) |
| `tools/patch_uboot_unlock_ums9620.py` | Patch UMS9620/T820 uboot for silent unlocked boot (force unlock + strip warning/timeout/SKIP VERIFY), delivered signature-preserving via magic64 |
| `tools/rehash.py` | Recompute DHTB SHA256 + SIMGHDR data hash for any modified image |
| `tools/verify_image.py` | Check that a DHTB image has a valid hash (integrity test) |
| `tools/modify_uboot.py` | Replace strings in uboot and re-hash in one step |
| `tools/patch_uboot_unlock.py` | Patch uboot to permanently report unlocked, disable AVB, strip SKIP VERIFY text + delay |
| `tools/avb_resign_partition.py` | Re-sign a modified chain partition (dtbo/boot/vendor_boot) against the stock vbmeta, auto-selecting the correct key (see [docs/AVB_RESIGN.md](docs/AVB_RESIGN.md)) |
| `tools/avb_disable_verity.py` | Rebuild vbmeta with dm-verity disabled (re-signed + SPRD wrapper regenerated) so modified system/vendor/product boot (see [docs/AVB_RESIGN.md](docs/AVB_RESIGN.md)) |
| `tools/avbtool` | Vendored AOSP avbtool 1.3.0 (runs unsandboxed via system python3) |

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

Use `spd_dump` with the included FDL files in `fdl/`. See `fdl/README.md` for the exact command. No prior unlock is required.

After the patched SPL + patched uboot are installed (via either method), the device permanently reports as unlocked on every boot, and all downstream signature checks are skipped.

On first boot after switching from a locked stock state, Android detects the verified-boot-state change (green -> orange) and wipes userdata. This is standard Android behavior, not specific to these patches.

## Supported SoCs

Verified working on:
- UMS512 / T618 (Anbernic RG Vita) - full SPL + uboot patch flow
- UMS9620 / T820 - silent unlocked boot via a signature-preserving uboot patch
  (see below and [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md))

The DHTB + SIMGHDR format and SPL verify-call pattern is shared across Unisoc T-series SoCs, so the SPL-patch approach should also carry over to:
- UMS312 / T310
- UMS9230 / T606, T612, T616

For other SoCs you may need to adjust the SPL verify-call pattern detection in `tools/patch_spl.py` (it currently matches `bl / cbz w0 / mov w0, #5` which is the standard T618 sequence).

### UMS9620 / T820: the SPL route does not apply

A fused (production) T820 cryptographically verifies the SPL, so the T618
"patch SPL + rehash" trick is rejected and the device drops back to download
mode. The working path there keeps the stock SPL and delivers the uboot patches
with a signature-preserving method (`magic64`), which leaves the signed payload
byte-for-byte intact and applies the edits at runtime. On an already-unlocked
device this removes the unlock warning text, the boot timeout, and the SKIP
VERIFY message in one step:

```bash
# produce a silent unlocked-boot uboot (magic64-packaged, no re-signing needed)
python3 tools/patch_uboot_unlock_ums9620.py stock_uboot.img unlocked_uboot.img
# then flash unlocked_uboot.img to the uboot partition
```

See [docs/UMS9620_PORT.md](docs/UMS9620_PORT.md) for the pinned offsets, the
`magic64` layout, and why re-signing is neither possible nor needed.

## Recovery if something goes wrong

If a patched SPL somehow fails to boot:

1. Power off the device completely
2. Hold volume down + connect USB to enter download mode
3. Use `spd_dump` to flash the stock SPL back:
```bash
spd_dump --wait 300 exec_addr 0x3ee8 \
  fdl fdl1-dl.bin 0x5500 \
  fdl fdl2-dl.bin 0x9efffe00 \
  exec w splloader stock_spl.img w splloader_bak stock_spl.img poweroff
```

**Important:** Always keep a stock SPL backup. `scripts/backup.sh` creates one automatically.

## License

MIT - see LICENSE file.

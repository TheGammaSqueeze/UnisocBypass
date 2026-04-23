# Unsigned FDL files for locked-device flashing

These two files allow flashing any partition on a **locked** Unisoc UMS512 device via SPD tools (`spd_dump`, SPD Factory, Research Download, UpgradeDownload) without going through BootROM signature verification.

- `fdl1-dl.bin` - unsigned FDL1 (USB download-mode stage 1)
- `fdl2-dl.bin` - unsigned FDL2 (download protocol handler that writes to eMMC)

Both are exactly as distributed in the CVE-2022-38694 unlock toolkit by TomKing062. Full credit to the original research by NCC Group and the tooling work by TomKing062.

## Why they matter for this repo

**You do NOT need an unlocked bootloader to install the patched SPL + uboot from this repo.** The patched images can be flashed onto a fresh, stock, locked device using these FDL files:

```bash
# Enter USB download mode: power off, hold volume down, connect USB
spd_dump --wait 300 exec_addr 0x3ee8 \
    fdl fdl1-dl.bin 0x5500 \
    fdl fdl2-dl.bin 0x9efffe00 \
    exec \
    w splloader ../examples/spl_patched.img \
    w splloader_bak ../examples/spl_patched.img \
    w uboot ../examples/uboot_unlocked.img \
    poweroff
```

The exploit chain:

1. `exec_addr 0x3ee8` triggers the CVE-2022-38694 BootROM stack overflow via USB download mode.
2. BootROM verification is bypassed for this session only.
3. `fdl1-dl.bin` is loaded to SRAM at `0x5500` and executed.
4. `fdl2-dl.bin` is loaded to DRAM at `0x9efffe00`.
5. The `w <partition> <file>` commands then write directly to eMMC with no signature check.
6. On next cold boot, BootROM loads our patched SPL from `splloader`, verifies only the DHTB hash (which is valid because `tools/rehash.py` updates it), and runs it.
7. Our patched SPL skips all downstream RSA checks, so the modified uboot boots normally.
8. Our modified uboot forces `flash.locked=0`, `verifiedbootstate=orange`, and skips AVB - even though the original device was locked.

On first Android boot, the verified-boot-state change from `green` -> `orange` triggers Android's standard data-wipe flow, so make sure the device is in a state where that's acceptable (factory-fresh or a unit you're OK with resetting).

## Compatibility

These FDL files target UMS512 (T618). They will not work on other Unisoc SoCs. For other chips, see the SoC-specific FDLs in the `soc/` directory of https://github.com/TomKing062/CVE-2022-38694_unlock_bootloader.

## Source and license

Files are copied verbatim from https://github.com/TomKing062/CVE-2022-38694_unlock_bootloader. Use subject to the terms of that upstream project. Not original work of this repository.

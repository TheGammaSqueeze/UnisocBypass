#!/usr/bin/env bash
# Flash a modified uboot image to both uboot_a and uboot_b slots.
#
# Usage:
#   ./scripts/flash_uboot.sh <modified_uboot.img>
#
# Prerequisite: the device must already have a patched SPL (from flash_spl.sh).
# The SPL checks every uboot image with RSA before jumping to it, so an un-
# patched SPL will refuse a modified uboot and hang.

set -euo pipefail

IMG="${1:-}"
if [[ -z "$IMG" || ! -f "$IMG" ]]; then
    echo "Usage: $0 <modified_uboot.img>" >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 "$SCRIPT_DIR/../tools/verify_image.py" "$IMG"; then
    echo "Error: image failed verification; refusing to flash" >&2
    exit 1
fi

if ! adb get-state >/dev/null 2>&1; then
    echo "Error: no adb device connected" >&2
    exit 1
fi

echo "Pushing $IMG to device..."
adb push "$IMG" /data/local/tmp/uboot_mod.img

echo "Flashing to uboot_a (mmcblk0p8)..."
adb shell 'dd if=/data/local/tmp/uboot_mod.img of=/dev/block/mmcblk0p8 bs=4096 && sync'

echo "Flashing to uboot_b (mmcblk0p9)..."
adb shell 'dd if=/data/local/tmp/uboot_mod.img of=/dev/block/mmcblk0p9 bs=4096 && sync'

echo
echo "Done. Reboot the device with: adb reboot"

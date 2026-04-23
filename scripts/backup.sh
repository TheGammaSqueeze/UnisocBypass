#!/usr/bin/env bash
# Back up SPL and uboot from an attached Unisoc device.
#
# Usage:
#   ./scripts/backup.sh <output_dir>
#
# Creates (inside output_dir):
#   mmcblk0boot0.bin   - Active SPL
#   mmcblk0boot1.bin   - Backup SPL
#   uboot_a.bin        - uboot slot A
#   uboot_b.bin        - uboot slot B
#
# Requires adb with root access on the device.

set -euo pipefail

OUT="${1:-backups}"
mkdir -p "$OUT"

echo "Checking adb connection..."
if ! adb get-state >/dev/null 2>&1; then
    echo "Error: no adb device connected" >&2
    exit 1
fi

echo "Backing up SPL (mmcblk0boot0, mmcblk0boot1)..."
adb pull /dev/block/mmcblk0boot0 "$OUT/mmcblk0boot0.bin"
adb pull /dev/block/mmcblk0boot1 "$OUT/mmcblk0boot1.bin"

echo "Backing up uboot (uboot_a = mmcblk0p8, uboot_b = mmcblk0p9)..."
adb pull /dev/block/mmcblk0p8 "$OUT/uboot_a.bin"
adb pull /dev/block/mmcblk0p9 "$OUT/uboot_b.bin"

echo
echo "Backup complete. Files in $OUT:"
ls -lh "$OUT"

#!/usr/bin/env bash
# Restore stock SPL from backup.
#
# Usage:
#   ./scripts/unpatch.sh <backup_dir>
#
# This flashes mmcblk0boot0.bin and mmcblk0boot1.bin from the backup directory
# (as produced by backup.sh) back to their respective partitions.

set -euo pipefail

BACKUP="${1:-backups}"
if [[ ! -f "$BACKUP/mmcblk0boot0.bin" || ! -f "$BACKUP/mmcblk0boot1.bin" ]]; then
    echo "Error: backup files not found in $BACKUP" >&2
    echo "Expected: mmcblk0boot0.bin, mmcblk0boot1.bin" >&2
    exit 1
fi

if ! adb get-state >/dev/null 2>&1; then
    echo "Error: no adb device connected" >&2
    exit 1
fi

echo "Restoring stock SPL..."
adb push "$BACKUP/mmcblk0boot0.bin" /data/local/tmp/spl_stock0.bin
adb push "$BACKUP/mmcblk0boot1.bin" /data/local/tmp/spl_stock1.bin

adb shell 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
adb shell 'echo 0 > /sys/block/mmcblk0boot1/force_ro'

adb shell 'dd if=/data/local/tmp/spl_stock0.bin of=/dev/block/mmcblk0boot0 bs=4096 && sync'
adb shell 'dd if=/data/local/tmp/spl_stock1.bin of=/dev/block/mmcblk0boot1 bs=4096 && sync'

# Also restore uboot slots if backups present
for slot in a b; do
    SRC="$BACKUP/uboot_${slot}.bin"
    case "$slot" in
        a) PART=/dev/block/mmcblk0p8 ;;
        b) PART=/dev/block/mmcblk0p9 ;;
    esac
    if [[ -f "$SRC" ]]; then
        echo "Restoring uboot_$slot..."
        adb push "$SRC" "/data/local/tmp/uboot_${slot}_stock.bin"
        adb shell "dd if=/data/local/tmp/uboot_${slot}_stock.bin of=$PART bs=4096 && sync"
    fi
done

echo
echo "Stock firmware restored. Reboot with: adb reboot"

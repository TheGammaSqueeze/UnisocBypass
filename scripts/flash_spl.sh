#!/usr/bin/env bash
# Flash a patched SPL to both eMMC boot partitions.
#
# Usage:
#   ./scripts/flash_spl.sh <patched_spl.img>
#
# This writes the SPL to mmcblk0boot0 AND mmcblk0boot1 so both primary and
# backup copies are consistent. The partitions have write protection enabled
# by default; this script disables it via force_ro.
#
# Safety:
#   - Always run `./scripts/backup.sh` first so you have a recovery image
#   - The patched SPL MUST have a valid DHTB hash (use tools/rehash.py if unsure)

set -euo pipefail

IMG="${1:-}"
if [[ -z "$IMG" || ! -f "$IMG" ]]; then
    echo "Usage: $0 <patched_spl.img>" >&2
    exit 2
fi

# Verify the image has valid DHTB hash before flashing
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! python3 "$SCRIPT_DIR/../tools/verify_image.py" "$IMG"; then
    echo "Error: image failed verification; refusing to flash" >&2
    echo "Run tools/rehash.py on it first to fix the DHTB hash." >&2
    exit 1
fi

if ! adb get-state >/dev/null 2>&1; then
    echo "Error: no adb device connected" >&2
    exit 1
fi

echo "Pushing $IMG to device..."
adb push "$IMG" /data/local/tmp/spl_patched.img

echo "Disabling write-protect on boot0 and boot1..."
adb shell 'echo 0 > /sys/block/mmcblk0boot0/force_ro'
adb shell 'echo 0 > /sys/block/mmcblk0boot1/force_ro'

echo "Flashing to mmcblk0boot0 (primary SPL)..."
adb shell 'dd if=/data/local/tmp/spl_patched.img of=/dev/block/mmcblk0boot0 bs=4096 && sync'

echo "Flashing to mmcblk0boot1 (backup SPL)..."
adb shell 'dd if=/data/local/tmp/spl_patched.img of=/dev/block/mmcblk0boot1 bs=4096 && sync'

echo
echo "Verifying flashed SPL hash on device..."
DEV_HASH=$(adb shell 'dd if=/dev/block/mmcblk0boot0 bs=1 skip=8 count=32 2>/dev/null' | xxd -p | tr -d '\n')
FILE_HASH=$(python3 -c "import sys; sys.stdout.write(open('$IMG','rb').read()[8:0x28].hex())")

if [[ "$DEV_HASH" == "$FILE_HASH" ]]; then
    echo "Flash verified. Hash: $FILE_HASH"
    echo
    echo "Done. Reboot the device with: adb reboot"
else
    echo "WARNING: on-device hash does not match file hash!"
    echo "  device: $DEV_HASH"
    echo "  file:   $FILE_HASH"
    exit 1
fi

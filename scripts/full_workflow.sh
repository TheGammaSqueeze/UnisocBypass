#!/usr/bin/env bash
# End-to-end workflow: backup, patch SPL, flash SPL, reboot.
#
# Usage:
#   ./scripts/full_workflow.sh
#
# After this runs, the device will have a patched SPL that skips RSA verify
# on uboot/sml/trustos. You can then modify those images freely with just a
# DHTB hash update (tools/rehash.py) - no RSA re-signing needed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK="$REPO/work"
BACKUP="$WORK/backups"

mkdir -p "$WORK"

if ! adb get-state >/dev/null 2>&1; then
    echo "Error: no adb device connected" >&2
    exit 1
fi

echo "=== Step 1/4: back up device ==="
"$SCRIPT_DIR/backup.sh" "$BACKUP"
echo

echo "=== Step 2/4: patch SPL ==="
python3 "$REPO/tools/patch_spl.py" "$BACKUP/mmcblk0boot0.bin" "$WORK/spl_patched.img"
echo

echo "=== Step 3/4: flash patched SPL ==="
"$SCRIPT_DIR/flash_spl.sh" "$WORK/spl_patched.img"
echo

echo "=== Step 4/4: reboot ==="
echo "Rebooting device to apply patched SPL..."
adb reboot

echo "Waiting for device to come back..."
until adb shell getprop sys.boot_completed 2>/dev/null | grep -q 1; do
    sleep 3
done

echo
echo "Device is up with patched SPL."
echo "Artifacts in $WORK:"
ls -lh "$WORK"
echo
echo "You can now modify sml, trustos, or uboot images; run tools/rehash.py,"
echo "then flash them without RSA re-signing."

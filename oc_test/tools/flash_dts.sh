#!/usr/bin/env bash
# Compile a DTS, wrap in multi-DTB, pack via android_boot_image_editor, flash both vendor_boot slots.
# Usage: ./tools/flash_dts.sh <modified.dts> <experiment_dir>
set -euo pipefail

DTS="${1:?usage: $0 <modified.dts> <experiment_dir>}"
EXP_DIR="${2:?}"
EDITOR=/work/vita/android_boot_image_editor
WORK=/tmp/oc_flash

mkdir -p "$WORK"
echo "==> compile DTS -> DTB"
dtc -q -I dts -O dtb -o "$WORK/modified.dtb" "$DTS"

echo "==> wrap into multi-DTB format"
python3 -c "
import struct
inner = open('$WORK/modified.dtb','rb').read()
hdr = struct.pack('>IIIIIIII', 0xd7b7ab1e, 64+len(inner), 32, 32, 1, 32, 4096, 1)
entry = struct.pack('>IIIIIIII', len(inner), 64, 0, 0, 0, 0, 0, 0)
open('$WORK/modified_multidtb.bin','wb').write(hdr + entry + inner)
"
cp "$WORK/modified_multidtb.bin" "$EDITOR/build/unzip_boot/dtb"

echo "==> pack via android_boot_image_editor"
(cd "$EDITOR" && ./gradlew -q pack)

SIGNED="$EDITOR/vendor_boot.img.signed"
SHA=$(sha256sum "$SIGNED" | awk '{print $1}')
echo "vendor_boot.img.signed sha256: $SHA"
echo "$SHA  vendor_boot.img.signed" > "$EXP_DIR/vendor_boot.img.signed.sha256"

echo "==> flash to both slots"
adb push "$SIGNED" /data/local/tmp/vb_mod.img
adb shell "su -c 'dd if=/data/local/tmp/vb_mod.img of=/dev/block/mmcblk0p47 bs=4096 && dd if=/data/local/tmp/vb_mod.img of=/dev/block/mmcblk0p48 bs=4096 && sync'"
echo "==> reboot and wait"
adb reboot
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 5; done
echo "BOOT_OK"

#!/usr/bin/env bash
# Full iteration: flash an experiment's DTB, run 3 bench modes, pull data.
# Args:
#   $1 experiment directory (must contain modified.dts)
# Produces subdirectories cpu/, gpu/, both/ with raw/ data.
set -euo pipefail
EXP="${1:?usage: $0 <experiment_dir>}"
EDITOR=/work/vita/android_boot_image_editor
WORK=/tmp/oc_flash
mkdir -p "$WORK"

echo "=== flash $EXP ==="
dtc -q -I dts -O dtb -o "$WORK/modified.dtb" "$EXP/modified.dts"
python3 -c "
import struct
inner = open('$WORK/modified.dtb','rb').read()
hdr = struct.pack('>IIIIIIII', 0xd7b7ab1e, 64+len(inner), 32, 32, 1, 32, 4096, 1)
entry = struct.pack('>IIIIIIII', len(inner), 64, 0, 0, 0, 0, 0, 0)
open('$EDITOR/build/unzip_boot/dtb','wb').write(hdr + entry + inner)
"
(cd "$EDITOR" && ./gradlew -q pack)
SIGNED="$EDITOR/vendor_boot.img.signed"
sha256sum "$SIGNED" | awk '{print $1}' > "$EXP/vendor_boot.img.signed.sha256.tmp"
mv "$EXP/vendor_boot.img.signed.sha256.tmp" "$EXP/vendor_boot.img.signed.sha256"

adb push "$SIGNED" /data/local/tmp/vb_mod.img >/dev/null
adb shell "su -c 'dd if=/data/local/tmp/vb_mod.img of=/dev/block/mmcblk0p47 bs=4096 2>/dev/null && dd if=/data/local/tmp/vb_mod.img of=/dev/block/mmcblk0p48 bs=4096 2>/dev/null && sync'"
adb reboot
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 5; done
echo "boot OK"

for MODE in cpu gpu both; do
    echo "=== mode=$MODE ==="
    adb shell "rm -rf /data/local/tmp/oc_test && mkdir -p /data/local/tmp/oc_test" >/dev/null
    adb shell "su -c '/data/local/tmp/bench_test.sh $MODE 180 /data/local/tmp/oc_test > /data/local/tmp/oc_test/run.log 2>&1 &'" >/dev/null
    # Wait for the run file to APPEAR (stress started) before watching for it to disappear
    for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
        if adb shell "ls /data/local/tmp/oc_test/run" 2>/dev/null | grep -q run; then
            break
        fi
        sleep 10
    done
    # Now wait for it to disappear (stress finished)
    while adb shell "ls /data/local/tmp/oc_test/run" 2>/dev/null | grep -q run; do sleep 15; done
    sleep 3
    sudo rm -rf "$EXP/$MODE"
    adb pull /data/local/tmp/oc_test "$EXP/$MODE" >/dev/null
    sudo chown -R gamma:gamma "$EXP/$MODE"
    LINES=$(wc -l < "$EXP/$MODE/telemetry.csv")
    echo "  collected $LINES telemetry lines in $MODE"
done

echo "=== all modes done for $EXP ==="

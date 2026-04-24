#!/system/bin/sh
# GPU-only torture: no CPU stress, just the GLES stresser, lock CPUs to min freq
# to minimize CPU-side heat, let GPU dominate thermal picture.
set -e
DURATION="${1:-180}"
LOG_DIR="${2:-/data/local/tmp/oc_test}"
GPU_BIN=/data/local/tmp/gpu_stress

mkdir -p "$LOG_DIR"
TELEM="$LOG_DIR/telemetry.csv"
EVENTS="$LOG_DIR/events.log"
GPU_LOG="$LOG_DIR/gpu_stress.log"

echo "==> GPU-only test: dur=${DURATION}s" > "$EVENTS"

# Lock CPUs to minimum to reduce CPU heat contribution
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 614400  > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
echo 614400  > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
echo 1228800 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
echo 1228800 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq

# GPU at max
echo performance > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/governor
echo 850000000 > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/min_freq
echo 850000000 > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/max_freq

TZONE_PATHS=""
TZONE_NAMES=""
for tz in /sys/class/thermal/thermal_zone*; do
    if [ -r "$tz/temp" ] && [ -n "$(cat $tz/temp 2>/dev/null)" ]; then
        TZONE_PATHS="$TZONE_PATHS $tz"
        TZONE_NAMES="$TZONE_NAMES $(basename $tz)_$(cat $tz/type)"
    fi
done
HDR="time_s,cpu0_mhz,cpu6_mhz,gpu_mhz"
for n in $TZONE_NAMES; do HDR="$HDR,$n"; done
echo "$HDR" > "$TELEM"

touch "$LOG_DIR/run"
"$GPU_BIN" 1280 720 > "$GPU_LOG" 2>&1 &
GPU_PID=$!
echo "gpu_pid=$GPU_PID" >> "$EVENTS"

START=$(date +%s)
NOW=$START
while [ $NOW -lt $((START + DURATION)) ]; do
    CPU0=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || echo 0)
    CPU6=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq 2>/dev/null || echo 0)
    GPU=$(cat /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/cur_freq 2>/dev/null || echo 0)
    ROW="$((NOW - START)),$((CPU0/1000)),$((CPU6/1000)),$((GPU/1000000))"
    for tz in $TZONE_PATHS; do
        T=$(cat $tz/temp 2>/dev/null || echo 0)
        ROW="$ROW,$T"
    done
    echo "$ROW" >> "$TELEM"
    sleep 1
    NOW=$(date +%s)
done

rm -f "$LOG_DIR/run"
kill $GPU_PID 2>/dev/null || true
echo done

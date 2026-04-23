#!/system/bin/sh
# Run a max-OPP torture test for DURATION seconds while logging thermals,
# frequencies and per-core CPU iteration counts.
#
# Arguments:
#   $1 = DURATION (seconds, default 180)
#   $2 = LOG_DIR  (where CSVs land, default /data/local/tmp/oc_test)
#
# Expects /data/local/tmp/gpu_stress (NDK binary) to be present.

set -e

DURATION="${1:-180}"
LOG_DIR="${2:-/data/local/tmp/oc_test}"
GPU_BIN=/data/local/tmp/gpu_stress

mkdir -p "$LOG_DIR"
TELEM="$LOG_DIR/telemetry.csv"
EVENTS="$LOG_DIR/events.log"
CPU_COUNTS="$LOG_DIR/cpu_counts.txt"
GPU_LOG="$LOG_DIR/gpu_stress.log"

echo "==> torture test: duration ${DURATION}s, logs in $LOG_DIR"
echo "ts_ms duration=${DURATION}" > "$EVENTS"

# --- Step 1: lock max clocks ---
echo "==> applying setclock_max.sh semantics"
# GPU: 850 MHz, performance governor
echo performance > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/governor
echo 850000000 > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/min_freq
echo 850000000 > /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/max_freq

# CPU LITTLE cluster (policy0): 2002 MHz userspace
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed 2>/dev/null || true
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_fix_freq 2>/dev/null || true

# CPU BIG cluster (policy6): 2002 MHz userspace
echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed 2>/dev/null || true
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_fix_freq 2>/dev/null || true

# DDR / scene-frequency: 1866 MHz
echo userspace > /sys/class/devfreq/scene-frequency/governor
echo 1866 > /sys/class/devfreq/scene-frequency/userspace/set_freq

sleep 1
echo "==> pre-test state"
echo "cpu0_freq=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq)" | tee -a "$EVENTS"
echo "cpu6_freq=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq)" | tee -a "$EVENTS"
echo "gpu_freq=$(cat /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/cur_freq)" | tee -a "$EVENTS"

# --- Step 2: enumerate thermal zones ---
TZONE_PATHS=""
TZONE_NAMES=""
for tz in /sys/class/thermal/thermal_zone*; do
    if [ -r "$tz/temp" ] && [ -n "$(cat $tz/temp 2>/dev/null)" ]; then
        TZONE_PATHS="$TZONE_PATHS $tz"
        TZONE_NAMES="$TZONE_NAMES $(basename $tz)_$(cat $tz/type)"
    fi
done

# CSV header
HDR="time_s,cpu0_mhz,cpu6_mhz,gpu_mhz"
for n in $TZONE_NAMES; do HDR="$HDR,$n"; done
HDR="$HDR,load1,load5,load15"
echo "$HDR" > "$TELEM"

# --- Step 3: start CPU stress (8 pinned sha256sum loops, one per core) ---
echo "==> starting CPU stress on 8 cores"
> "$CPU_COUNTS"
for cpu in 0 1 2 3 4 5 6 7; do
    (
        taskset $((1 << cpu)) sh -c '
            count=0
            # Kill on parent exit via fd trick
            while [ -e /data/local/tmp/oc_test/run ]; do
                # sha256sum of 64 KiB zeros -> discard
                dd if=/dev/zero bs=64k count=64 2>/dev/null | sha256sum >/dev/null
                count=$((count + 64*64))
            done
            echo "cpu'"$cpu"'_kbytes=$count"
        ' > "$LOG_DIR/cpu${cpu}_count.txt" 2>&1
    ) &
done

# --- Step 4: start GPU stress ---
echo "==> starting GPU stress"
touch "$LOG_DIR/run"
if [ -x "$GPU_BIN" ]; then
    "$GPU_BIN" 1280 720 > "$GPU_LOG" 2>&1 &
    GPU_PID=$!
    echo "gpu_pid=$GPU_PID" >> "$EVENTS"
else
    echo "!! GPU stress binary missing at $GPU_BIN, skipping GPU load"
    GPU_PID=
fi

# --- Step 5: monitor for DURATION seconds ---
echo "==> running for ${DURATION}s ..."
START_TS=$(date +%s)
TARGET_END=$((START_TS + DURATION))
NOW=$START_TS
while [ $NOW -lt $TARGET_END ]; do
    CPU0=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || echo 0)
    CPU6=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq 2>/dev/null || echo 0)
    GPU=$(cat /sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu/cur_freq 2>/dev/null || echo 0)
    CPU0_M=$((CPU0 / 1000))
    CPU6_M=$((CPU6 / 1000))
    GPU_M=$((GPU / 1000000))

    ELAPSED=$((NOW - START_TS))
    ROW="$ELAPSED,$CPU0_M,$CPU6_M,$GPU_M"

    for tz in $TZONE_PATHS; do
        TEMP=$(cat $tz/temp 2>/dev/null)
        [ -z "$TEMP" ] && TEMP=0
        ROW="$ROW,$TEMP"
    done

    LOAD=$(cut -d' ' -f1,2,3 /proc/loadavg | tr ' ' ',')
    ROW="$ROW,$LOAD"
    echo "$ROW" >> "$TELEM"

    sleep 1
    NOW=$(date +%s)
done

# --- Step 6: stop stressors ---
echo "==> stopping stressors"
rm -f "$LOG_DIR/run"
if [ -n "$GPU_PID" ]; then kill $GPU_PID 2>/dev/null || true; fi
# Let the child shells finish writing their counts
sleep 2

# Aggregate CPU counts
cat "$LOG_DIR/cpu"*"_count.txt" > "$CPU_COUNTS"

echo "==> done"
echo "telemetry: $TELEM"
echo "gpu log:   $GPU_LOG"
echo "cpu cnts:  $CPU_COUNTS"

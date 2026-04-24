#!/system/bin/sh
# Run a max-OPP torture test for DURATION seconds while logging thermals,
# frequencies, per-rail voltages and per-core CPU iteration counts.
#
# ALSO runs a pre-test OPP sweep that forces each GPU OPP and each CPU freq
# target in turn, recording the actual regulator voltage for each. This is
# the authoritative evidence of whether DTB voltage changes are being applied
# at runtime (vs what the device tree merely claims).
#
# Args: $1 DURATION (default 180), $2 LOG_DIR (default /data/local/tmp/oc_test)

set -e
DURATION="${1:-180}"
LOG_DIR="${2:-/data/local/tmp/oc_test}"
GPU_BIN=/data/local/tmp/gpu_stress

mkdir -p "$LOG_DIR"
TELEM="$LOG_DIR/telemetry.csv"
EVENTS="$LOG_DIR/events.log"
CPU_COUNTS="$LOG_DIR/cpu_counts.txt"
GPU_LOG="$LOG_DIR/gpu_stress.log"
SWEEP="$LOG_DIR/opp_voltage_sweep.csv"

echo "==> torture test: duration ${DURATION}s"
echo "ts_ms duration=${DURATION}" > "$EVENTS"

GPU_DEV=/sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu
GPU_REG=""
CPU_REG=""
CORE_REG=""
for r in /sys/class/regulator/regulator.*; do
    name=$(cat $r/name 2>/dev/null)
    case "$name" in
        vddcpu)  CPU_REG=$r/microvolts ;;
        vddgpu)  GPU_REG=$r/microvolts ;;
        vddcore) CORE_REG=$r/microvolts ;;
    esac
done
echo "vddcpu=$CPU_REG vddgpu=$GPU_REG vddcore=$CORE_REG" >> "$EVENTS"

# ---- Pre-test OPP sweep: evidence voltage actually tracks OPP ----
echo "==> OPP voltage sweep (pre-test)"
echo "stage,target_mhz,actual_cur_freq_hz,vddcpu_uV,vddgpu_uV,vddcore_uV" > "$SWEEP"

# GPU: sweep each available OPP
GPU_FREQS=$(cat $GPU_DEV/available_frequencies)
echo simple_ondemand > $GPU_DEV/governor 2>/dev/null || true
# First drop min to the lowest so we can range freely without min>max violations
echo 384000000 > $GPU_DEV/min_freq 2>/dev/null || true
for f in $GPU_FREQS; do
    mhz=$((f / 1000000))
    # Always set max first (grows the allowed range), then min
    echo $f > $GPU_DEV/max_freq 2>/dev/null || true
    echo $f > $GPU_DEV/min_freq 2>/dev/null || true
    sleep 1
    cur=$(cat $GPU_DEV/cur_freq)
    vc=$(cat $CPU_REG 2>/dev/null || echo -1)
    vg=$(cat $GPU_REG 2>/dev/null || echo -1)
    vcr=$(cat $CORE_REG 2>/dev/null || echo -1)
    echo "gpu_sweep,$mhz,$cur,$vc,$vg,$vcr" >> "$SWEEP"
done

# CPU LITTLE / BIG sweep
for p in policy0 policy6; do
    FREQS=$(cat /sys/devices/system/cpu/cpufreq/$p/scaling_available_frequencies)
    echo userspace > /sys/devices/system/cpu/cpufreq/$p/scaling_governor 2>/dev/null || true
    # Drop min low first
    MIN_F=$(echo $FREQS | awk '{print $1}')
    echo $MIN_F > /sys/devices/system/cpu/cpufreq/$p/scaling_min_freq 2>/dev/null || true
    for f in $FREQS; do
        mhz=$((f / 1000))
        echo $f > /sys/devices/system/cpu/cpufreq/$p/scaling_max_freq 2>/dev/null || true
        echo $f > /sys/devices/system/cpu/cpufreq/$p/scaling_min_freq 2>/dev/null || true
        echo $f > /sys/devices/system/cpu/cpufreq/$p/scaling_setspeed 2>/dev/null || true
        sleep 1
        cur=$(cat /sys/devices/system/cpu/cpufreq/$p/scaling_cur_freq)
        vc=$(cat $CPU_REG 2>/dev/null || echo -1)
        vg=$(cat $GPU_REG 2>/dev/null || echo -1)
        vcr=$(cat $CORE_REG 2>/dev/null || echo -1)
        echo "cpu_${p}_sweep,$mhz,$cur,$vc,$vg,$vcr" >> "$SWEEP"
    done
done

# ---- Step 1: lock max clocks for the stress phase ----
echo "==> applying setclock_max.sh semantics"
echo performance > $GPU_DEV/governor
echo 850000000 > $GPU_DEV/min_freq
echo 850000000 > $GPU_DEV/max_freq

echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed 2>/dev/null || true
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_fix_freq 2>/dev/null || true

echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed 2>/dev/null || true
echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_fix_freq 2>/dev/null || true

echo userspace > /sys/class/devfreq/scene-frequency/governor
echo 1866 > /sys/class/devfreq/scene-frequency/userspace/set_freq

sleep 1
echo "cpu0_freq=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq)" | tee -a "$EVENTS"
echo "cpu6_freq=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq)" | tee -a "$EVENTS"
echo "gpu_freq=$(cat $GPU_DEV/cur_freq)" | tee -a "$EVENTS"
echo "pre_stress_vddcpu=$(cat $CPU_REG 2>/dev/null)" | tee -a "$EVENTS"
echo "pre_stress_vddgpu=$(cat $GPU_REG 2>/dev/null)" | tee -a "$EVENTS"

# ---- Enumerate thermal zones, write CSV header ----
TZONE_PATHS=""
TZONE_NAMES=""
for tz in /sys/class/thermal/thermal_zone*; do
    if [ -r "$tz/temp" ] && [ -n "$(cat $tz/temp 2>/dev/null)" ]; then
        TZONE_PATHS="$TZONE_PATHS $tz"
        TZONE_NAMES="$TZONE_NAMES $(basename $tz)_$(cat $tz/type)"
    fi
done

HDR="time_s,cpu0_mhz,cpu6_mhz,gpu_mhz,vddcpu_uV,vddgpu_uV,vddcore_uV"
for n in $TZONE_NAMES; do HDR="$HDR,$n"; done
HDR="$HDR,load1,load5,load15"
echo "$HDR" > "$TELEM"

# ---- Start CPU stress ----
echo "==> starting CPU stress on 8 cores"
> "$CPU_COUNTS"
for cpu in 0 1 2 3 4 5 6 7; do
    (
        taskset $((1 << cpu)) sh -c '
            count=0
            while [ -e /data/local/tmp/oc_test/run ]; do
                dd if=/dev/zero bs=64k count=64 2>/dev/null | sha256sum >/dev/null
                count=$((count + 64*64))
            done
            echo "cpu'"$cpu"'_kbytes=$count"
        ' > "$LOG_DIR/cpu${cpu}_count.txt" 2>&1
    ) &
done

# ---- Start GPU stress ----
echo "==> starting GPU stress"
touch "$LOG_DIR/run"
if [ -x "$GPU_BIN" ]; then
    "$GPU_BIN" 1280 720 > "$GPU_LOG" 2>&1 &
    GPU_PID=$!
    echo "gpu_pid=$GPU_PID" >> "$EVENTS"
else
    echo "!! GPU stress binary missing at $GPU_BIN"
    GPU_PID=
fi

# ---- Monitor loop, now including rail voltages ----
echo "==> running for ${DURATION}s"
START_TS=$(date +%s)
TARGET_END=$((START_TS + DURATION))
NOW=$START_TS
while [ $NOW -lt $TARGET_END ]; do
    CPU0=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null || echo 0)
    CPU6=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq 2>/dev/null || echo 0)
    GPU=$(cat $GPU_DEV/cur_freq 2>/dev/null || echo 0)
    VCPU=$(cat $CPU_REG 2>/dev/null || echo -1)
    VGPU=$(cat $GPU_REG 2>/dev/null || echo -1)
    VCORE=$(cat $CORE_REG 2>/dev/null || echo -1)

    ELAPSED=$((NOW - START_TS))
    ROW="$ELAPSED,$((CPU0/1000)),$((CPU6/1000)),$((GPU/1000000)),$VCPU,$VGPU,$VCORE"
    for tz in $TZONE_PATHS; do
        TEMP=$(cat $tz/temp 2>/dev/null || echo 0)
        ROW="$ROW,$TEMP"
    done
    LOAD=$(cut -d' ' -f1,2,3 /proc/loadavg | tr ' ' ',')
    ROW="$ROW,$LOAD"
    echo "$ROW" >> "$TELEM"
    sleep 1
    NOW=$(date +%s)
done

echo "==> stopping stressors"
rm -f "$LOG_DIR/run"
if [ -n "$GPU_PID" ]; then kill $GPU_PID 2>/dev/null || true; fi
sleep 2
cat "$LOG_DIR/cpu"*"_count.txt" > "$CPU_COUNTS"

echo "==> done"
echo "telemetry: $TELEM"
echo "opp sweep: $SWEEP"
echo "gpu log:   $GPU_LOG"
echo "cpu cnts:  $CPU_COUNTS"

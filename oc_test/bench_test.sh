#!/system/bin/sh
# Comprehensive torture + bench test with three modes.
# NOTE: no `set -u` because Android mksh's handling of unset params in
# backgrounded subshells differs from bash and causes silent exits.
# Produces per-run:
#   - opp_voltage_sweep.csv (evidence the DTB voltages are applied per OPP)
#   - telemetry.csv (freq/volt/temp every 1 s)
#   - cpu_counts.txt (sha256 KiB hashed per core, CPU throughput)
#   - gpu_stress.log (fragment-shader FPS per second, GPU throughput)
#
# Usage:
#   bench_test.sh <mode> [duration_s] [log_dir]
# Modes:
#   cpu   - 8 CPU cores at 2002 MHz stress, GPU held at 384 MHz idle
#   gpu   - CPU policies pinned to min, GPU stress at 850 MHz
#   both  - CPU + GPU both maxed (full torture)
#
# All three modes also run the pre-test OPP voltage sweep so changes to the
# DTB voltage fields can be seen at the regulator level.

MODE="${1:?usage: $0 <cpu|gpu|both> [duration_s] [log_dir]}"
DURATION="${2:-180}"
LOG_DIR="${3:-/data/local/tmp/oc_test}"
GPU_BIN=/data/local/tmp/gpu_stress

mkdir -p "$LOG_DIR"
TELEM="$LOG_DIR/telemetry.csv"
EVENTS="$LOG_DIR/events.log"
CPU_COUNTS="$LOG_DIR/cpu_counts.txt"
GPU_LOG="$LOG_DIR/gpu_stress.log"
SWEEP="$LOG_DIR/opp_voltage_sweep.csv"

echo "==> bench mode=$MODE duration=${DURATION}s" | tee "$EVENTS"
GPU_DEV=/sys/devices/platform/soc/soc:mm/60000000.gpu/devfreq/60000000.gpu

GPU_REG=""; CPU_REG=""; CORE_REG=""
for r in /sys/class/regulator/regulator.*; do
    name=$(cat $r/name 2>/dev/null)
    case "$name" in
        vddcpu)  CPU_REG=$r/microvolts ;;
        vddgpu)  GPU_REG=$r/microvolts ;;
        vddcore) CORE_REG=$r/microvolts ;;
    esac
done
echo "vddcpu=$CPU_REG vddgpu=$GPU_REG vddcore=$CORE_REG" >> "$EVENTS"

# ---- Clean any leftover scaling_fix_freq from a previous run ----
echo 0 > /sys/devices/system/cpu/cpufreq/policy0/scaling_fix_freq 2>/dev/null || true
echo 0 > /sys/devices/system/cpu/cpufreq/policy6/scaling_fix_freq 2>/dev/null || true

# ---- Pre-test OPP voltage sweep ----
echo "==> pre-test OPP voltage sweep"
echo "stage,target_mhz,actual_cur_freq_hz,vddcpu_uV,vddgpu_uV,vddcore_uV" > "$SWEEP"

# GPU sweep
GPU_FREQS=$(cat $GPU_DEV/available_frequencies)
echo simple_ondemand > $GPU_DEV/governor 2>/dev/null || true
MIN_GPU=$(echo $GPU_FREQS | awk '{print $1}')
echo $MIN_GPU > $GPU_DEV/min_freq 2>/dev/null || true
for f in $GPU_FREQS; do
    mhz=$((f / 1000000))
    echo $f > $GPU_DEV/max_freq 2>/dev/null || true
    echo $f > $GPU_DEV/min_freq 2>/dev/null || true
    sleep 1
    cur=$(cat $GPU_DEV/cur_freq)
    vc=$(cat $CPU_REG 2>/dev/null || echo -1)
    vg=$(cat $GPU_REG 2>/dev/null || echo -1)
    vcr=$(cat $CORE_REG 2>/dev/null || echo -1)
    echo "gpu_sweep,$mhz,$cur,$vc,$vg,$vcr" >> "$SWEEP"
done

# CPU sweep (both policies). Ensure scaling_fix_freq is OFF so freq can move.
for p in policy0 policy6; do
    FREQS=$(cat /sys/devices/system/cpu/cpufreq/$p/scaling_available_frequencies)
    echo userspace > /sys/devices/system/cpu/cpufreq/$p/scaling_governor 2>/dev/null || true
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

# ---- Configure clocks for the selected mode ----
case "$MODE" in
    cpu)
        # CPUs at max, GPU at min idle
        echo performance > $GPU_DEV/governor 2>/dev/null || true
        echo 384000000 > $GPU_DEV/min_freq
        echo 384000000 > $GPU_DEV/max_freq
        echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed 2>/dev/null || true
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_fix_freq 2>/dev/null || true
        echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed 2>/dev/null || true
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_fix_freq 2>/dev/null || true
        RUN_CPU_STRESS=1; RUN_GPU_STRESS=0
        ;;
    gpu)
        # GPU at max, CPUs at min idle
        echo performance > $GPU_DEV/governor 2>/dev/null || true
        echo 850000000 > $GPU_DEV/min_freq
        echo 850000000 > $GPU_DEV/max_freq
        echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
        echo 614400 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
        echo 614400 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
        echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
        echo 1228800 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq
        echo 1228800 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
        RUN_CPU_STRESS=0; RUN_GPU_STRESS=1
        ;;
    both)
        echo performance > $GPU_DEV/governor 2>/dev/null || true
        echo 850000000 > $GPU_DEV/min_freq
        echo 850000000 > $GPU_DEV/max_freq
        echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_min_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed 2>/dev/null || true
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_fix_freq 2>/dev/null || true
        echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_max_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_min_freq
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed 2>/dev/null || true
        echo 2002000 > /sys/devices/system/cpu/cpufreq/policy6/scaling_fix_freq 2>/dev/null || true
        RUN_CPU_STRESS=1; RUN_GPU_STRESS=1
        ;;
    *)
        echo "unknown mode $MODE" >&2; exit 2
        ;;
esac

echo userspace > /sys/class/devfreq/scene-frequency/governor 2>/dev/null || true
echo 1866 > /sys/class/devfreq/scene-frequency/userspace/set_freq 2>/dev/null || true

sleep 1
echo "mode=$MODE cpu0=$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq) cpu6=$(cat /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq) gpu=$(cat $GPU_DEV/cur_freq)" | tee -a "$EVENTS"

# CSV header
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

# ---- Start stressors ----
touch "$LOG_DIR/run"
if [ "$RUN_CPU_STRESS" = "1" ]; then
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
fi

if [ "$RUN_GPU_STRESS" = "1" ]; then
    echo "==> starting GPU stress"
    if [ -x "$GPU_BIN" ]; then
        "$GPU_BIN" 1280 720 > "$GPU_LOG" 2>&1 &
        GPU_PID=$!
        echo "gpu_pid=$GPU_PID" >> "$EVENTS"
    fi
fi

# ---- Monitor loop ----
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
        T=$(cat $tz/temp 2>/dev/null || echo 0)
        ROW="$ROW,$T"
    done
    LOAD=$(cut -d' ' -f1,2,3 /proc/loadavg | tr ' ' ',')
    ROW="$ROW,$LOAD"
    echo "$ROW" >> "$TELEM"
    sleep 1
    NOW=$(date +%s)
done

echo "==> stopping stressors"
rm -f "$LOG_DIR/run"
[ -n "${GPU_PID:-}" ] && kill $GPU_PID 2>/dev/null || true
sleep 2
[ -f "$LOG_DIR/cpu0_count.txt" ] && cat "$LOG_DIR/cpu"*"_count.txt" > "$CPU_COUNTS"

echo "==> done mode=$MODE"

#!/system/bin/sh
# Long-form torture test: gpu_stress at pinned 900 MHz for 600s
# Captures per-second telemetry into a CSV
set -u
OUT=${1:-/data/local/tmp/torture}
DUR=${2:-600}
mkdir -p "$OUT"

# Setup
mount -t debugfs none /sys/kernel/debug 2>/dev/null

# Cool down
sleep 30

# Pin GPU to 900 MHz performance
echo performance > /sys/class/devfreq/60000000.gpu/governor
echo 850000000  > /sys/class/devfreq/60000000.gpu/max_freq
echo 850000000  > /sys/class/devfreq/60000000.gpu/min_freq

# Pin CPU policies to min so GPU mode is clean
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
echo 614400    > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
echo 1228800   > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed

# Begin telemetry
HDR="time_s,fps_inst,gpu_mhz,vddgpu_uV,thmsoc,thmboard,thmgpu"
echo "$HDR" > "$OUT/telemetry.csv"

# Start gpu_stress in background
/data/local/tmp/gpu_stress 1280 720 > "$OUT/gpu.log" 2>&1 &
GPID=$!
sleep 1

# Telemetry loop
END=$(($(date +%s) + DUR))
while [ "$(date +%s)" -lt "$END" ]; do
    # Pull last fps line (most recent)
    FPS=$(tail -n 1 "$OUT/gpu.log" | awk -F'fps=' '{print $2}' | awk '{print $1}')
    GMHZ=$(awk '{print $1/1000000}' /sys/class/devfreq/60000000.gpu/cur_freq 2>/dev/null)
    VDD=$(cat /sys/class/regulator/regulator.2/microvolts 2>/dev/null)
    SOC=$(cat /sys/class/thermal/thermal_zone1/temp 2>/dev/null)
    BRD=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
    GPU=$(cat /sys/class/thermal/thermal_zone7/temp 2>/dev/null)
    NOW=$(($(date +%s) - END + DUR))
    echo "$NOW,$FPS,$GMHZ,$VDD,$SOC,$BRD,$GPU" >> "$OUT/telemetry.csv"
    sleep 1
done

kill -9 $GPID 2>/dev/null

# Restore
echo simple_ondemand > /sys/class/devfreq/60000000.gpu/governor 2>/dev/null
echo 384000000      > /sys/class/devfreq/60000000.gpu/min_freq 2>/dev/null
echo 850000000      > /sys/class/devfreq/60000000.gpu/max_freq 2>/dev/null
echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>/dev/null
echo schedutil > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor 2>/dev/null

echo "DONE: $(wc -l < "$OUT/telemetry.csv") telemetry lines, $(wc -l < "$OUT/gpu.log") gpu lines"

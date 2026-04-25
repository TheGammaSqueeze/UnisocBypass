#!/system/bin/sh
# CPU torture: 8 parallel sha256sum workers pinned via taskset, GPU at min
# Captures per-second freq + vdd + temps + KiB hashed per core
set -u
OUT=${1:-/data/local/tmp/cpu_torture}
DUR=${2:-600}
LIT_FREQ=${3:-2002000}
BIG_FREQ=${4:-2002000}
mkdir -p "$OUT"

mount -t debugfs none /sys/kernel/debug 2>/dev/null

# Cool down
sleep 30

# Pin GPU to min (idle) so it doesn't share thermal envelope
echo simple_ondemand > /sys/class/devfreq/60000000.gpu/governor 2>/dev/null
echo 384000000 > /sys/class/devfreq/60000000.gpu/min_freq
echo 384000000 > /sys/class/devfreq/60000000.gpu/max_freq

# Pin CPU clusters at requested frequencies via userspace governor
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo userspace > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor
echo $LIT_FREQ > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
echo $BIG_FREQ > /sys/devices/system/cpu/cpufreq/policy6/scaling_setspeed

# Telemetry header
echo "time_s,cpu0_mhz,cpu6_mhz,vddcpu_uV,vddgpu_uV,thmsoc,thmboard,thmcputop,gpu_mhz,kib_total" > "$OUT/telemetry.csv"

# Per-core counter files
for c in 0 1 2 3 4 5 6 7; do : > "$OUT/cpu${c}_count.txt"; done

# Spawn 8 sha256sum workers, one per core
for c in 0 1 2 3 4 5 6 7; do
  ( taskset $((1<<c)) sh -c "
      while :; do
        # Hash 1 MiB of zeros, repeat
        dd if=/dev/zero bs=1048576 count=1 2>/dev/null | sha256sum >/dev/null
        echo 1048576 >> '$OUT/cpu${c}_count.txt'
      done
  " ) &
done
sleep 1

END=$(($(date +%s) + DUR))
START=$(date +%s)
while [ "$(date +%s)" -lt "$END" ]; do
  NOW=$(($(date +%s) - START))
  CPU0=$(awk '{print $1/1000}' /sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq 2>/dev/null)
  CPU6=$(awk '{print $1/1000}' /sys/devices/system/cpu/cpufreq/policy6/scaling_cur_freq 2>/dev/null)
  VDC=$(cat /sys/class/regulator/regulator.1/microvolts 2>/dev/null)
  VDG=$(cat /sys/class/regulator/regulator.2/microvolts 2>/dev/null)
  SOC=$(cat /sys/class/thermal/thermal_zone1/temp 2>/dev/null)
  BRD=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
  CPUT=$(cat /sys/class/thermal/thermal_zone12/temp 2>/dev/null)
  GMHZ=$(awk '{print $1/1000000}' /sys/class/devfreq/60000000.gpu/cur_freq 2>/dev/null)
  KIB=0
  for c in 0 1 2 3 4 5 6 7; do
    n=$(wc -l < "$OUT/cpu${c}_count.txt")
    KIB=$((KIB + n*1024))
  done
  echo "$NOW,$CPU0,$CPU6,$VDC,$VDG,$SOC,$BRD,$CPUT,$GMHZ,$KIB" >> "$OUT/telemetry.csv"
  sleep 1
done

# Stop workers
pkill -f 'taskset' 2>/dev/null
pkill -f 'dd if=/dev/zero' 2>/dev/null
pkill -f 'sha256sum' 2>/dev/null

# Restore
echo schedutil > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>/dev/null
echo schedutil > /sys/devices/system/cpu/cpufreq/policy6/scaling_governor 2>/dev/null
echo simple_ondemand > /sys/class/devfreq/60000000.gpu/governor 2>/dev/null
echo 384000000 > /sys/class/devfreq/60000000.gpu/min_freq 2>/dev/null
echo 850000000 > /sys/class/devfreq/60000000.gpu/max_freq 2>/dev/null

echo "DONE: $(wc -l < "$OUT/telemetry.csv") rows"

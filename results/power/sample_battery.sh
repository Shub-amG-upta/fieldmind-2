#!/bin/zsh
# Board "battery" sampler (SM8750 1d9c8f40, root): laptop unix time, current_now, voltage_now, power_now, charge_counter.
# Purpose: TEST whether these readings track load; not an energy measurement until validated (CLAUDE.md: no invented energy).
OUT=$1; INTERVAL=${2:-1}
while true; do
  v=$(adb -s 1d9c8f40 shell 'su 0 cat /sys/class/power_supply/battery/current_now /sys/class/power_supply/battery/voltage_now /sys/class/power_supply/battery/power_now /sys/class/power_supply/battery/charge_counter' < /dev/null 2>/dev/null | tr '\n' ' ')
  echo "$(date +%s.%N | cut -c1-14) $v" >> $OUT
  sleep $INTERVAL
done

# FieldMind power probe, board side. Written by bench/power_probe.py and pushed as a file.
# Args: OUT_DIR IDLE_S LOAD_S N_LOAD. Clock: /proc/uptime (the board's wall clock is wrong).
# No `kill`: on the board's /system/bin/sh a redirected `( ... ) &` is two nested processes and $! names the outer one,
# so kill missed its target (and on the first SM8650 run took the whole script down). Loops stop on a stop file.
B=${FM_PSY:-/sys/class/power_supply/battery}
STAT=${FM_STAT:-/proc/stat}
UP=${FM_UPTIME:-/proc/uptime}
O=$1; IDLE=$2; LOAD=$3; N=$4
now() { read u _ < "$UP"; echo "$u"; }
mark() { echo "$1,$(now),$(head -n 1 "$STAT")" >> "$O/markers.csv"; }
mkdir -p "$O"; rm -f "$O/stop_log" "$O/stop_load"
: > "$O/samples.csv"; : > "$O/markers.csv"; : > "$O/errors.txt"
( while [ ! -e "$O/stop_log" ]; do
    read i < "$B/current_now"; read v < "$B/voltage_now"
    echo "$(now),$i,$v"
    sleep 0.1
  done ) >> "$O/samples.csv" 2>> "$O/errors.txt" &
mark log_start
sleep "$IDLE"
mark load_start
k=0
while [ "$k" -lt "$N" ]; do
  ( while [ ! -e "$O/stop_load" ]; do :; done ) > /dev/null 2>&1 &
  k=$((k+1))
done
sleep "$LOAD"
mark load_end
: > "$O/stop_load"
sleep "$IDLE"
mark log_end
: > "$O/stop_log"
wait
echo probe-done

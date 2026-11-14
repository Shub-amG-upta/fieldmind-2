# FieldMind power probe, board side. Written by bench/power_probe.py and pushed as a file.
# Args: OUT_DIR IDLE_S LOAD_S N_LOAD. Clock: /proc/uptime (the board's wall clock is wrong).
B=${FM_PSY:-/sys/class/power_supply/battery}
STAT=${FM_STAT:-/proc/stat}
UP=${FM_UPTIME:-/proc/uptime}
O=$1; IDLE=$2; LOAD=$3; N=$4
now() { read u _ < "$UP"; echo "$u"; }
mark() { echo "$1,$(now),$(head -n 1 "$STAT")" >> "$O/markers.csv"; }
mkdir -p "$O"; : > "$O/samples.csv"; : > "$O/markers.csv"; : > "$O/errors.txt"
( while :; do
    read i < "$B/current_now"; read v < "$B/voltage_now"
    echo "$(now),$i,$v"
    sleep 0.1
  done ) >> "$O/samples.csv" 2>> "$O/errors.txt" &
LOGGER=$!
mark log_start
sleep "$IDLE"
mark load_start
PIDS=""
k=0
while [ "$k" -lt "$N" ]; do
  ( while :; do :; done ) > /dev/null 2>&1 &
  PIDS="$PIDS $!"
  k=$((k+1))
done
sleep "$LOAD"
mark load_end
kill $PIDS
sleep "$IDLE"
mark log_end
kill "$LOGGER"
echo probe-done

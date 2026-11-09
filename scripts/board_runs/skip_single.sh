#!/bin/bash
# Human decision: no Cranfield single-agent baseline. Ends the queue in its 5-minute pause after TEP.
L=~/qidk_logs
Q=$L/queue.log
until grep -qE 'tep_v3_board: attempt [0-9]+ ended, exit 0|tep_v3_board: GAVE UP' $Q; do sleep 15; done
pkill -f '^bash /home/harsha/qidk_logs/run_tep2.sh$'
pkill -f '^sleep 300$'
r=$(grep -E 'tep_v3_board: (attempt [0-9]+ ended, exit 0|GAVE UP)' $Q | tail -1 | cut -c25-)
echo ">>> $(date '+%F %T') queue ended by decision: single-agent baseline not run. TEP: $r" | tee -a $Q
echo "tep_done single=skipped_by_decision" > $L/TEP_ALL_DONE

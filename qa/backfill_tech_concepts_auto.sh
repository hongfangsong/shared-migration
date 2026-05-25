#!/bin/bash
# backfill_tech_concepts_auto.sh
# 自动连续执行 backfill_tech_concepts.py 直到完成所有批次

LOG="/tmp/backfill_tech_log.txt"
PROGRESS="/tmp/backfill_tech_progress.json"
BATCH_LOG="/tmp/backfill_tech_batch.log"
START=300
LIMIT=50

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting batch start=$START" >> "$BATCH_LOG"
    
    python3 /mnt/data/sub_agents/shared/qa/backfill_tech_concepts.py --start $START --limit $LIMIT >> "$BATCH_LOG" 2>&1
    
    LAST_STATUS=$(tail -3 "$BATCH_LOG" | grep "Batch done" | tail -1)
    if echo "$LAST_STATUS" | grep -q "0 failed"; then
        TOTAL_OK=$(grep -c "OK:" "$LOG" 2>/dev/null || echo "?")
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Batch $START done (total OK: $TOTAL_OK)" >> "$BATCH_LOG"
    fi
    
    # 检查是否完成（Missing < LIMIT 或无新处理）
    MISSING=$(python3 -c "import json; d=json.load(open('$PROGRESS')); print(d.get('missing', 999999))" 2>/dev/null)
    DONE=$(python3 -c "import json; d=json.load(open('$PROGRESS')); print(d.get('done', 0))" 2>/dev/null)
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Progress: done=$DONE missing=$MISSING" >> "$BATCH_LOG"
    
    if [ "$MISSING" -lt "$LIMIT" ] || [ "$DONE" -ge 3658 ]; then
        TOTAL=$(grep -c "OK:" "$LOG" 2>/dev/null || echo "?")
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALL DONE! Total OK: $TOTAL" >> "$BATCH_LOG"
        break
    fi
    
    START=$((START + LIMIT))
    sleep 2
done

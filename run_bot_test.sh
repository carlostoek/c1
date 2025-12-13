#!/bin/bash
pkill -9 python 2>/dev/null
sleep 1
python main.py > bot_live.log 2>&1 &
BOT_PID=$!
echo "Bot iniciado PID: $BOT_PID"
echo "Esperando 10 segundos..."
sleep 10
echo ""
echo "Log del bot:"
tail -30 bot_live.log
echo ""
echo "Matando bot..."
kill -INT $BOT_PID 2>/dev/null
sleep 2

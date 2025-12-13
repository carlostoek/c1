#!/bin/bash
echo "🧪 Test Final del Bot"
echo "===================="
echo ""

# Limpiar procesos previos
pkill -9 python 2>/dev/null || true
sleep 1

# Iniciar bot
echo "▶️  Iniciando bot..."
python main.py > bot_final.log 2>&1 &
BOT_PID=$!
echo "✅ Bot PID: $BOT_PID"
echo ""

# Esperar que inicie
echo "⏳ Esperando 15 segundos para que el bot inicie..."
sleep 15

# Verificar que está corriendo
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Bot está corriendo"
else
    echo "❌ Bot no está corriendo"
    exit 1
fi
echo ""

# Mostrar log relevante
echo "📋 Log del bot (últimas 20 líneas):"
tail -20 bot_final.log | grep -E "(Registr|handlers|Bot iniciado|polling|TIMEOUT)" || echo "(No hay líneas relevantes)"
echo ""

# Enviar señal de cierre
echo "📨 Enviando SIGINT para cerrar..."
kill -INT $BOT_PID
sleep 3

# Verificar que cerró
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "⚠️  Bot aún corriendo, esperando más..."
    sleep 7
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "❌ Bot no cerró limpiamente"
        kill -9 $BOT_PID
        exit 1
    else
        echo "✅ Bot cerró correctamente"
    fi
else
    echo "✅ Bot cerró correctamente"
fi
echo ""

# Mostrar shutdown
echo "📋 Shutdown log:"
tail -15 bot_final.log | grep -E "(Cerrando|shutdown|Timeout|Background|cerrada)" || echo "(No hay líneas de shutdown)"

echo ""
echo "✅ Test completado exitosamente"

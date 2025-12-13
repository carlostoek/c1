#!/bin/bash
# Script helper para ejecutar tests

set -e

echo "🧪 Ejecutando suite de tests..."
echo ""

# Verificar que pytest esta instalado
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no esta instalado"
    echo "   Instala con: pip install pytest pytest-asyncio --break-system-packages"
    exit 1
fi

# Limpiar base de datos de prueba
echo "🗑️  Limpiando BD de prueba anterior..."
rm -f bot.db bot.db-shm bot.db-wal

# Ejecutar tests
echo "▶️  Ejecutando tests..."
echo ""
pytest tests/ -v --tb=short

# Resultado
echo ""
if [ $? -eq 0 ]; then
    echo "✅✅✅ TODOS LOS TESTS PASARON"
else
    echo "❌ ALGUNOS TESTS FALLARON"
    exit 1
fi

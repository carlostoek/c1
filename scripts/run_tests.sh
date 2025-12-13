#!/bin/bash
# Script helper para ejecutar tests del bot

echo "🧪 Test Suite - Bot Telegram VIP/Free"
echo "======================================"
echo ""

# Verificar que pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest no está instalado"
    echo "   Instala con: pip install pytest pytest-asyncio --break-system-packages"
    exit 1
fi

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Función para limpiar BD
cleanup_db() {
    echo "🗑️  Limpiando BD de prueba anterior..."
    rm -f bot.db bot.db-shm bot.db-wal
}

# Función para ejecutar tests
run_tests() {
    local test_file=$1
    local description=$2

    echo -e "${YELLOW}Ejecutando: ${description}${NC}"
    pytest "$test_file" -v --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${description} - PASÓ${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ ${description} - FALLÓ${NC}"
        echo ""
        return 1
    fi
}

# Verificar argumento
if [ -z "$1" ] || [ "$1" = "all" ]; then
    echo "Ejecutando TODOS los tests..."
    echo ""

    cleanup_db

    # ONDA 1
    run_tests "tests/test_e2e_flows.py" "Tests E2E ONDA 1"
    ONDA1=$?

    # ONDA 2
    run_tests "tests/test_e2e_onda2.py" "Tests E2E ONDA 2"
    ONDA2=$?

    # Resumen
    echo "======================================"
    echo "📊 RESUMEN"
    echo "======================================"

    if [ $ONDA1 -eq 0 ]; then
        echo -e "${GREEN}✅ ONDA 1 E2E - PASÓ${NC}"
    else
        echo -e "${RED}❌ ONDA 1 E2E - FALLÓ${NC}"
    fi

    if [ $ONDA2 -eq 0 ]; then
        echo -e "${GREEN}✅ ONDA 2 E2E - PASÓ${NC}"
    else
        echo -e "${RED}❌ ONDA 2 E2E - FALLÓ${NC}"
    fi

    echo ""

    if [ $ONDA1 -eq 0 ] && [ $ONDA2 -eq 0 ]; then
        echo -e "${GREEN}🎉 TODOS LOS TESTS PASARON${NC}"
        exit 0
    else
        echo -e "${RED}⚠️ Algunos tests fallaron${NC}"
        exit 1
    fi

elif [ "$1" = "onda1" ]; then
    echo "Ejecutando tests de ONDA 1..."
    echo ""
    cleanup_db
    run_tests "tests/test_e2e_flows.py" "Tests E2E ONDA 1"
    exit $?

elif [ "$1" = "onda2" ]; then
    echo "Ejecutando tests de ONDA 2..."
    echo ""
    cleanup_db
    run_tests "tests/test_e2e_onda2.py" "Tests E2E ONDA 2"
    exit $?

else
    echo "❌ Opción inválida: $1"
    echo ""
    echo "Uso: $0 [onda1|onda2|all]"
    echo ""
    echo "Opciones:"
    echo "  onda1  - Ejecutar tests de ONDA 1"
    echo "  onda2  - Ejecutar tests de ONDA 2"
    echo "  all    - Ejecutar todos los tests (default)"
    exit 1
fi

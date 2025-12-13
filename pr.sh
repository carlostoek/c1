#!/bin/bash
# claude-review-pr.sh

PR_NUM=$1

if [ -z "$PR_NUM" ]; then
    echo "Uso: $0 [número-pr]"
    exit 1
fi

echo "🤖 Preparando PR para review de Claude Code..."

# Obtener diff del PR
gh pr diff $PR_NUM > pr_${PR_NUM}_diff.txt

# Obtener archivos cambiados
gh pr view $PR_NUM --json files --jq '.files[].path' > pr_${PR_NUM}_files.txt

# Crear prompt para Claude Code
cat > pr_${PR_NUM}_review_prompt.txt << EOF
Por favor revisa este Pull Request siguiendo estas pautas:

ARCHIVOS MODIFICADOS:
$(cat pr_${PR_NUM}_files.txt)

CAMBIOS COMPLETOS:
$(cat pr_${PR_NUM}_diff.txt)

Analiza y proporciona feedback sobre:
1. 🐛 Bugs potenciales o errores lógicos
2. 🔒 Problemas de seguridad
3. ⚡ Oportunidades de optimización
4. 📚 Mejoras en documentación
5. 🎨 Calidad del código y mejores prácticas
6. 🧪 Casos edge no contemplados
7. ♻️ Código duplicado o refactorización necesaria

Formato tu respuesta con:
- Severidad: CRÍTICO / IMPORTANTE / SUGERENCIA
- Archivo y línea específica
- Descripción del problema
- Sugerencia de corrección
EOF

echo "✅ Archivos generados:"
echo "   - pr_${PR_NUM}_diff.txt (diferencias)"
echo "   - pr_${PR_NUM}_files.txt (archivos)"
echo "   - pr_${PR_NUM}_review_prompt.txt (prompt)"
echo ""
echo "🤖 Ahora ejecuta en Claude Code:"
echo "   cat pr_${PR_NUM}_review_prompt.txt"

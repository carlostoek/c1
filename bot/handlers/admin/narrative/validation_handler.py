"""
Handler de validación de integridad narrativa.

Ejecuta validaciones y muestra reporte de problemas:
- Dead ends: Fragmentos sin decisiones no marcados como ending
- Broken references: Decisiones con target_fragment_key inexistente
- Unreachable: Fragmentos sin camino de acceso
- Missing entry: Capítulos sin entry_point
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.services.container import NarrativeContainer
from bot.narrative.services.validation import ValidationIssueType
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@narrative_admin_router.callback_query(F.data == "narrative:validate")
async def callback_validate_narrative(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Ejecuta validación completa de la narrativa."""
    await callback.answer("🔍 Validando narrativa...")

    narrative = NarrativeContainer(session)
    result = await narrative.validation.validate_all()

    # Formatear reporte
    text = narrative.validation.format_validation_report(result)

    # Botones de acción
    buttons = []

    if result.total_issues > 0:
        # Agregar botones para cada tipo de issue encontrado
        issue_types_found = set(issue.issue_type for issue in result.issues)

        if ValidationIssueType.DEAD_END in issue_types_found:
            count = sum(1 for i in result.issues if i.issue_type == ValidationIssueType.DEAD_END)
            buttons.append([{
                "text": f"🔴 Dead Ends ({count})",
                "callback_data": "narrative:validate:type:dead_end"
            }])

        if ValidationIssueType.BROKEN_REFERENCE in issue_types_found:
            count = sum(1 for i in result.issues if i.issue_type == ValidationIssueType.BROKEN_REFERENCE)
            buttons.append([{
                "text": f"🔴 Referencias Rotas ({count})",
                "callback_data": "narrative:validate:type:broken_ref"
            }])

        if ValidationIssueType.UNREACHABLE in issue_types_found:
            count = sum(1 for i in result.issues if i.issue_type == ValidationIssueType.UNREACHABLE)
            buttons.append([{
                "text": f"🟡 Inalcanzables ({count})",
                "callback_data": "narrative:validate:type:unreachable"
            }])

        if ValidationIssueType.MISSING_ENTRY in issue_types_found:
            count = sum(1 for i in result.issues if i.issue_type == ValidationIssueType.MISSING_ENTRY)
            buttons.append([{
                "text": f"🟡 Sin Entry Point ({count})",
                "callback_data": "narrative:validate:type:missing_entry"
            }])

    buttons.append([{
        "text": "🔄 Volver a Validar",
        "callback_data": "narrative:validate"
    }])
    buttons.append([{
        "text": "🔙 Volver",
        "callback_data": "admin:narrative"
    }])

    keyboard = create_inline_keyboard(buttons)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.startswith("narrative:validate:type:"))
async def callback_validate_by_type(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalles de un tipo de issue."""
    await callback.answer()

    issue_type_str = callback.data.replace("narrative:validate:type:", "")

    type_mapping = {
        "dead_end": ValidationIssueType.DEAD_END,
        "broken_ref": ValidationIssueType.BROKEN_REFERENCE,
        "unreachable": ValidationIssueType.UNREACHABLE,
        "missing_entry": ValidationIssueType.MISSING_ENTRY,
    }

    issue_type = type_mapping.get(issue_type_str)
    if not issue_type:
        await callback.message.edit_text("❌ Tipo de issue no válido.")
        return

    narrative = NarrativeContainer(session)
    result = await narrative.validation.validate_all()

    # Filtrar issues por tipo
    filtered_issues = [i for i in result.issues if i.issue_type == issue_type]

    type_labels = {
        ValidationIssueType.DEAD_END: ("🔴 Dead Ends", "Fragmentos sin decisiones y no marcados como ending"),
        ValidationIssueType.BROKEN_REFERENCE: ("🔴 Referencias Rotas", "Decisiones apuntando a fragmentos inexistentes"),
        ValidationIssueType.UNREACHABLE: ("🟡 Fragmentos Inalcanzables", "Fragmentos sin camino de acceso"),
        ValidationIssueType.MISSING_ENTRY: ("🟡 Sin Entry Point", "Capítulos sin punto de entrada"),
    }

    label, description = type_labels[issue_type]

    text = (
        f"{label}\n"
        f"<i>{description}</i>\n\n"
        f"Total: {len(filtered_issues)}\n\n"
    )

    # Mostrar cada issue con acción
    buttons = []

    for issue in filtered_issues[:10]:  # Máximo 10
        if issue.fragment_key:
            text += f"• <code>{issue.fragment_key}</code>\n"
            text += f"  └ {issue.detail[:60]}...\n" if len(issue.detail) > 60 else f"  └ {issue.detail}\n"

            # Botón para ir al fragmento
            buttons.append([{
                "text": f"📄 {issue.fragment_key[:20]}",
                "callback_data": f"narrative:fragment:view:{issue.fragment_key}"
            }])
        else:
            text += f"• <b>{issue.chapter_name}</b>: {issue.detail}\n"
            # Botón para ir al capítulo
            buttons.append([{
                "text": f"📚 {issue.chapter_name[:20]}",
                "callback_data": f"narrative:chapter:view:{issue.chapter_id}"
            }])

    if len(filtered_issues) > 10:
        text += f"\n<i>... y {len(filtered_issues) - 10} más</i>\n"

    # Acciones de corrección rápida según tipo
    if issue_type == ValidationIssueType.DEAD_END:
        text += "\n<b>Acciones sugeridas:</b>\n"
        text += "• Marcar fragmentos como 🏁 Ending\n"
        text += "• Agregar decisiones a los fragmentos\n"

    elif issue_type == ValidationIssueType.BROKEN_REFERENCE:
        text += "\n<b>Acciones sugeridas:</b>\n"
        text += "• Corregir target_fragment_key en las decisiones\n"
        text += "• Crear los fragmentos faltantes\n"

    elif issue_type == ValidationIssueType.UNREACHABLE:
        text += "\n<b>Acciones sugeridas:</b>\n"
        text += "• Marcar como 🚪 Entry Point si es inicio\n"
        text += "• Agregar decisiones que lleven a estos fragmentos\n"

    elif issue_type == ValidationIssueType.MISSING_ENTRY:
        text += "\n<b>Acciones sugeridas:</b>\n"
        text += "• Marcar un fragmento del capítulo como 🚪 Entry Point\n"

    buttons.append([{
        "text": "🔙 Volver al Reporte",
        "callback_data": "narrative:validate"
    }])

    keyboard = create_inline_keyboard(buttons)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:validate:chapter:\d+"))
async def callback_validate_chapter(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Valida un capítulo específico."""
    await callback.answer("🔍 Validando capítulo...")

    chapter_id = int(callback.data.split(":")[-1])

    narrative = NarrativeContainer(session)
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)

    if not chapter:
        await callback.message.edit_text("❌ Capítulo no encontrado.")
        return

    result = await narrative.validation.validate_chapter(chapter_id)

    if result.total_issues == 0:
        text = (
            f"✅ <b>Capítulo: {chapter.name}</b>\n\n"
            "No se encontraron problemas de validación."
        )
    else:
        status_emoji = "❌" if result.errors > 0 else "⚠️"
        text = (
            f"{status_emoji} <b>Capítulo: {chapter.name}</b>\n\n"
            f"<b>Errores:</b> {result.errors}\n"
            f"<b>Warnings:</b> {result.warnings}\n\n"
        )

        for issue in result.issues[:8]:
            severity = "🔴" if issue.severity.value == "error" else "🟡"
            text += f"{severity} <code>{issue.fragment_key}</code>\n"
            text += f"  └ {issue.detail[:50]}...\n" if len(issue.detail) > 50 else f"  └ {issue.detail}\n"

        if len(result.issues) > 8:
            text += f"\n<i>... y {len(result.issues) - 8} más</i>\n"

    keyboard = create_inline_keyboard([
        [{"text": "📄 Ver Fragmentos", "callback_data": f"narrative:fragments:{chapter_id}"}],
        [{"text": "🔙 Volver al Reporte", "callback_data": "narrative:validate"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

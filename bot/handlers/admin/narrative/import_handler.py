"""
Handlers para wizard de importación JSON de narrativa.

Flujo:
1. Admin accede desde menú -> Importar JSON
2. Admin sube archivo .json
3. Bot valida y muestra resumen
4. Si hay conflictos: flujo de resolución
5. Confirmación final
6. Procesamiento y reporte
"""
import json
import logging
from typing import Dict

from aiogram import F
from aiogram.types import CallbackQuery, Message, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.states.admin import JsonImportStates
from bot.narrative.services.import_service import (
    JsonImportService,
    ConflictResolution,
    ValidationResult,
)
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


# ========================================
# KEYBOARDS
# ========================================

def import_menu_keyboard():
    """Keyboard del menú de importación."""
    return create_inline_keyboard([
        [{"text": "📥 Subir Archivo JSON", "callback_data": "narr_import:start"}],
        [{"text": "🔙 Volver", "callback_data": "admin:narrative"}]
    ])


def waiting_for_file_keyboard():
    """Keyboard mientras espera archivo."""
    return create_inline_keyboard([
        [{"text": "❌ Cancelar", "callback_data": "narr_import:cancel"}]
    ])


def conflict_resolution_keyboard():
    """Keyboard para opciones globales de resolución de conflictos."""
    return create_inline_keyboard([
        [{"text": "✅ Actualizar Todos", "callback_data": "narr_import:conflict:update_all"}],
        [{"text": "⏭️ Omitir Todos", "callback_data": "narr_import:conflict:skip_all"}],
        [{"text": "🔍 Revisar Uno por Uno", "callback_data": "narr_import:conflict:review"}],
        [{"text": "❌ Cancelar Importación", "callback_data": "narr_import:cancel"}]
    ])


def single_conflict_keyboard(fragment_key: str):
    """Keyboard para revisión de conflicto individual."""
    return create_inline_keyboard([
        [
            {"text": "✅ Actualizar", "callback_data": f"narr_import:single:update:{fragment_key}"},
            {"text": "⏭️ Omitir", "callback_data": f"narr_import:single:skip:{fragment_key}"}
        ],
        [{"text": "🔙 Volver a Opciones", "callback_data": "narr_import:conflict:back"}]
    ])


def confirmation_keyboard():
    """Keyboard de confirmación final."""
    return create_inline_keyboard([
        [
            {"text": "✅ Confirmar", "callback_data": "narr_import:confirm"},
            {"text": "❌ Cancelar", "callback_data": "narr_import:cancel"}
        ]
    ])


def result_keyboard():
    """Keyboard después de importación."""
    return create_inline_keyboard([
        [{"text": "📥 Importar Más", "callback_data": "narrative_admin:import"}],
        [{"text": "🔙 Volver", "callback_data": "admin:narrative"}]
    ])


def error_keyboard():
    """Keyboard después de error."""
    return create_inline_keyboard([
        [{"text": "🔄 Intentar de Nuevo", "callback_data": "narrative_admin:import"}],
        [{"text": "🔙 Volver", "callback_data": "admin:narrative"}]
    ])


# ========================================
# INICIO DEL WIZARD
# ========================================

@narrative_admin_router.callback_query(F.data == "narrative_admin:import")
async def callback_import_menu(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Muestra menú de opciones de importación.
    """
    await state.clear()

    text = (
        "📥 <b>Importar Contenido Narrativo</b>\n\n"
        "Puedes importar contenido desde un archivo JSON.\n\n"
        "<b>Formatos soportados:</b>\n"
        "• <b>Capítulo completo:</b> Incluye datos del capítulo + fragmentos\n"
        "• <b>Solo fragmentos:</b> Agrega fragmentos a capítulo existente\n\n"
        "<i>El archivo debe ser un documento .json (no texto pegado).</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=import_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@narrative_admin_router.callback_query(F.data == "narr_import:start")
async def callback_start_import(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Inicia el wizard de importación.
    """
    await state.set_state(JsonImportStates.waiting_for_json_file)

    example_chapter = (
        '{\n'
        '  "type": "chapter",\n'
        '  "chapter": {\n'
        '    "name": "Los Kinkys",\n'
        '    "slug": "los-kinkys",\n'
        '    "chapter_type": "free"\n'
        '  },\n'
        '  "fragments": [...]\n'
        '}'
    )

    example_fragments = (
        '{\n'
        '  "type": "fragments",\n'
        '  "chapter_slug": "los-kinkys",\n'
        '  "fragments": [...]\n'
        '}'
    )

    text = (
        "📄 <b>Importar JSON</b>\n\n"
        "Envía el archivo JSON con el contenido narrativo.\n\n"
        "<b>Estructura para capítulo completo:</b>\n"
        f"<pre>{example_chapter}</pre>\n\n"
        "<b>Estructura para solo fragmentos:</b>\n"
        f"<pre>{example_fragments}</pre>\n\n"
        "<i>Envía el archivo como documento .json</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=waiting_for_file_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# RECEPCIÓN DE ARCHIVO JSON
# ========================================

@narrative_admin_router.message(
    JsonImportStates.waiting_for_json_file,
    F.content_type == ContentType.DOCUMENT
)
async def process_json_file(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Recibe y procesa el archivo JSON.
    """
    document = message.document

    # Validar extensión
    if not document.file_name.lower().endswith(".json"):
        await message.answer(
            "❌ El archivo debe tener extensión .json\n\n"
            "Por favor, envía un archivo JSON válido.",
            reply_markup=waiting_for_file_keyboard()
        )
        return

    # Validar tamaño (max 1MB)
    if document.file_size > 1024 * 1024:
        await message.answer(
            "❌ El archivo es muy grande (máx 1MB)\n\n"
            "Divide el contenido en archivos más pequeños.",
            reply_markup=waiting_for_file_keyboard()
        )
        return

    # Notificar que estamos procesando
    processing_msg = await message.answer("⏳ Procesando archivo JSON...")

    try:
        # Descargar archivo
        file = await message.bot.get_file(document.file_id)
        file_bytes = await message.bot.download_file(file.file_path)

        # Parsear JSON
        json_content = json.loads(file_bytes.read().decode("utf-8"))

        # Detectar si es un array y procesarlo inteligentemente
        if isinstance(json_content, list):
            # Verificar si es un array de capítulos (cada uno con type/chapter/fragments)
            if (json_content and
                isinstance(json_content[0], dict) and
                "type" in json_content[0] and
                json_content[0]["type"] == "chapter"):
                # Es un array de capítulos - procesarlos uno por uno
                await processing_msg.edit_text(
                    f"📚 <b>Detectado Array de Capítulos</b>\n\n"
                    f"Se encontraron <b>{len(json_content)} capítulos</b> para importar.\n\n"
                    f"Procesando cada capítulo...",
                    parse_mode="HTML"
                )

                # Guardar en FSM para procesamiento secuencial
                await state.update_data(
                    import_mode="batch_chapters",
                    chapters_to_import=json_content,
                    current_chapter_idx=0,
                    import_results={
                        "total": len(json_content),
                        "successful": 0,
                        "failed": 0,
                        "details": []
                    },
                    admin_chat_id=message.chat.id
                )

                # Procesar primer capítulo
                await process_next_chapter(processing_msg, state, session)
                return
            else:
                # Array simple sin estructura - error
                await processing_msg.edit_text(
                    "❌ <b>Formato JSON Incorrecto</b>\n\n"
                    "Detectamos un array simple que no sigue el formato de capítulos.\n\n"
                    "<b>El JSON debe tener una de estas estructuras:</b>\n\n"
                    "<b>1. Capítulo completo:</b>\n"
                    "<pre>{\n"
                    '  "type": "chapter",\n'
                    '  "chapter": {...},\n'
                    '  "fragments": [...]\n'
                    "}</pre>\n\n"
                    "<b>2. Solo fragmentos:</b>\n"
                    "<pre>{\n"
                    '  "type": "fragments",\n'
                    '  "chapter_slug": "nombre",\n'
                    '  "fragments": [...]\n'
                    "}</pre>\n\n"
                    "<b>3. Array de capítulos:</b>\n"
                    "<pre>[\n"
                    '  {"type": "chapter", "chapter": {...}, "fragments": [...]},\n'
                    '  {"type": "chapter", "chapter": {...}, "fragments": [...]}\n'
                    "]</pre>",
                    reply_markup=error_keyboard(),
                    parse_mode="HTML"
                )
                await state.clear()
                return

        # Validar contenido
        import_service = JsonImportService(session, message.bot)
        validation = await import_service.validate_json(json_content)

        if not validation.is_valid:
            # Mostrar errores
            await processing_msg.edit_text(
                import_service.format_validation_summary(validation),
                reply_markup=error_keyboard(),
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Guardar en FSM
        await state.update_data(
            json_content=json_content,
            import_type=validation.import_type.value,
            chapter_slug=validation.chapter_slug,
            chapter_data=validation.chapter_data,
            fragments=validation.fragments,
            conflicts=validation.conflicts,
            conflict_resolutions={},
            current_conflict_idx=0,
            admin_chat_id=message.chat.id
        )

        # Si hay conflictos, mostrar opciones de resolución
        if validation.conflicts:
            await state.set_state(JsonImportStates.resolving_conflicts)

            conflicts_text = "\n".join([
                f"• <code>{c['fragment_key']}</code>: "
                f"'{c['existing_title']}' → '{c['new_title']}'"
                for c in validation.conflicts[:5]
            ])

            if len(validation.conflicts) > 5:
                conflicts_text += f"\n... y {len(validation.conflicts) - 5} más"

            await processing_msg.edit_text(
                f"⚠️ <b>Conflictos Detectados</b>\n\n"
                f"Se encontraron <b>{len(validation.conflicts)} fragmentos</b> "
                f"que ya existen:\n\n"
                f"{conflicts_text}\n\n"
                f"<b>¿Cómo deseas resolver los conflictos?</b>",
                reply_markup=conflict_resolution_keyboard(),
                parse_mode="HTML"
            )
        else:
            # Sin conflictos, ir a confirmación
            await state.set_state(JsonImportStates.waiting_for_confirmation)
            await show_confirmation(processing_msg, validation, {})

    except json.JSONDecodeError as e:
        await processing_msg.edit_text(
            f"❌ <b>Error de Formato JSON</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Verifica que el archivo sea un JSON válido.",
            reply_markup=error_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error procesando JSON: {e}", exc_info=True)
        await processing_msg.edit_text(
            f"❌ <b>Error Inesperado</b>\n\n"
            f"<code>{str(e)}</code>",
            reply_markup=error_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()


# ========================================
# PROCESAMIENTO BATCH DE CAPÍTULOS
# ========================================

async def process_next_chapter(
    processing_msg,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el siguiente capítulo en un batch."""
    data = await state.get_data()

    if data.get("import_mode") != "batch_chapters":
        return

    chapters = data.get("chapters_to_import", [])
    current_idx = data.get("current_chapter_idx", 0)
    results = data.get("import_results", {})

    if current_idx >= len(chapters):
        # Todos los capítulos procesados - mostrar resumen
        await show_batch_summary(processing_msg, results)
        await state.clear()
        return

    chapter_data = chapters[current_idx]

    try:
        # Validar este capítulo
        import_service = JsonImportService(session, processing_msg.bot)
        validation = await import_service.validate_json(chapter_data)

        if not validation.is_valid:
            # Error en este capítulo
            results["failed"] += 1
            results["details"].append({
                "chapter": chapter_data.get("chapter", {}).get("name", "Unknown"),
                "status": "ERROR",
                "message": ", ".join(validation.errors[:2])
            })
        else:
            # Procesar importación
            import_result = await import_service.import_content(
                validation,
                {},
                data.get("admin_chat_id")
            )

            if import_result.success:
                results["successful"] += 1
                results["details"].append({
                    "chapter": validation.chapter_data.get("name", "Unknown"),
                    "status": "✅ OK",
                    "message": f"{import_result.fragments_created} fragmentos"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "chapter": validation.chapter_data.get("name", "Unknown"),
                    "status": "ERROR",
                    "message": import_result.message
                })

    except Exception as e:
        logger.error(f"Error procesando capítulo {current_idx}: {e}", exc_info=True)
        results["failed"] += 1
        results["details"].append({
            "chapter": chapter_data.get("chapter", {}).get("name", "Unknown"),
            "status": "ERROR",
            "message": str(e)[:50]
        })

    # Actualizar y procesar siguiente
    await state.update_data(
        current_chapter_idx=current_idx + 1,
        import_results=results
    )

    # Mostrar progreso
    progress_text = (
        f"📚 Procesando capítulos...\n\n"
        f"Progreso: {current_idx + 1}/{len(chapters)}\n"
        f"✅ Éxitos: {results['successful']}\n"
        f"❌ Errores: {results['failed']}"
    )

    await processing_msg.edit_text(progress_text, parse_mode="HTML")

    # Procesar siguiente capítulo recursivamente
    await process_next_chapter(processing_msg, state, session)


async def show_batch_summary(processing_msg, results):
    """Muestra resumen de importación batch."""
    summary = (
        f"📊 <b>Importación Completada</b>\n\n"
        f"<b>Total Capítulos:</b> {results['total']}\n"
        f"<b>✅ Exitosos:</b> {results['successful']}\n"
        f"<b>❌ Errores:</b> {results['failed']}\n\n"
    )

    if results["details"]:
        summary += "<b>Detalles:</b>\n"
        for detail in results["details"][:10]:
            summary += (
                f"\n{detail['status']} <code>{detail['chapter']}</code>\n"
                f"   └ {detail['message']}"
            )

        if len(results["details"]) > 10:
            summary += f"\n\n<i>... y {len(results['details']) - 10} más</i>"

    await processing_msg.edit_text(
        summary,
        reply_markup=result_keyboard(),
        parse_mode="HTML"
    )


@narrative_admin_router.message(JsonImportStates.waiting_for_json_file)
async def process_invalid_input(message: Message):
    """Maneja entrada inválida (no es documento)."""
    await message.answer(
        "❌ Por favor envía un archivo .json\n\n"
        "No envíes texto pegado, debe ser un documento.",
        reply_markup=waiting_for_file_keyboard()
    )


# ========================================
# RESOLUCIÓN DE CONFLICTOS
# ========================================

@narrative_admin_router.callback_query(
    JsonImportStates.resolving_conflicts,
    F.data == "narr_import:conflict:update_all"
)
async def resolve_update_all(
    callback: CallbackQuery,
    state: FSMContext
):
    """Actualizar todos los fragmentos conflictivos."""
    data = await state.get_data()
    conflicts = data.get("conflicts", [])

    # Marcar todos como UPDATE
    resolutions = {
        c["fragment_key"]: ConflictResolution.UPDATE.value
        for c in conflicts
    }
    await state.update_data(conflict_resolutions=resolutions)

    await state.set_state(JsonImportStates.waiting_for_confirmation)
    await show_confirmation_from_data(callback.message, data, resolutions)
    await callback.answer("Todos los conflictos serán actualizados")


@narrative_admin_router.callback_query(
    JsonImportStates.resolving_conflicts,
    F.data == "narr_import:conflict:skip_all"
)
async def resolve_skip_all(
    callback: CallbackQuery,
    state: FSMContext
):
    """Omitir todos los fragmentos conflictivos."""
    data = await state.get_data()
    conflicts = data.get("conflicts", [])

    # Marcar todos como SKIP
    resolutions = {
        c["fragment_key"]: ConflictResolution.SKIP.value
        for c in conflicts
    }
    await state.update_data(conflict_resolutions=resolutions)

    await state.set_state(JsonImportStates.waiting_for_confirmation)
    await show_confirmation_from_data(callback.message, data, resolutions)
    await callback.answer("Todos los conflictos serán omitidos")


@narrative_admin_router.callback_query(
    JsonImportStates.resolving_conflicts,
    F.data == "narr_import:conflict:review"
)
async def start_individual_review(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar revisión individual de conflictos."""
    await state.update_data(current_conflict_idx=0)
    await state.set_state(JsonImportStates.reviewing_single_conflict)
    await show_current_conflict(callback.message, state)
    await callback.answer()


@narrative_admin_router.callback_query(
    JsonImportStates.reviewing_single_conflict,
    F.data == "narr_import:conflict:back"
)
async def back_to_conflict_options(
    callback: CallbackQuery,
    state: FSMContext
):
    """Volver a opciones de conflicto."""
    data = await state.get_data()
    conflicts = data.get("conflicts", [])

    await state.set_state(JsonImportStates.resolving_conflicts)

    conflicts_text = "\n".join([
        f"• <code>{c['fragment_key']}</code>"
        for c in conflicts[:5]
    ])

    if len(conflicts) > 5:
        conflicts_text += f"\n... y {len(conflicts) - 5} más"

    await callback.message.edit_text(
        f"⚠️ <b>Conflictos Detectados</b>\n\n"
        f"Se encontraron <b>{len(conflicts)} fragmentos</b> que ya existen:\n\n"
        f"{conflicts_text}\n\n"
        f"<b>¿Cómo deseas resolver los conflictos?</b>",
        reply_markup=conflict_resolution_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# REVISIÓN INDIVIDUAL
# ========================================

async def show_current_conflict(message: Message, state: FSMContext):
    """Muestra el conflicto actual para revisión."""
    data = await state.get_data()
    conflicts = data.get("conflicts", [])
    idx = data.get("current_conflict_idx", 0)
    resolutions = data.get("conflict_resolutions", {})

    if idx >= len(conflicts):
        # Terminamos, ir a confirmación
        await state.set_state(JsonImportStates.waiting_for_confirmation)
        await show_confirmation_from_data(message, data, resolutions)
        return

    conflict = conflicts[idx]

    text = (
        f"🔍 <b>Revisar Conflicto {idx + 1}/{len(conflicts)}</b>\n\n"
        f"<b>Fragment Key:</b> <code>{conflict['fragment_key']}</code>\n\n"
        f"<b>Título Existente:</b>\n{conflict['existing_title']}\n\n"
        f"<b>Título Nuevo:</b>\n{conflict['new_title']}\n\n"
        f"<i>¿Qué deseas hacer con este fragmento?</i>"
    )

    await message.edit_text(
        text,
        reply_markup=single_conflict_keyboard(conflict["fragment_key"]),
        parse_mode="HTML"
    )


@narrative_admin_router.callback_query(
    JsonImportStates.reviewing_single_conflict,
    F.data.startswith("narr_import:single:")
)
async def handle_single_conflict(
    callback: CallbackQuery,
    state: FSMContext
):
    """Maneja decisión individual de conflicto."""
    parts = callback.data.split(":")
    action = parts[2]  # "update" o "skip"
    fragment_key = parts[3]

    data = await state.get_data()
    resolutions = data.get("conflict_resolutions", {})

    # Guardar resolución
    resolutions[fragment_key] = action
    await state.update_data(
        conflict_resolutions=resolutions,
        current_conflict_idx=data.get("current_conflict_idx", 0) + 1
    )

    action_text = "Actualizar" if action == "update" else "Omitir"
    await callback.answer(f"{action_text}: {fragment_key}")

    # Mostrar siguiente conflicto
    await show_current_conflict(callback.message, state)


# ========================================
# CONFIRMACIÓN
# ========================================

async def show_confirmation(
    message: Message,
    validation: ValidationResult,
    resolutions: Dict[str, str]
):
    """Muestra pantalla de confirmación."""
    import_type_label = (
        "Capítulo completo" if validation.import_type.value == "chapter"
        else "Solo fragmentos"
    )

    updates = sum(1 for r in resolutions.values() if r == "update")
    skips = sum(1 for r in resolutions.values() if r == "skip")
    new_count = len(validation.fragments) - len(validation.conflicts)

    text = (
        f"✅ <b>Confirmar Importación</b>\n\n"
        f"<b>Tipo:</b> {import_type_label}\n"
        f"<b>Capítulo:</b> {validation.chapter_slug}\n\n"
        f"<b>Operaciones a realizar:</b>\n"
        f"• Fragmentos nuevos: {new_count}\n"
    )

    if updates > 0:
        text += f"• Fragmentos a actualizar: {updates}\n"
    if skips > 0:
        text += f"• Fragmentos a omitir: {skips}\n"

    text += "\n<i>¿Proceder con la importación?</i>"

    await message.edit_text(
        text,
        reply_markup=confirmation_keyboard(),
        parse_mode="HTML"
    )


async def show_confirmation_from_data(
    message: Message,
    data: Dict,
    resolutions: Dict[str, str]
):
    """Muestra confirmación desde datos de FSM."""
    import_type = data.get("import_type")
    chapter_slug = data.get("chapter_slug")
    fragments = data.get("fragments", [])
    conflicts = data.get("conflicts", [])

    import_type_label = (
        "Capítulo completo" if import_type == "chapter"
        else "Solo fragmentos"
    )

    updates = sum(1 for r in resolutions.values() if r == "update")
    skips = sum(1 for r in resolutions.values() if r == "skip")
    new_count = len(fragments) - len(conflicts)

    text = (
        f"✅ <b>Confirmar Importación</b>\n\n"
        f"<b>Tipo:</b> {import_type_label}\n"
        f"<b>Capítulo:</b> {chapter_slug}\n\n"
        f"<b>Operaciones a realizar:</b>\n"
        f"• Fragmentos nuevos: {new_count}\n"
    )

    if updates > 0:
        text += f"• Fragmentos a actualizar: {updates}\n"
    if skips > 0:
        text += f"• Fragmentos a omitir: {skips}\n"

    text += "\n<i>¿Proceder con la importación?</i>"

    await message.edit_text(
        text,
        reply_markup=confirmation_keyboard(),
        parse_mode="HTML"
    )


# ========================================
# PROCESAMIENTO FINAL
# ========================================

@narrative_admin_router.callback_query(
    JsonImportStates.waiting_for_confirmation,
    F.data == "narr_import:confirm"
)
async def execute_import(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ejecuta la importación."""
    await callback.answer("Iniciando importación...")

    # Notificar procesamiento
    await callback.message.edit_text(
        "⏳ <b>Procesando Importación...</b>\n\n"
        "Esto puede tardar unos segundos.",
        parse_mode="HTML"
    )

    data = await state.get_data()
    json_content = data.get("json_content")
    resolutions_raw = data.get("conflict_resolutions", {})
    admin_chat_id = data.get("admin_chat_id")

    # Convertir resoluciones a enum
    resolutions = {
        key: ConflictResolution(val)
        for key, val in resolutions_raw.items()
    }

    try:
        import_service = JsonImportService(session, callback.bot)

        # Re-validar (por seguridad)
        validation = await import_service.validate_json(json_content)

        if not validation.is_valid:
            await callback.message.edit_text(
                "❌ Error de validación inesperado. Intenta de nuevo.",
                reply_markup=error_keyboard()
            )
            await state.clear()
            return

        # Ejecutar importación
        result = await import_service.import_content(
            validation,
            resolutions,
            admin_chat_id
        )

        # Mostrar resultado
        await callback.message.edit_text(
            import_service.format_import_result(result),
            reply_markup=result_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error en importación: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ <b>Error Durante Importación</b>\n\n"
            f"<code>{str(e)}</code>",
            reply_markup=error_keyboard(),
            parse_mode="HTML"
        )
    finally:
        await state.clear()


# ========================================
# CANCELACIÓN
# ========================================

@narrative_admin_router.callback_query(F.data == "narr_import:cancel")
async def cancel_import(
    callback: CallbackQuery,
    state: FSMContext
):
    """Cancela importación en cualquier estado."""
    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Importación Cancelada</b>\n\n"
        "No se realizaron cambios.",
        reply_markup=error_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

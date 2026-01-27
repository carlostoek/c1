"""
Admin Content Messages Provider - Content management menu messages.

Provides messages for content package management UI with Lucien's voice.
All messages maintain Lucien's sophisticated mayordomo voice from docs/guia-estilo.md.
"""
from typing import Tuple, Optional, Any
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup

from bot.services.message.base import BaseMessageProvider
from bot.utils.keyboards import create_inline_keyboard


class AdminContentMessages(BaseMessageProvider):
    """
    Admin content management messages provider.

    Voice Characteristics (from docs/guia-estilo.md):
    - Admin = "custodio" (custodian) or "guardián" (guardian)
    - Content packages = "Paquetes de Contenido" or "tesoros del reino"
    - Uses "usted", never "tú"
    - Emoji 📦 for packages, ✏️ for edit, 🚫 for inactive, ✅ for active
    - Weighted variations: 70% formal, 30% slightly warmer for admin

    Stateless Design:
    - No session or bot stored as instance variables
    - All context passed as method parameters
    - Returns (text, keyboard) tuples for complete UI

    Examples:
        >>> provider = AdminContentMessages()
        >>> text, kb = provider.content_menu()
        >>> '📦' in text and 'custodio' in text.lower()
        True
    """

    def content_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate main content management menu.

        Returns:
            Tuple of (text, keyboard) for content management menu

        Voice Rationale:
            "Galería de tesoros" maintains elegant terminology for content.
            "Curador" (curator) reinforces admin's role as content steward.
            70% formal tone, 30% slightly warmer (admin-facing).

        Examples:
            >>> provider = AdminContentMessages()
            >>> text, kb = provider.content_menu()
            >>> '📦' in text and ('paquete' in text.lower() or 'contenido' in text.lower())
            True
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>La galería de tesoros del reino aguarda su dirección, curador...</i>"

        body = (
            f"<b>📦 Paquetes de Contenido</b>\n\n"
            f"<i>Desde aquí puede administrar los tesoros disponibles "
            f"para los miembros del círculo y los visitantes del jardín.</i>\n\n"
            f"<i>Seleccione la acción que desea realizar.</i>"
        )

        text = self._compose(header, body)
        keyboard = self._content_menu_keyboard()
        return text, keyboard

    def content_list_empty(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate message for empty content package list.

        Returns:
            Tuple of (text, keyboard) when no packages exist

        Voice Rationale:
            "Los estantes están vacíos" uses imagery of empty gallery shelves.
            Encourages creation with "primer obra maestra" (first masterpiece).

        Examples:
            >>> provider = AdminContentMessages()
            >>> text, kb = provider.content_list_empty()
            >>> 'vacío' in text.lower() or 'vacio' in text.lower()
            True
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Parece que los estantes del reino están vacíos...</i>"

        body = (
            f"<b>📦 Galería Vacía</b>\n\n"
            f"<i>No hay paquetes de contenido registrados en el reino.</i>\n\n"
            f"<i>Le sugiero comenzar con la creación de su primera obra maestra, "
            f"curador. Los visitantes del jardín agradecerán el contenido.</i>"
        )

        text = self._compose(header, body)
        keyboard = self._content_menu_keyboard()
        return text, keyboard

    def content_list_header(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate header for content package list.

        Returns:
            Tuple of (text, keyboard) with list header and empty keyboard

        Voice Rationale:
            Simple header for package list views.
            "Colección del reino" maintains elegant terminology.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>La colección del reino, curador...</i>"

        body = (
            f"<b>📦 Paquetes de Contenido</b>\n\n"
            f"<i>A continuación, los tesoros disponibles en el reino.</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([])  # Empty keyboard, handlers add list items
        return text, keyboard

    def package_summary(
        self,
        package: "ContentPackage",
        interest_count: int = 0
    ) -> str:
        """
        Format single package for list view.

        Args:
            package: ContentPackage instance
            interest_count: Number of users interested in this package

        Returns:
            Formatted HTML string for package display in list

        Voice Rationale:
            Uses category emoji and display names for quick scanning.
            "Interesados" (interested) shows user engagement.

        Examples:
            >>> from bot.database.models import ContentPackage
            >>> from bot.database.enums import ContentCategory
            >>> provider = AdminContentMessages()
            >>> pkg = ContentPackage(id=1, name="Test Pack", category=ContentCategory.FREE_CONTENT)
            >>> summary = provider.package_summary(pkg)
            >>> 'Test Pack' in summary
            True
        """
        # Get category info
        category_emoji = "🆓"
        category_name = "Gratuito"
        if package.category:
            category_str = str(package.category)
            if "vip" in category_str and "premium" in category_str:
                category_emoji = "💎"
                category_name = "VIP Premium"
            elif "vip" in category_str:
                category_emoji = "⭐"
                category_name = "VIP"

        # Status indicator
        status_emoji = "✅" if package.is_active else "🚫"
        status_text = "Activo" if package.is_active else "Inactivo"

        # Price display
        price_text = "Gratis"
        if package.price is not None:
            price_text = f"${package.price:.2f}"

        # Format summary
        summary = (
            f"<b>{category_emoji} {package.name}</b>\n"
            f"{status_emoji} <b>Estado:</b> {status_text} | "
            f"<b>Categoría:</b> {category_name} | "
            f"<b>Precio:</b> {price_text}\n"
        )

        # Add description if exists
        if package.description:
            description = package.description[:100]
            if len(package.description) > 100:
                description += "..."
            summary += f"<i>{description}</i>\n"

        # Add interest count
        if interest_count > 0:
            summary += f"👥 <b>Interesados:</b> {interest_count}\n"

        return summary

    def package_detail(
        self,
        package: "ContentPackage",
        interest_count: int = 0
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate full package details view.

        Args:
            package: ContentPackage instance
            interest_count: Number of users interested

        Returns:
            Tuple of (text, keyboard) with package details and action buttons

        Voice Rationale:
            "Detalles de la obra" treats content as artwork/masterpiece.
            Shows comprehensive information with elegant formatting.

        Examples:
            >>> from bot.database.models import ContentPackage
            >>> provider = AdminContentMessages()
            >>> pkg = ContentPackage(id=1, name="Test Pack")
            >>> text, kb = provider.package_detail(pkg)
            >>> 'Test Pack' in text
            True
        """
        # Get category info
        category_emoji = "🆓"
        category_name = "Contenido Gratuito"
        if package.category:
            category_str = str(package.category)
            if "vip_premium" in category_str:
                category_emoji = "💎"
                category_name = "VIP Premium"
            elif "vip_content" in category_str:
                category_emoji = "⭐"
                category_name = "Contenido VIP"
            elif "free_content" in category_str:
                category_emoji = "🆓"
                category_name = "Contenido Gratuito"

        # Status indicator
        status_emoji = "✅" if package.is_active else "🚫"
        status_text = "Activo" if package.is_active else "Inactivo"

        # Price display
        price_text = "Gratis"
        if package.price is not None:
            price_text = f"${package.price:.2f}"

        # Type display
        type_name = "Estándar"
        if package.type:
            type_str = str(package.type)
            if "bundle" in type_str:
                type_name = "Paquete"
            elif "collection" in type_str:
                type_name = "Colección"

        # Build detail body
        body = (
            f"<b>📦 Detalles del Paquete</b>\n\n"
            f"<b>{status_emoji} Estado:</b> {status_text}\n"
            f"<b>📝 Nombre:</b> {package.name}\n"
            f"<b>{category_emoji} Categoría:</b> {category_name}\n"
            f"<b>📦 Tipo:</b> {type_name}\n"
            f"<b>💰 Precio:</b> {price_text}\n"
        )

        # Add description if exists
        if package.description:
            body += f"\n<b>📄 Descripción:</b>\n<i>{package.description}</i>\n"

        # Add media URL if exists
        if package.media_url:
            media_preview = package.media_url[:50]
            if len(package.media_url) > 50:
                media_preview += "..."
            body += f"\n<b>🔗 Media:</b> <code>{media_preview}</code>\n"

        # Add timestamps
        if package.created_at:
            created = package.created_at.strftime("%Y-%m-%d %H:%M")
            body += f"\n<b>📅 Creado:</b> {created}\n"

        if package.updated_at and package.updated_at != package.created_at:
            updated = package.updated_at.strftime("%Y-%m-%d %H:%M")
            body += f"<b>🔄 Actualizado:</b> {updated}\n"

        # Add interest count
        if interest_count > 0:
            body += f"\n👥 <b>Interesados:</b> {interest_count} usuario(s)\n"

        header = "🎩 <b>Lucien:</b>\n\n<i>Los detalles de la obra seleccionada, curador...</i>"
        text = self._compose(header, body)
        keyboard = self._package_detail_keyboard(package.id, package.is_active)
        return text, keyboard

    def create_welcome(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate welcome message for package creation wizard.

        Returns:
            Tuple of (text, keyboard) starting the creation flow

        Voice Rationale:
            "Nueva obra maestra" treats content creation as artistic endeavor.
            Encourages admin with "creatividad" (creativity) terminology.

        Examples:
            >>> provider = AdminContentMessages()
            >>> text, kb = provider.create_welcome()
            >>> 'crear' in text.lower() or 'nuevo' in text.lower()
            True
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Excelente decisión, curador. El reino siempre acepta nuevas obras...</i>"

        body = (
            f"<b>➕ Crear Nuevo Paquete</b>\n\n"
            f"<i>Le guiaré en la creación de un nuevo paquete de contenido "
            f"para enriquecer la experiencia del círculo y del jardín.</i>\n\n"
            f"<i>Prepare su creatividad. Comencemos.</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "⏭️ Comenzar", "callback_data": "admin:content:create:start"}],
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    def create_step_name(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate prompt for package name input.

        Returns:
            Tuple of (text, keyboard) for name input step

        Voice Rationale:
            "Paso 1/4" indicates progress in wizard.
            Simple, clear instruction for name input.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>El primer paso hacia una nueva obra...</i>"

        body = (
            f"<b>➕ Paso 1/4: Nombre del Paquete</b>\n\n"
            f"<i>Por favor, proporcione el nombre de este paquete de contenido.</i>\n\n"
            f"<i>Un nombre evocador atraerá a los miembros del círculo "
            f"y a los visitantes del jardín por igual.</i>\n\n"
            f"<b>Envíe el nombre ahora:</b>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    def create_step_type(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate prompt for package type selection.

        Returns:
            Tuple of (text, keyboard) with type selection buttons

        Voice Rationale:
            "Naturaleza de la obra" (nature of the work) for type selection.
            Inline buttons provide clear choices without ambiguity.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Excelente nombre. Ahora, definamos su naturaleza...</i>"

        body = (
            f"<b>➕ Paso 2/4: Tipo de Contenido</b>\n\n"
            f"<i>Seleccione la categoría más apropiada para esta obra.</i>\n\n"
            f"<i>Considere quién podrá acceder: ¿todos los visitantes, "
            f"solo el círculo exclusivo, o los miembros más distinguidos?</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [
                {"text": "🆓 Contenido Gratuito", "callback_data": "admin:content:create:type:free_content"},
                {"text": "⭐ Contenido VIP", "callback_data": "admin:content:create:type:vip_content"}
            ],
            [
                {"text": "💎 VIP Premium", "callback_data": "admin:content:create:type:vip_premium"},
            ],
            [{"text": "❌ Cancelar", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    def create_step_price(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate prompt for package price input.

        Returns:
            Tuple of (text, keyboard) for price input step

        Voice Rationale:
            Price is optional - /skip allows proceeding without price.
            "Valor" (value) sounds more elegant than "precio".
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>La categoría ha sido registrada. Ahora, el valor...</i>"

        body = (
            f"<b>➕ Paso 3/4: Precio (Opcional)</b>\n\n"
            f"<i>Asigne un precio a este paquete, si corresponde.</i>\n\n"
            f"<i>Puede enviar un valor numérico (ej: 9.99) o /skip para omitir "
            f"y dejar el contenido gratuito.</i>\n\n"
            f"<b>Envíe el precio o /skip:</b>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "⏭️ Omitir (/skip)", "callback_data": "admin:content:create:skip:price"}],
            [{"text": "❌ Cancelar", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    def create_step_description(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate prompt for package description input.

        Returns:
            Tuple of (text, keyboard) for description input step

        Voice Rationale:
            Description is optional - /skip allows proceeding.
            "Descripción" guides users on package contents.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Excelente. Finalmente, los detalles...</i>"

        body = (
            f"<b>➕ Paso 4/4: Descripción (Opcional)</b>\n\n"
            f"<i>Proporcione una descripción que informe a los miembros "
            f"sobre el contenido de este paquete.</i>\n\n"
            f"<i>Puede enviar una descripción detallada o /skip para omitir "
            f"este paso y finalizar.</i>\n\n"
            f"<b>Envíe la descripción o /skip:</b>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "⏭️ Omitir (/skip)", "callback_data": "admin:content:create:skip:description"}],
            [{"text": "❌ Cancelar", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    def create_success(self, package: "ContentPackage") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate success message after package creation.

        Args:
            package: Newly created ContentPackage instance

        Returns:
            Tuple of (text, keyboard) with confirmation and next actions

        Voice Rationale:
            "Obra maestra añadida" (masterpiece added) celebrates creation.
            Options to view, create another, or return to main menu.

        Examples:
            >>> from bot.database.models import ContentPackage
            >>> provider = AdminContentMessages()
            >>> pkg = ContentPackage(id=1, name="Test Pack")
            >>> text, kb = provider.create_success(pkg)
            >>> 'test pack' in text.lower() or 'creado' in text.lower()
            True
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Enhorabuena, curador. Una nueva obra adorna el reino...</i>"

        body = (
            f"<b>✅ Paquete Creado Exitosamente</b>\n\n"
            f"<b>📦 {package.name}</b>\n"
            f"<i>El paquete ha sido registrado y está disponible para "
            f"los miembros del círculo y los visitantes del jardín.</i>\n\n"
            f"<i>¿Qué desea hacer ahora?</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [
                {"text": "👁️ Ver Paquete", "callback_data": f"admin:content:view:{package.id}"},
                {"text": "➕ Crear Otro", "callback_data": "admin:content:create:start"}
            ],
            [{"text": "🔙 Menú Principal", "callback_data": "admin:main"}],
        ])
        return text, keyboard

    def edit_prompt(
        self,
        field_name: str,
        current_value: Any
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate prompt for editing a specific field.

        Args:
            field_name: Name of the field being edited
            current_value: Current value of the field

        Returns:
            Tuple of (text, keyboard) for edit prompt

        Voice Rationale:
            "✏️ Editar" indicates modification action.
            Shows current value for reference before editing.

        Examples:
            >>> provider = AdminContentMessages()
            >>> text, kb = provider.edit_prompt("Nombre", "Pack Viejo")
            >>> 'editar' in text.lower() and 'pack viejo' in text.lower()
            True
        """
        # Format current value for display
        if current_value is None:
            current_display = "<i>(vacío)</i>"
        elif isinstance(current_value, bool):
            current_display = "✅ Sí" if current_value else "❌ No"
        elif isinstance(current_value, float):
            current_display = f"${current_value:.2f}"
        else:
            current_display = str(current_value)
            # Limit display length
            if len(current_display) > 100:
                current_display = current_display[:97] + "..."

        header = f"🎩 <b>Lucien:</b>\n\n<i>Modificando {field_name.lower()}...</i>"

        body = (
            f"<b>✏️ Editar {field_name}</b>\n\n"
            f"<b>Valor actual:</b>\n{current_display}\n\n"
            f"<i>Envíe el nuevo valor para este campo.</i>\n\n"
            f"<b>Envíe el nuevo valor:</b>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:content:cancel_edit"}],
        ])
        return text, keyboard

    def deactivate_confirm(self, package: "ContentPackage") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate confirmation prompt for package deactivation.

        Args:
            package: ContentPackage to deactivate

        Returns:
            Tuple of (text, keyboard) with yes/no confirmation

        Voice Rationale:
            "Desactivar" (deactivate) instead of "eliminar" (delete) - soft delete.
            "Retirar de la galería" (remove from gallery) uses elegant imagery.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Una decisión que requiere confirmación...</i>"

        body = (
            f"<b>🚫 Desactivar Paquete</b>\n\n"
            f"<i>Está a punto de retirar este paquete de la galería del reino:</i>\n\n"
            f"<b>📦 {package.name}</b>\n\n"
            f"<i>El paquete dejará de estar disponible para nuevos miembros, "
            f"pero permanecerá en los registros.</i>\n\n"
            f"<i>¿Confirma esta acción, curador?</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [
                {"text": "✅ Sí, Desactivar", "callback_data": f"admin:content:deactivate:{package.id}"},
                {"text": "❌ No, Cancelar", "callback_data": f"admin:content:view:{package.id}"}
            ],
        ])
        return text, keyboard

    def reactivate_confirm(self, package: "ContentPackage") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate confirmation prompt for package reactivation.

        Args:
            package: ContentPackage to reactivate

        Returns:
            Tuple of (text, keyboard) with yes/no confirmation

        Voice Rationale:
            "Restaurar a la galería" (restore to gallery) for reactivation.
            Opposite of deactivate - brings content back to availability.
        """
        header = "🎩 <b>Lucien:</b>\n\n<i>Una decisión que requiere confirmación...</i>"

        body = (
            f"<b>✅ Reactivar Paquete</b>\n\n"
            f"<i>Está a punto de restaurar este paquete a la galería del reino:</i>\n\n"
            f"<b>📦 {package.name}</b>\n\n"
            f"<i>El paquete volverá a estar disponible para todos los miembros "
            f"del círculo y los visitantes del jardín.</i>\n\n"
            f"<i>¿Confirma esta acción, curador?</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [
                {"text": "✅ Sí, Reactivar", "callback_data": f"admin:content:reactivate:{package.id}"},
                {"text": "❌ No, Cancelar", "callback_data": f"admin:content:view:{package.id}"}
            ],
        ])
        return text, keyboard

    def toggle_success(self, package: "ContentPackage") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Generate success message after package toggle (activate/deactivate).

        Args:
            package: ContentPackage that was toggled

        Returns:
            Tuple of (text, keyboard) with confirmation message

        Voice Rationale:
            Adapts message based on new active status.
            "Disponible" or "retirado" depending on state change.
        """
        if package.is_active:
            header = "🎩 <b>Lucien:</b>\n\n<i>La obra vuelve a brillar en el reino...</i>"
            status_text = "reactivado"
            status_emoji = "✅"
        else:
            header = "🎩 <b>Lucien:</b>\n\n<i>La obra ha sido retirada de la galería...</i>"
            status_text = "desactivado"
            status_emoji = "🚫"

        body = (
            f"<b>{status_emoji} Paquete {status_text.title()}</b>\n\n"
            f"<b>📦 {package.name}</b>\n"
            f"<i>El cambio ha sido aplicado exitosamente.</i>"
        )

        text = self._compose(header, body)
        keyboard = create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "admin:content"}],
        ])
        return text, keyboard

    # ===== PRIVATE KEYBOARD FACTORY METHODS =====

    def _content_menu_keyboard(self) -> InlineKeyboardMarkup:
        """
        Generate keyboard for main content management menu.

        Returns:
            InlineKeyboardMarkup with content navigation options

        Voice Rationale:
            "Ver Paquetes" (view packages), "Crear Paquete" (create package).
            Spanish terminology maintained throughout.
        """
        return create_inline_keyboard([
            [{"text": "📋 Ver Paquetes", "callback_data": "admin:content:list"}],
            [{"text": "➕ Crear Paquete", "callback_data": "admin:content:create:start"}],
            [{"text": "🔙 Volver al Menú Principal", "callback_data": "admin:main"}],
        ])

    def _package_detail_keyboard(
        self,
        package_id: int,
        is_active: bool
    ) -> InlineKeyboardMarkup:
        """
        Generate keyboard for package detail view.

        Args:
            package_id: ID of the package
            is_active: Current active status of the package

        Returns:
            InlineKeyboardMarkup with package action buttons

        Voice Rationale:
            Action buttons adapt based on package state.
            "Editar", "Desactivar"/"Reactivar", "Volver".
        """
        action_text = "🚫 Desactivar" if is_active else "✅ Reactivar"
        action_callback = f"admin:content:deactivate:{package_id}" if is_active else f"admin:content:reactivate:{package_id}"

        return create_inline_keyboard([
            [{"text": "✏️ Editar", "callback_data": f"admin:content:edit:{package_id}"}],
            [{"text": action_text, "callback_data": action_callback}],
            [{"text": "🔙 Volver", "callback_data": "admin:content:list"}],
        ])

# Plan: Sistema de Menús Diferenciados VIP/FREE

## Objetivo
Implementar menús diferenciados según rol de usuario (VIP vs FREE), integrando el MenuService existente de la branch `sinmenus` y estableciendo un sistema robusto de navegación comercial.

---

## Arquitectura General

```
Usuario ejecuta /start
    ↓
¿Es Admin? → Sí → Menú Admin
    ↓ No
¿Es VIP? → Sí → Menú VIP (completo)
    ↓ No
¿Completó onboarding? → Sí → Menú FREE (comercial + historia)
    ↓ No
Menú FREE (comercial) + Opciones bloqueadas con mensaje Lucien
```

---

## Fase 1: Integrar MenuService (Base)

### 1.1 Traer modelos de BD desde `sinmenus`
**Archivos a crear/modificar:**
- `bot/database/models_menu.py` (NUEVO) - Modelos MenuItem y MenuConfig

```python
class MenuItem(Base):
    """Item de menú configurable por admin."""
    __tablename__ = "menu_items"

    id: int (PK)
    item_key: str (UNIQUE)       # "free_sets", "vip_premium"
    target_role: str             # 'vip', 'free', 'all'
    parent_key: Optional[str]    # Para submenús
    button_text: str
    button_emoji: Optional[str]
    action_type: str             # 'submenu', 'info', 'callback', 'url', 'blocked'
    action_content: str          # Contenido según tipo
    display_order: int
    row_number: int
    requires_onboarding: bool    # Si requiere onboarding completado
    is_active: bool
    created_by: Optional[int]

class MenuConfig(Base):
    """Configuración de menú por rol."""
    __tablename__ = "menu_configs"

    id: int (PK)
    role: str (UNIQUE)           # 'vip', 'free', 'profile'
    welcome_message: str
    footer_message: Optional[str]
    show_subscription_info: bool
```

### 1.2 Crear MenuService
**Archivo:** `bot/services/menu_service.py`

```python
class MenuService:
    async def get_menu_for_role(self, role: str, user_completed_onboarding: bool) -> List[MenuItem]
    async def build_keyboard_for_role(self, role: str, user_id: int) -> List[List[Dict]]
    async def create_menu_item(self, **kwargs) -> MenuItem
    async def update_menu_item(self, item_key: str, **kwargs) -> MenuItem
    async def delete_menu_item(self, item_key: str) -> bool
    async def get_submenu_items(self, parent_key: str) -> List[MenuItem]
```

### 1.3 Integrar en ServiceContainer
**Archivo:** `bot/services/container.py`

```python
@property
def menu(self) -> MenuService:
    if self._menu_service is None:
        from bot.services.menu_service import MenuService
        self._menu_service = MenuService(self._session)
    return self._menu_service
```

### 1.4 Migración de BD
**Archivo:** `alembic/versions/XXX_add_menu_system.py`

---

## Fase 2: Menús Diferenciados VIP/FREE

### 2.1 Modificar `build_start_menu()`
**Archivo:** `bot/utils/menu_helpers.py`

```python
async def build_start_menu(
    session: AsyncSession,
    bot,
    user_id: int,
    user_name: str,
    container: ServiceContainer = None
) -> Tuple[str, InlineKeyboardMarkup]:

    # Obtener usuario y su rol
    user = await container.user.get_user(user_id)
    role = user.role.value if user else "free"

    # Verificar si completó onboarding
    narrative = NarrativeContainer(session, bot)
    completed_onboarding = await narrative.onboarding.has_completed_onboarding(user_id)

    # Construir menú según rol
    keyboard_buttons = await container.menu.build_keyboard_for_role(
        role=role,
        user_id=user_id,
        completed_onboarding=completed_onboarding
    )

    # Mensaje de bienvenida diferenciado
    lucien = LucienVoiceService()
    if role == "vip":
        welcome_message = await lucien.get_welcome_message("vip_user")
    else:
        welcome_message = await lucien.get_welcome_message("free_user")

    return welcome_message, create_inline_keyboard(keyboard_buttons)
```

### 2.2 Estructura de Menú FREE
```
📢 Información de Contenido
├── 🌸 Sets
│   ├── Encanto Inicial → [Info + "Me interesa"]
│   ├── Sensualidad Revelada → [Info + "Me interesa"]
│   ├── Pasión Desbordante → [Info + "Me interesa"]
│   └── Intimidad Explosiva → [Info + "Me interesa"]
├── ✨ Personalizados → [Info + "Me interesa"]
└── 🔙 Volver

📜 Mi Historia → [BLOQUEADO si no completó onboarding]
📊 Mi Perfil → [BLOQUEADO si no completó onboarding]
🎮 Juegos → [BLOQUEADO si no completó onboarding]

⭐ ¡Hazte VIP! → [Info planes VIP]
```

### 2.3 Estructura de Menú VIP
```
🛋️ Mi Diván → [Por implementar - placeholder]
💎 Contenido Premium → [Acceso a contenido]
🗺️ Mapa del Deseo → [Acceso a producto]
📜 Mi Historia → [Narrativa completa]
📊 Mi Perfil → [Gamificación completa]
```

### 2.4 Handler para opciones bloqueadas
**Archivo:** `bot/handlers/user/menu_handlers.py` (NUEVO)

```python
@user_router.callback_query(F.data.startswith("blocked:"))
async def callback_blocked_option(callback: CallbackQuery, session: AsyncSession):
    """Muestra mensaje de Lucien cuando usuario intenta acceder a opción bloqueada."""
    lucien = LucienVoiceService()
    message = await lucien.get_message("onboarding_required")

    keyboard = create_inline_keyboard([
        [{"text": "📖 Iniciar Tutorial", "callback_data": "onboard:start"}],
        [{"text": "🔙 Volver", "callback_data": "profile:back"}]
    ])

    await callback.message.edit_text(message, reply_markup=keyboard, parse_mode="HTML")
```

---

## Fase 3: Sistema "Me Interesa"

### 3.1 Modelo UserInterest
**Archivo:** `bot/database/models_menu.py`

```python
class UserInterest(Base):
    """Registro de interés de usuario en producto."""
    __tablename__ = "user_interests"

    id: int (PK)
    user_id: BigInteger (FK)
    product_type: str            # "set", "personalizado", "vip"
    product_key: str             # "encanto_inicial", "sensualidad_revelada"
    status: str                  # "pending", "contacted", "converted", "rejected"
    created_at: datetime
    contacted_at: Optional[datetime]
    contacted_by: Optional[int]  # Admin que contactó
    notes: Optional[str]
```

### 3.2 InterestService
**Archivo:** `bot/services/interest_service.py`

```python
class InterestService:
    async def register_interest(self, user_id: int, product_type: str, product_key: str) -> UserInterest
    async def get_pending_interests(self, limit: int = 50) -> List[UserInterest]
    async def mark_as_contacted(self, interest_id: int, admin_id: int) -> UserInterest
    async def get_user_interests(self, user_id: int) -> List[UserInterest]
```

### 3.3 Handler "Me interesa"
**Archivo:** `bot/handlers/user/menu_handlers.py`

```python
@user_router.callback_query(F.data.startswith("interest:"))
async def callback_interest(callback: CallbackQuery, session: AsyncSession):
    """Usuario expresa interés en producto."""
    # Parsear: interest:set:encanto_inicial
    parts = callback.data.split(":")
    product_type = parts[1]
    product_key = parts[2]

    container = ServiceContainer(session, callback.bot)

    # Registrar interés
    interest = await container.interest.register_interest(
        user_id=callback.from_user.id,
        product_type=product_type,
        product_key=product_key
    )

    # Notificar a admin
    await _notify_admin_interest(callback.bot, interest, callback.from_user)

    # Responder al usuario (voz de Diana)
    await callback.message.edit_text(
        "💋 <b>¡Gracias por tu interés!</b>\n\n"
        "Me pondré en contacto contigo lo antes posible.\n\n"
        "<i>— Diana</i>",
        parse_mode="HTML",
        reply_markup=create_inline_keyboard([
            [{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}]
        ])
    )
```

### 3.4 Notificación a Admin
```python
async def _notify_admin_interest(bot, interest: UserInterest, user):
    """Notifica a admins sobre nuevo interés."""
    from config import Config

    text = (
        f"🔔 <b>Nuevo Interés</b>\n\n"
        f"👤 Usuario: {user.first_name} (@{user.username or 'sin username'})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📦 Producto: {interest.product_type} - {interest.product_key}\n"
        f"🕐 Fecha: {interest.created_at.strftime('%d/%m/%Y %H:%M')}"
    )

    keyboard = create_inline_keyboard([
        [
            {"text": "💬 Responder", "callback_data": f"admin:contact:{interest.id}"},
            {"text": "✅ Marcar Contactado", "callback_data": f"admin:contacted:{interest.id}"}
        ],
        [
            {"text": "🚫 Bloquear Usuario", "callback_data": f"admin:block:{user.id}"},
            {"text": "👋 Expulsar", "callback_data": f"admin:kick:{user.id}"}
        ]
    ])

    for admin_id in Config.ADMIN_USER_IDS:
        await bot.send_message(admin_id, text, reply_markup=keyboard, parse_mode="HTML")
```

### 3.5 Handlers Admin para gestionar intereses
**Archivo:** `bot/handlers/admin/interests.py` (NUEVO)

```python
@admin_router.callback_query(F.data.startswith("admin:contact:"))
async def callback_admin_contact(callback: CallbackQuery, session: AsyncSession):
    """Admin inicia contacto con usuario interesado."""
    # Abrir chat directo con el usuario

@admin_router.callback_query(F.data.startswith("admin:contacted:"))
async def callback_admin_mark_contacted(callback: CallbackQuery, session: AsyncSession):
    """Admin marca interés como contactado."""

@admin_router.callback_query(F.data.startswith("admin:block:"))
async def callback_admin_block_user(callback: CallbackQuery, session: AsyncSession):
    """Admin bloquea usuario."""
```

---

## Fase 4: Mensajes de Lucien Diferenciados

### 4.1 Agregar mensajes en LucienVoiceService
**Archivo:** `bot/services/lucien_voice.py`

```python
# Nuevos tipos de mensaje:
"vip_user": "Bienvenido de vuelta... {name}. Diana lo espera."
"free_user": "Ah, llegó alguien nuevo... Vea lo que Diana tiene para ofrecer."
"onboarding_required": "Esta área requiere que complete el tutorial primero..."
"interest_registered": "Su interés ha sido registrado. Diana se comunicará pronto."
```

---

## Fase 5: Seed de Menús Iniciales

### 5.1 Script de seed
**Archivo:** `scripts/seed_menus.py`

```python
async def seed_free_menu():
    """Crea menú inicial para usuarios FREE."""
    items = [
        MenuItem(item_key="free_content", button_text="📢 Información de Contenido",
                 target_role="free", action_type="submenu", display_order=1),
        MenuItem(item_key="free_sets", button_text="🌸 Sets", parent_key="free_content",
                 target_role="free", action_type="submenu", display_order=1),
        # ... más items
    ]

async def seed_vip_menu():
    """Crea menú inicial para usuarios VIP."""
    items = [
        MenuItem(item_key="vip_divan", button_text="🛋️ Mi Diván",
                 target_role="vip", action_type="callback", action_content="vip:divan"),
        # ... más items
    ]
```

---

## Archivos a Modificar/Crear

### Nuevos:
1. `bot/database/models_menu.py` - Modelos MenuItem, MenuConfig, UserInterest
2. `bot/services/menu_service.py` - MenuService completo
3. `bot/services/interest_service.py` - InterestService
4. `bot/handlers/user/menu_handlers.py` - Handlers de menú y "Me interesa"
5. `bot/handlers/admin/interests.py` - Gestión de intereses
6. `alembic/versions/XXX_add_menu_system.py` - Migración
7. `scripts/seed_menus.py` - Seed de menús iniciales

### Modificar:
1. `bot/utils/menu_helpers.py` - Usar MenuService
2. `bot/services/container.py` - Agregar menu e interest services
3. `bot/services/lucien_voice.py` - Nuevos mensajes
4. `bot/database/__init__.py` - Exportar nuevos modelos
5. `bot/handlers/user/__init__.py` - Registrar nuevos handlers

### Eliminar/Deprecar:
1. Referencias rotas a `container.menu` actuales (línea 115 menu_helpers.py)

---

## Verificación

### Tests a ejecutar:
```bash
# Después de implementación
python -m pytest tests/test_menu_service.py -v
python -m pytest tests/test_interest_service.py -v
```

### Pruebas manuales:
1. `/start` como usuario FREE → Ver menú comercial
2. Clic en "Sets" → Ver submenú
3. Clic en "Me interesa" → Recibir confirmación + admin recibe notificación
4. Clic en opción bloqueada → Ver mensaje de Lucien
5. `/start` como usuario VIP → Ver menú VIP diferente
6. Admin: responder/bloquear desde notificación

---

## Orden de Implementación

1. **Fase 1**: Modelos + MenuService + Migración
2. **Fase 2**: Modificar `build_start_menu()` + handlers bloqueados
3. **Fase 3**: Sistema "Me interesa" + notificaciones
4. **Fase 4**: Mensajes Lucien
5. **Fase 5**: Seed + Tests

**Tiempo estimado**: ~4-6 horas de implementación

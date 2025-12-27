# Guía de Instalación - Módulo de Tienda y Mochila

## 📋 Requisitos Previos

Antes de instalar el módulo de tienda y mochila, asegúrate de tener:

- Python 3.11+
- SQLAlchemy 2.0+
- Aiogram 3.4.1+
- SQLite (o PostgreSQL para producción)
- Alembic para migraciones
- Bot de Telegram con permisos adecuados
- Módulo de gamificación instalado y configurado (requerido para besitos)

## 🚀 Instalación Paso a Paso

### 1. Aplicar Migraciones de Base de Datos

El módulo requiere una estructura de base de datos específica. Aplica las migraciones:

```bash
alembic upgrade head
```

Esto creará las 5 tablas necesarias para el sistema de tienda y mochila:

- `shop_item_categories` - Categorías de productos
- `shop_items` - Productos de la tienda
- `user_inventories` - Inventario personal de usuarios
- `user_inventory_items` - Items poseídos por usuarios
- `shop_item_purchases` - Historial de compras

### 2. Configurar Variables de Entorno

Agrega las siguientes variables al archivo `.env`:

```env
# Configuración de la Tienda
SHOP_ENABLED=true
SHOP_MAX_ITEMS_PER_PAGE=5
SHOP_PURCHASE_COOLDOWN_SECONDS=5
SHOP_MAX_ITEMS_PER_USER=1000

# Configuración de Inventarios
INVENTORY_ENABLED=true
INVENTORY_MAX_SIZE=500
INVENTORY_AUTO_CLEAN_DAYS=365

# Configuración de Seguridad
PURCHASE_VALIDATION_ENABLED=true
ANTI_FRAUD_CHECKS=true
MAX_QUANTITY_PER_PURCHASE=10

# Configuración de Regalo Diario
DAILY_GIFT_ENABLED=true
DAILY_GIFT_BESITOS=10
```

### 3. Inicializar Datos Básicos

Después de aplicar migraciones, puedes crear datos iniciales como categorías y productos:

```python
# Crear contenedor de servicios
from bot.shop.services.container import ShopContainer

container = ShopContainer(session)

# Crear categoría inicial
category = await container.shop.create_category(
    name="Artefactos Narrativos",
    description="Items que desbloquean contenido en la historia",
    emoji="📜",
    order=1
)

# Crear producto de ejemplo
success, message, item = await container.shop.create_item(
    category_id=category.id,
    name="Mapa Secreto",
    description="Revela ubicación oculta en el capítulo 3",
    item_type=ItemType.NARRATIVE,
    price_besitos=200,
    created_by=admin_user_id,  # ID del admin que crea
    rarity=ItemRarity.UNCOMMON,
    icon="🗺️",
    stock=50,  # Limitado a 50 unidades
    max_per_user=1  # Máximo 1 por usuario
)
```

### 4. Integrar con el Bot Existente

Asegúrate de registrar los handlers en tu bot principal:

```python
# En main.py o donde registres tus routers
from bot.shop.handlers.user import shop_user_router, backpack_router

# Registrar routers de la tienda
dp.include_router(shop_user_router)
dp.include_router(backpack_router)

# También puedes registrarlos en routers específicos si los tienes organizados por módulo
```

### 5. Configurar Servicios en Container Principal

Integra el container de la tienda con el container principal si usas un sistema de inyección de dependencias:

```python
# Ejemplo de integración con container principal
from bot.services.container import ServiceContainer  # Container principal
from bot.shop.services.container import ShopContainer  # Container de la tienda

# En tu archivo de setup principal
class MainContainer(ServiceContainer):
    def __init__(self, session, bot):
        super().__init__(session, bot)
        self._shop_container = None
    
    @property
    def shop(self):
        if self._shop_container is None:
            from bot.shop.services.container import ShopContainer
            self._shop_container = ShopContainer(self.session, self.bot)
        return self._shop_container
```

## 🔧 Configuración Avanzada

### Configuración Personalizada

Puedes personalizar el comportamiento del sistema creando entradas en la tabla `shop_settings` o integrando con la configuración global:

```python
from bot.shop.database.models import ShopSettings

settings = ShopSettings(
    default_item_rarity=ItemRarity.COMMON,
    allow_refunds=True,
    refund_cool_down_hours=24,
    low_stock_threshold=5,
    featured_rotation_days=7
)
session.add(settings)
await session.commit()
```

### Integración con Sistema de Reacciones y Gamificación

Para que la tienda funcione correctamente con el sistema de besitos, asegúrate que el BesitoService esté correctamente integrado:

```python
# Los servicios de tienda ya están integrados para usar BesitoService
# automáticamente al procesar compras
async def purchase_item(self, user_id: int, item_id: int, quantity: int = 1):
    # ... validación ...
    
    # Deducir besitos usando el servicio de besitos
    from bot.gamification.services.besito import BesitoService
    from bot.gamification.database.enums import TransactionType
    
    besito_service = BesitoService(self.session)
    success, msg, _ = await besito_service.deduct_besitos(
        user_id=user_id,
        amount=total_price,
        transaction_type=TransactionType.PURCHASE,
        description=f"Compra: {item.name} x{quantity}"
    )
    
    # El resto del procesamiento ...
```

## 🧪 Pruebas de Instalación

Después de la instalación, puedes verificar que todo esté funcionando:

1. Verifica que las tablas se hayan creado correctamente
2. Prueba el comando `/tienda` en el bot
3. Prueba el comando `/mochila` en el bot
4. Verifica que puedes crear categorías y productos de ejemplo
5. Confirma que se pueden procesar compras
6. Verifica que se actualiza correctamente el inventario

## 🔍 Troubleshooting

### Problemas Comunes

**Error en migraciones**: Asegúrate de que alembic esté configurado correctamente con el módulo de tienda.

**Comandos no funcionan**: Verifica que hayas registrado los routers correctamente en el dispatcher.

**No puedes comprar**: Confirma que el usuario tenga besitos suficientes y que el stock esté disponible.

### Verificación de Salud

Puedes verificar el estado del sistema con:

```python
from bot.shop.services.container import ShopContainer

container = ShopContainer(session)
shop_summary = await container.shop.get_shop_summary()  # Ver resumen de la tienda
inventory_summary = await container.inventory.get_inventory_summary(user_id)  # Ver inventario de usuario
```

## 🔄 Actualización de Versiones

Para actualizar a nuevas versiones del módulo:

1. Aplica nuevas migraciones: `alembic upgrade head`
2. Verifica la compatibilidad con tu versión actual de Aiogram
3. Prueba las funcionalidades críticas en un entorno de test
4. Actualiza las configuraciones necesarias en `.env`

## ✅ Verificación Final

Después de completar la instalación:

- [ ] Migraciones aplicadas correctamente
- [ ] Variables de entorno configuradas
- [ ] Categoría de ejemplo creada
- [ ] Producto de ejemplo creado
- [ ] Handlers registrados
- [ ] Pruebas básicas pasadas (ver tienda, ver mochila)
- [ ] Prueba de compra exitosa
- [ ] Verificación de actualización de inventario
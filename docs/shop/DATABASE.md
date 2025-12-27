# Documentación de Base de Datos - Módulo de Tienda y Mochila

## 📋 Resumen de Modelos

El módulo de tienda y mochila utiliza 5 modelos principales en SQLAlchemy 2.0 con soporte para relaciones y optimización de consultas:

| Modelo | Propósito | Registros (estimado) |
|--------|----------|---------------------|
| `ItemCategory` | Categorías de productos (Artefactos, Paquetes, etc.) | 5-20 |
| `ShopItem` | Productos disponibles en la tienda | 20-200 |
| `UserInventory` | Inventario personal de cada usuario | 1 por usuario activo |
| `UserInventoryItem` | Items poseídos por cada usuario | Variable (1-1000+) |
| `ItemPurchase` | Registro de todas las compras | Variable (1-5000+) |

## Modelo 1: ItemCategory

**Descripción:** Categoría de productos en la tienda que permite organizar los productos de forma lógica.

**Tabla:** `shop_item_categories`

### Estructura

```python
class ItemCategory(Base):
    __tablename__ = "shop_item_categories"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Información básica
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String(10), default="📦")
    
    # Metadatos
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    items: Mapped[List["ShopItem"]] = relationship(
        "ShopItem",
        back_populates="category",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index("idx_shop_category_order", "order"),
        Index("idx_shop_category_active", "is_active"),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK | ID único de la categoría |
| `name` | VARCHAR(100) | NOT NULL | Nombre de la categoría (ej: "Artefactos Narrativos") |
| `slug` | VARCHAR(50) | UNIQUE, NOT NULL | Identificador amigable para URLs |
| `description` | TEXT | NULL | Descripción de la categoría |
| `emoji` | VARCHAR(10) | DEFAULT "📦" | Emoji representativo |
| `order` | INTEGER | DEFAULT 0 | Orden de visualización (menor = primero) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Si la categoría es visible en la tienda |
| `created_at` | DATETIME | NOT NULL | Fecha de creación |

### Índices

```sql
-- Búsqueda por orden de categoría
CREATE INDEX idx_shop_category_order ON shop_item_categories(order);

-- Filtrar categorías activas
CREATE INDEX idx_shop_category_active ON shop_item_categories(is_active);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "name": "Artefactos Narrativos",
    "slug": "artefactos-narrativos",
    "description": "Items que desbloquean contenido en la historia",
    "emoji": "📜",
    "order": 1,
    "is_active": true,
    "created_at": "2025-12-27T10:15:30.123456"
}
```

### Operaciones Comunes

```python
from bot.shop.database.models import ItemCategory

# Crear categoría
async with get_session() as session:
    category = ItemCategory(
        name="Cosméticos VIP",
        slug="cosmeticos-vip",
        description="Items especiales para usuarios VIP",
        emoji="👑",
        order=2,
        is_active=True
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)

# Buscar categoría por slug
async with get_session() as session:
    query = select(ItemCategory).where(ItemCategory.slug == "artefactos-narrativos")
    result = await session.execute(query)
    category = result.scalar_one_or_none()

# Buscar categorías activas ordenadas
async with get_session() as session:
    query = select(ItemCategory).where(
        ItemCategory.is_active == True
    ).order_by(ItemCategory.order)
    result = await session.execute(query)
    categories = result.scalars().all()
```

## Modelo 2: ShopItem

**Descripción:** Producto disponible en la tienda con precios, stock y metadatos específicos.

**Tabla:** `shop_items`

### Estructura

```python
class ShopItem(Base):
    __tablename__ = "shop_items"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relación con categoría
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_item_categories.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Información del producto
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tipo y rareza
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ItemType
    rarity: Mapped[str] = mapped_column(String(20), default="common")
    
    # Precio
    price_besitos: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Visual
    icon: Mapped[str] = mapped_column(String(10), default="📦")
    image_file_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Metadatos (JSON)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Stock y límites
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = ilimitado
    max_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Requisitos
    requires_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Estado y ordenamiento
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Auditoría
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    category: Mapped["ItemCategory"] = relationship("ItemCategory", back_populates="items")
    inventory_items: Mapped[List["UserInventoryItem"]] = relationship(
        "UserInventoryItem",
        back_populates="item",
        cascade="all, delete-orphan"
    )
    purchases: Mapped[List["ItemPurchase"]] = relationship(
        "ItemPurchase",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index("idx_shop_item_category", "category_id"),
        Index("idx_shop_item_type", "item_type"),
        Index("idx_shop_item_active", "is_active"),
        Index("idx_shop_item_featured", "is_featured"),
        Index("idx_shop_item_order", "order"),
        Index("idx_shop_item_price", "price_besitos"),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK | ID único del producto |
| `category_id` | INTEGER | FK, NOT NULL | Referencia a categoría |
| `name` | VARCHAR(200) | NOT NULL | Nombre del producto |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | Slug único para URLs |
| `description` | VARCHAR(500) | NOT NULL | Descripción corta |
| `long_description` | TEXT | NULL | Descripción detallada (HTML permitido) |
| `item_type` | VARCHAR(50) | NOT NULL | Tipo de item (narrative, digital, consumable, cosmetic) |
| `rarity` | VARCHAR(20) | DEFAULT "common" | Rareza del item (common, uncommon, etc.) |
| `price_besitos` | INTEGER | NOT NULL | Precio en besitos |
| `icon` | VARCHAR(10) | DEFAULT "📦" | Icono del producto |
| `image_file_id` | VARCHAR(200) | NULL | ID de archivo de imagen en Telegram |
| `metadata` | TEXT | NULL | JSON con datos específicos del tipo |
| `stock` | INTEGER | NULL | Cantidad disponible (NULL = ilimitado) |
| `max_per_user` | INTEGER | NULL | Máximo por usuario (NULL = ilimitado) |
| `requires_vip` | BOOLEAN | DEFAULT FALSE | Si requiere suscripción VIP |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Si está destacado |
| `is_active` | BOOLEAN | DEFAULT TRUE | Si está disponible |
| `order` | INTEGER | DEFAULT 0 | Orden de visualización |
| `created_by` | BIGINT | NOT NULL | ID del admin que creó |
| `created_at` | DATETIME | NOT NULL | Fecha de creación |
| `updated_at` | DATETIME | NOT NULL | Fecha de última actualización |

### Índices

```sql
-- Búsqueda rápida por categoría
CREATE INDEX idx_shop_item_category ON shop_items(category_id);

-- Búsqueda por tipo de item
CREATE INDEX idx_shop_item_type ON shop_items(item_type);

-- Filtrar items activos
CREATE INDEX idx_shop_item_active ON shop_items(is_active);

-- Filtrar items destacados
CREATE INDEX idx_shop_item_featured ON shop_items(is_featured);

-- Búsqueda ordenada por precio
CREATE INDEX idx_shop_item_price ON shop_items(price_besitos);

-- Búsqueda ordenada por orden de visualización
CREATE INDEX idx_shop_item_order ON shop_items(order);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "category_id": 1,
    "name": "Mapa Secreto",
    "slug": "mapa-secreto",
    "description": "Revela ubicación oculta en el capítulo 3",
    "long_description": "Un mapa antiguo que muestra un camino escondido...",
    "item_type": "narrative",
    "rarity": "rare",
    "price_besitos": 200,
    "icon": "🗺️",
    "image_file_id": "AgACAgQ...",
    "metadata": "{\"unlocks_fragment_key\": \"chapter3_secret_path\", \"requires_chapter\": 2}",
    "stock": 50,
    "max_per_user": 1,
    "requires_vip": true,
    "is_featured": true,
    "is_active": true,
    "order": 1,
    "created_by": 123456789,
    "created_at": "2025-12-27T10:30:45.123456",
    "updated_at": "2025-12-27T11:45:20.789012"
}
```

### Operaciones Comunes

```python
from bot.shop.database.models import ShopItem
from sqlalchemy import select, func

# Crear producto
async with get_session() as session:
    item = ShopItem(
        category_id=1,
        name="Avatar Dorado",
        slug="avatar-dorado",
        description="Icono dorado para tu perfil",
        item_type="cosmetic",
        price_besitos=150,
        icon="👑",
        stock=100,
        max_per_user=1,
        requires_vip=True,
        metadata='{"effect": "glow_avatar", "duration_days": 30}'
    )
    session.add(item)
    await session.commit()

# Buscar productos por categoría
async with get_session() as session:
    query = select(ShopItem).where(
        (ShopItem.category_id == 1) &
        (ShopItem.is_active == True)
    ).order_by(ShopItem.order, ShopItem.name)
    result = await session.execute(query)
    items = result.scalars().all()

# Buscar productos en stock
async with get_session() as session:
    query = select(ShopItem).where(
        ShopItem.stock > 0  # Con stock disponible
    )
    result = await session.execute(query)
    available_items = result.scalars().all()

# Buscar productos por rango de precio
async with get_session() as session:
    query = select(ShopItem).where(
        (ShopItem.price_besitos >= 50) &
        (ShopItem.price_besitos <= 500)
    ).order_by(ShopItem.price_besitos)
    result = await session.execute(query)
    affordable_items = result.scalars().all()
```

## Modelo 3: UserInventory

**Descripción:** Inventario personal del usuario que almacena estadísticas generales y preferencias.

**Tabla:** `user_inventories`

### Estructura

```python
class UserInventory(Base):
    __tablename__ = "user_inventories"

    # Identificador de usuario (relación 1:1 con users)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    
    # Estadísticas del inventario
    total_items: Mapped[int] = mapped_column(Integer, default=0)  # Tipos de items diferentes
    total_spent: Mapped[int] = mapped_column(Integer, default=0)  # Besitos gastados
    
    # Preferencias
    favorite_item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadatos
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relaciones
    items: Mapped[List["UserInventoryItem"]] = relationship(
        "UserInventoryItem",
        back_populates="inventory",
        cascade="all, delete-orphan"
    )
    favorite_item: Mapped[Optional["ShopItem"]] = relationship(
        "ShopItem",
        foreign_keys=[favorite_item_id]
    )

    # Índices
    __table_args__ = (
        Index("idx_inventory_user_stats", "user_id", "total_items"),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `user_id` | BIGINT | PK, FK | ID del usuario (referencia a tabla users) |
| `total_items` | INTEGER | DEFAULT 0 | Total de tipos de items diferentes poseídos |
| `total_spent` | INTEGER | DEFAULT 0 | Total de besitos gastados en la tienda |
| `favorite_item_id` | INTEGER | FK, NULL | Item favorito del usuario (NULL si no tiene) |
| `created_at` | DATETIME | NOT NULL | Fecha de creación del inventario |
| `updated_at` | DATETIME | NOT NULL | Fecha de última actualización |

### Índices

```sql
-- Búsqueda por usuario y estadísticas
CREATE INDEX idx_inventory_user_stats ON user_inventories(user_id, total_items);
```

### Ejemplo de Dato

```json
{
    "user_id": 123456789,
    "total_items": 5,
    "total_spent": 1200,
    "favorite_item_id": 3,
    "created_at": "2025-12-27T09:15:30.123456",
    "updated_at": "2025-12-27T15:45:20.789012"
}
```

### Operaciones Comunes

```python
from bot.shop.database.models import UserInventory
from sqlalchemy import select, func

# Crear inventario (automático al primer item)
async with get_session() as session:
    inventory = UserInventory(
        user_id=123456789,
        total_items=0,
        total_spent=0
    )
    session.add(inventory)
    await session.commit()

# Obtener inventario de usuario
async with get_session() as session:
    inventory = await session.get(UserInventory, 123456789)
    if not inventory:
        # Crear inventario vacío si no existe
        inventory = UserInventory(user_id=123456789)
        session.add(inventory)
        await session.commit()

# Actualizar estadísticas al comprar
async with get_session() as session:
    inventory = await session.get(UserInventory, 123456789)
    if inventory:
        inventory.total_spent += 200  # Precio del item comprado
        inventory.total_items += 1    # Nuevo tipo de item
        await session.commit()

# Ver usuarios con inventario grande
async with get_session() as session:
    query = select(UserInventory).where(
        UserInventory.total_items >= 10  # 10+ tipos de items
    ).order_by(UserInventory.total_spent.desc())
    result = await session.execute(query)
    rich_collectors = result.scalars().all()
```

## Modelo 4: UserInventoryItem

**Descripción:** Item específico poseído por un usuario, con cantidad y estado.

**Tabla:** `user_inventory_items`

### Estructura

```python
class UserInventoryItem(Base):
    __tablename__ = "user_inventory_items"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relación con usuario e inventario
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_inventories.user_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relación con el item de la tienda
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Cantidad poseída
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Metadatos del item
    obtained_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    obtained_via: Mapped[str] = mapped_column(String(50), default="purchase")
    
    # Estado del item (especial para cosméticos/consumibles)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    inventory: Mapped["UserInventory"] = relationship(
        "UserInventory",
        back_populates="items"
    )
    item: Mapped["ShopItem"] = relationship(
        "ShopItem",
        back_populates="inventory_items"
    )

    # Índices
    __table_args__ = (
        Index("idx_inventory_user_item", "user_id", "item_id"),
        Index("idx_inventory_item", "item_id"),
        Index("idx_inventory_equipped", "user_id", "is_equipped"),
        Index("idx_inventory_used", "user_id", "is_used"),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK | ID único del registro |
| `user_id` | BIGINT | FK, NOT NULL | ID del usuario poseedor |
| `item_id` | INTEGER | FK, NOT NULL | ID del item de la tienda |
| `quantity` | INTEGER | DEFAULT 1 | Cantidad poseída |
| `obtained_at` | DATETIME | NOT NULL | Fecha de obtención |
| `obtained_via` | VARCHAR(50) | DEFAULT "purchase" | Cómo se obtuvo (purchase, gift, reward) |
| `is_equipped` | BOOLEAN | DEFAULT FALSE | Si el item está equipado |
| `is_used` | BOOLEAN | DEFAULT FALSE | Si el item ha sido usado |
| `used_at` | DATETIME | NULL | Fecha de uso (para consumibles) |

### Índices

```sql
-- Búsqueda rápida por usuario y item
CREATE INDEX idx_inventory_user_item ON user_inventory_items(user_id, item_id);

-- Búsqueda por item (para estadísticas)
CREATE INDEX idx_inventory_item ON user_inventory_items(item_id);

-- Filtrar items equipados por usuario
CREATE INDEX idx_inventory_equipped ON user_inventory_items(user_id, is_equipped);

-- Filtrar items usados por usuario
CREATE INDEX idx_inventory_used ON user_inventory_items(user_id, is_used);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "user_id": 123456789,
    "item_id": 3,
    "quantity": 2,
    "obtained_at": "2025-12-27T12:30:45.123456",
    "obtained_via": "purchase",
    "is_equipped": false,
    "is_used": false,
    "used_at": null
}
```

### Operaciones Comunes

```python
from bot.shop.database.models import UserInventoryItem
from sqlalchemy import select, func

# Agregar item al inventario
async with get_session() as session:
    inventory_item = UserInventoryItem(
        user_id=123456789,
        item_id=5,  # ID del item comprado
        quantity=1,
        obtained_via="purchase",
        is_equipped=False
    )
    session.add(inventory_item)
    await session.commit()

# Incrementar cantidad de item existente
async with get_session() as session:
    # Buscar item existente
    query = select(UserInventoryItem).where(
        (UserInventoryItem.user_id == 123456789) &
        (UserInventoryItem.item_id == 5)
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Incrementar cantidad
        existing.quantity += 1
    else:
        # Crear nuevo registro
        new_item = UserInventoryItem(
            user_id=123456789,
            item_id=5,
            quantity=1,
            obtained_via="gift"
        )
        session.add(new_item)
    
    await session.commit()

# Buscar items de un usuario por tipo
async with get_session() as session:
    query = select(UserInventoryItem).join(
        ShopItem, UserInventoryItem.item_id == ShopItem.id
    ).where(
        (UserInventoryItem.user_id == 123456789) &
        (ShopItem.item_type == "consumable")
    )
    result = await session.execute(query)
    consumables = result.scalars().all()

# Buscar items equipados
async with get_session() as session:
    query = select(UserInventoryItem).where(
        (UserInventoryItem.user_id == 123456789) &
        (UserInventoryItem.is_equipped == True)
    )
    result = await session.execute(query)
    equipped_items = result.scalars().all()

# Actualizar estado al usar item
async with get_session() as session:
    query = select(UserInventoryItem).where(
        (UserInventoryItem.user_id == 123456789) &
        (UserInventoryItem.item_id == 5) &
        (UserInventoryItem.quantity > 0)
    )
    result = await session.execute(query)
    item = result.scalar_one_or_none()
    
    if item and item.quantity > 0:
        item.quantity -= 1
        item.is_used = True
        item.used_at = datetime.now(UTC)
        await session.commit()
```

## Modelo 5: ItemPurchase

**Descripción:** Registro de compra de un item por parte de un usuario, para estadísticas y auditoría.

**Tabla:** `shop_item_purchases`

### Estructura

```python
class ItemPurchase(Base):
    __tablename__ = "shop_item_purchases"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Relación con usuario (almacenada como BIGINT para eficiencia)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Relación con item comprado
    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shop_items.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Cantidad comprada
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    # Precio pagado (puede diferir del precio actual del item)
    price_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Estado de la compra
    status: Mapped[str] = mapped_column(String(20), default="completed")
    
    # Timestamps
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Notas adicionales
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relación con el item (para consultas)
    item: Mapped["ShopItem"] = relationship(
        "ShopItem",
        back_populates="purchases"
    )

    # Índices
    __table_args__ = (
        Index("idx_purchase_user", "user_id"),
        Index("idx_purchase_item", "item_id"),
        Index("idx_purchase_date", "purchased_at"),
        Index("idx_purchase_status", "status"),
        Index("idx_purchase_user_date", "user_id", "purchased_at"),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK | ID único de la compra |
| `user_id` | BIGINT | NOT NULL | ID del usuario que compró (almacenado directamente) |
| `item_id` | INTEGER | FK, NOT NULL | ID del item comprado |
| `quantity` | INTEGER | DEFAULT 1 | Cantidad comprada |
| `price_paid` | INTEGER | NOT NULL | Precio que pagó el usuario (puede diferir del precio actual) |
| `status` | VARCHAR(20) | DEFAULT "completed" | Estado de la compra (completed, refunded, cancelled) |
| `purchased_at` | DATETIME | NOT NULL | Fecha de la compra |
| `refunded_at` | DATETIME | NULL | Fecha de reembolso (si aplica) |
| `notes` | VARCHAR(500) | NULL | Notas adicionales sobre la compra |

### Índices

```sql
-- Búsqueda por usuario
CREATE INDEX idx_purchase_user ON shop_item_purchases(user_id);

-- Búsqueda por item
CREATE INDEX idx_purchase_item ON shop_item_purchases(item_id);

-- Búsqueda por fecha
CREATE INDEX idx_purchase_date ON shop_item_purchases(purchased_at);

-- Filtrar por estado
CREATE INDEX idx_purchase_status ON shop_item_purchases(status);

-- Búsqueda combinada usuario y fecha (para historial)
CREATE INDEX idx_purchase_user_date ON shop_item_purchases(user_id, purchased_at);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "user_id": 123456789,
    "item_id": 3,
    "quantity": 1,
    "price_paid": 200,
    "status": "completed",
    "purchased_at": "2025-12-27T14:20:30.123456",
    "refunded_at": null,
    "notes": null
}
```

### Operaciones Comunes

```python
from bot.shop.database.models import ItemPurchase
from sqlalchemy import select, func
from bot.shop.database.enums import PurchaseStatus

# Registrar compra
async with get_session() as session:
    purchase = ItemPurchase(
        user_id=123456789,
        item_id=5,
        quantity=1,
        price_paid=200,
        status=PurchaseStatus.COMPLETED.value
    )
    session.add(purchase)
    await session.commit()

# Buscar historial de compras de usuario
async with get_session() as session:
    query = select(ItemPurchase).join(
        ShopItem, ItemPurchase.item_id == ShopItem.id
    ).where(
        ItemPurchase.user_id == 123456789
    ).order_by(ItemPurchase.purchased_at.desc()).limit(10)
    result = await session.execute(query)
    history = result.scalars().all()

# Buscar compras exitosas de un item específico
async with get_session() as session:
    query = select(ItemPurchase).where(
        (ItemPurchase.item_id == 5) &
        (ItemPurchase.status == PurchaseStatus.COMPLETED.value)
    )
    result = await session.execute(query)
    successful_purchases = result.scalars().all()

# Calcular ingresos por item
async with get_session() as session:
    query = select(
        func.sum(ItemPurchase.price_paid).label('total_revenue'),
        func.count(ItemPurchase.id).label('total_sales')
    ).where(
        (ItemPurchase.item_id == 5) &
        (ItemPurchase.status == PurchaseStatus.COMPLETED.value)
    )
    result = await session.execute(query)
    revenue, sales = result.one()

# Buscar compras recientes para estadísticas
from datetime import datetime, timedelta
async with get_session() as session:
    week_ago = datetime.now(UTC) - timedelta(days=7)
    query = select(ItemPurchase).where(
        ItemPurchase.purchased_at >= week_ago
    )
    result = await session.execute(query)
    recent_purchases = result.scalars().all()
```

## Relaciones Entre Modelos

### Diagrama de Relaciones

```
ItemCategory (1) 
    ├─ Contiene muchos (M) ShopItem
    └─ Relación 1:M con ShopItem

ShopItem (M)
    ├─ Puede pertenecer a (1) ItemCategory (relación M:1)
    ├─ Genera muchos (M) UserInventoryItem (relación M:1 inversa)
    └─ Tiene muchos (M) ItemPurchase (relación M:1 inversa)

UserInventory (1)
    ├─ Pertenece a (1) Usuario (relación 1:1 con users.user_id)
    ├─ Tiene muchos (M) UserInventoryItem (relación 1:M)
    └─ Puede tener (0-1) ShopItem como favorito (relación 1:1 con ShopItem)

UserInventoryItem (M)
    ├─ Perteneciente a (1) UserInventory (relación M:1)
    └─ Representa (1) ShopItem (relación M:1)

ItemPurchase (M)
    ├─ Registro de compra por (1) Usuario (almacenado como biginteger)
    └─ Referencia a (1) ShopItem (relación M:1)
```

### Relaciones en Código

```python
# Category - Items (1:M)
category.items  # Todos los items en esta categoría
item.category   # Categoría a la que pertenece el item

# Item - Inventory Items (1:M)
item.inventory_items  # Todos los registros de posesión por usuarios
inventory_item.item   # Item específico al que se refiere el registro

# Item - Purchases (1:M)
item.purchases        # Todas las compras de este item
purchase.item         # Item específico en la compra

# User - Inventory (1:1)
user.inventory        # Inventario del usuario
inventory.user_id     # ID del usuario al que pertenece

# Inventory - Inventory Items (1:M)
inventory.items       # Todos los items del usuario
inventory_item.inventory  # Inventario al que pertenece el item
```

## Índices y Optimización

### Índices Primarios

1. **ItemCategory:**
   - `idx_shop_category_order(category_order)` - Para ordenar categorías
   - `idx_shop_category_active(is_active)` - Para filtrar categorías activas

2. **ShopItem:**
   - `idx_shop_item_category(category_id)` - Búsqueda rápida por categoría
   - `idx_shop_item_type(item_type)` - Filtrar por tipo de item
   - `idx_shop_item_active(is_active)` - Filtrar items disponibles
   - `idx_shop_item_featured(is_featured)` - Filtrar items destacados
   - `idx_shop_item_price(price_besitos)` - Búsqueda por rango de precios
   - `idx_shop_item_order(order)` - Ordenar items

3. **UserInventory:**
   - `idx_inventory_user_stats(user_id, total_items)` - Estadísticas por usuario

4. **UserInventoryItem:**
   - `idx_inventory_user_item(user_id, item_id)` - Búsqueda rápida de posesión
   - `idx_inventory_item(item_id)` - Consultas estadísticas por item
   - `idx_inventory_equipped(user_id, is_equipped)` - Filtrar equipados
   - `idx_inventory_used(user_id, is_used)` - Filtrar usados

5. **ItemPurchase:**
   - `idx_purchase_user(user_id)` - Historial por usuario
   - `idx_purchase_item(item_id)` - Estadísticas por item
   - `idx_purchase_date(purchased_at)` - Consultas cronológicas
   - `idx_purchase_status(status)` - Filtrar por estado
   - `idx_purchase_user_date(user_id, purchased_at)` - Historial cronológico

### Consultas Optimizadas

```python
# BUENO: Usa índices
from sqlalchemy import select, desc

# Buscar items por categoría (usa idx_shop_item_category)
query = select(ShopItem).where(
    ShopItem.category_id == 1
).order_by(ShopItem.order)

# Buscar posesiones por usuario (usa idx_inventory_user_item)
query = select(UserInventoryItem).where(
    UserInventoryItem.user_id == 123456789
)

# Buscar historial de compras (usa idx_purchase_user_date)
query = select(ItemPurchase).where(
    ItemPurchase.user_id == 123456789
).order_by(desc(ItemPurchase.purchased_at))

# MALO: No usa índice eficientemente
query = select(ShopItem).order_by(ShopItem.stock)  # Sin índice en stock

# BUENO: Carga relaciones eficientemente
from sqlalchemy.orm import selectinload

query = select(ItemCategory).options(
    selectinload(ItemCategory.items)
).where(ItemCategory.is_active == True)

# MALO: N+1 query problem
categories = query.execute().scalars().all()
for category in categories:
    print(category.items)  # N nuevas queries (una por categoría)
```

## Seguridad y Validaciones

### Restricciones de Integridad

- **ON DELETE CASCADE**: Elimina items relacionados al eliminar categoría
- **ON DELETE CASCADE**: Elimina registros de inventario al eliminar item
- **UNIQUE CONSTRAINTS**: Impiden slugs duplicados en categorías/items
- **NOT NULL CONSTRAINTS**: Garantizan datos mínimos requeridos

### Validaciones a Nivel de Base de Datos

1. **Restricciones Check** (si se implementan):
   - Stock no negativo
   - Precios positivos
   - Cantidad por usuario >= 1

2. **Restricciones de Integridad Referencial**:
   - Solo categorías válidas
   - Solo items existentes
   - Solo usuarios existentes

### Auditoría y Seguimiento

1. **Historial de Compras**: Todos los ItemPurchase se mantienen para estadísticas
2. **Cambios de Precio**: Se registra price_paid para mantener historial
3. **Timestamps**: Todos los modelos tienen created_at/updated_at

---

**Última actualización:** 2025-12-27  
**Versión:** 1.0.0
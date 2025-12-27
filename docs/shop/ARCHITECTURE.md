# Arquitectura del Módulo de Tienda y Mochila

## 🏗️ Visión General

La arquitectura del módulo de tienda y mochila sigue los principios de separación de responsabilidades y sigue un patrón de 4 capas con inyección de dependencias. El módulo permite a los usuarios comprar productos con besitos, almacenarlos en un inventario personal (mochila) y usarlos para mejorar su experiencia.

## 🎯 Objetivos de la Arquitectura

1. **Separación de Responsabilidades:** Cada componente tiene una única responsabilidad claramente definida
2. **Escalabilidad:** Facilidad para añadir nuevos tipos de items y funcionalidades
3. **Seguridad:** Validaciones robustas para prevenir fraudes y exploits
4. **Integración:** Conexión fluida con sistemas de gamificación y narrativa
5. **Flexibilidad:** Configuración dinámica de productos y categorías

## 🔬 Estructura de Capas

### Capa 1: Base de Datos
- **Tecnología:** SQLAlchemy 2.0 (async ORM)
- **Características:**
  - 5 modelos principales relacionados
  - Índices optimizados para consultas comunes
  - Relaciones definidas con lazy/eager loading adecuado
  - Control de integridad referencial
  - Timestamps de auditoría

### Capa 2: Servicios (Lógica de Negocio)
- **Patrón:** Inyección de dependencias con lazy loading
- **Componentes:**
  - `ShopService` - Gestión de productos, categorías y compras
  - `InventoryService` - Gestión de inventario personal
  - `ShopContainer` - Contenedor con inyección de dependencias
- **Características:**
  - Operaciones CRUD completas
  - Validaciones de negocio
  - Transacciones atómicas
  - Control de concurrencia
  - Caching opcional para operaciones frecuentes

### Capa 3: Handlers (Interfaz con Telegram)
- **Framework:** Aiogram 3.4.1 (async handlers)
- **Características:**
  - Separación entre handlers de usuario y administrador
  - Estado FSM para flujos de configuración
  - Validación de permisos
  - Inyección de sesiones de BD
  - Parseo de comandos y callbacks
  - Teclados dinámicos según rol

### Capa 4: Utils (Ayudas)
- **Componentes:**
  - Construcción de teclados inline
  - Formateo de mensajes
  - Validación de inputs
  - Manejo de errores

## 🔄 Flujo de Datos

### Flujo de Compra de Producto
```
Usuario → Handler → Container → ShopService → Base de Datos
   ↓                                             ↓
   ← Botón ← Keyboard ← Validación ← Transacción ←
```

1. Usuario selecciona producto
2. Handler recibe callback
3. Container inyecta servicios
4. Validación de saldo y stock
5. Procesamiento de compra
6. Actualización de BD
7. Confirmación al usuario

### Flujo de Uso de Item
```
Usuario → Handler → Container → InventoryService → Base de Datos
   ↓                                              ↓
   ← Botón ← Keyboard ← Efecto ← Actualización ←
```

## 🔗 Integraciones

### Con Gamificación
- Sistema de besitos como moneda de compra
- Integración con BesitoService para deducciones
- Bonificaciones por posesión de items raros

### Con Narrativa
- Items narrativos que desbloquean contenido
- Integración con sistema de capítulos y fragmentos
- Condiciones de desbloqueo basadas en posesión de items

### Con Usuarios
- Sistema basado en roles (VIP, FREE)
- Control de acceso a productos VIP
- Estadísticas individuales por usuario

## 🛡️ Seguridad y Validaciones

### Control de Acceso
- Validación de roles en cada acción
- Verificación de autorización
- Control de límites por usuario
- Prevención de duplicados

### Prevención de Fraudes
- Sistema de cooldown entre compras
- Validación de stock en tiempo real
- Control de límites de cantidad
- Registro de actividades sospechosas

## 📊 Patrones de Diseño Implementados

### Inyección de Dependencias
- `ShopContainer` con lazy loading
- Servicios singleton con ciclo de vida gestionado
- Interfaces claras entre componentes

### Repositorio
- Métodos CRUD abstractos en servicios
- Consultas optimizadas con eager loading
- Caché opcional para operaciones frecuentes

### Estratégia de Consulta
- Uso de `selectinload` y `joinedload` para optimizar consultas
- Índices en campos frecuentemente consultados
- Paginación en listados grandes

## 🚀 Patrones de Implementación

### Patrón de Contenedor de Servicios
```python
class ShopContainer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._shop_service = None
        self._inventory_service = None

    @property
    def shop(self) -> "ShopService":
        if self._shop_service is None:
            self._shop_service = ShopService(self.session)
        return self._shop_service
```

### Patrón de Validación de Compra
```python
async def can_purchase(self, user_id: int, item_id: int) -> Tuple[bool, str]:
    """Valida si un usuario puede comprar un item."""
    # 1. Verificar stock
    # 2. Verificar saldo
    # 3. Verificar límites por usuario
    # 4. Verificar requisitos especiales
    # 5. Devolver (puede_comprar, motivo_si_no)
```

## 🔧 Componentes Configurables

### Categorías Dinámicas
- Categorías personalizables por administradores
- Control de visibilidad y orden
- Asociación flexible con productos

### Productos Personalizables
- Tipos de items configurables
- Rareza variable
- Precio personalizable
- Metadatos flexibles (JSON)

### Configuración Global
- Límites de stock
- Configuración de precios VIP
- Control de acceso
- Sistema de reembolsos

## 📈 Escalabilidad y Rendimiento

### Optimizaciones Realizadas
- Índices en campos de búsqueda frecuente
- Caching de operaciones comunes
- Consultas optimizadas con joins
- Lazy loading de relaciones pesadas

### Consideraciones para Escalabilidad
- Sistema diseñado para soportar múltiples tiendas
- Separación de concernencias para fácil expansión
- Patrón de eventos para operaciones asíncronas
- Posibilidad de integración con Redis para caching

## 🔄 Integridad de Datos

### Transacciones Atómicas
- Compras completas en transacciones únicas
- Rollbacks automáticos en errores
- Control de concurrencia
- Validaciones de integridad referencial

### Auditoría
- Registro de compras completas
- Tracking de posesión de items
- Historial de movimientos
- Validaciones de consistencia

---

**Última actualización:** 2025-12-27  
**Versión:** 1.0.0
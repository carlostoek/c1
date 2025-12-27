# Módulo de Tienda y Mochila - Sistema de Inventario y Compras

## 📋 Descripción General

El módulo de Tienda y Mochila es un sistema integral que permite a los usuarios:
- Comprar productos con besitos
- Almacenar items en su inventario personal (Mochila)
- Usar items consumibles
- Equipar cosméticos
- Desbloquear contenido narrativo
- Seguir historial de compras

## 🎯 Características Principales

- **Catálogo de productos** - Organizados por categorías con descripciones y precios
- **Sistema de compras** - Compra segura con deducción automática de besitos
- **Inventario personal** - Sistema de mochila donde los usuarios guardan sus items
- **Items consumibles** - Productos que pueden usarse para obtener efectos
- **Items cosméticos** - Items que pueden equiparse para personalizar la experiencia
- **Items narrativos** - Items que desbloquean contenido en la historia
- **Control de stock** - Gestión de disponibilidad de productos
- **Histórico de transacciones** - Registro de todas las compras realizadas
- **Integración con gamificación** - Items afectan sistema de besitos, misiones y niveles
- **Integración con narrativa** - Items pueden desbloquear contenido narrativo

## 🏗️ Arquitectura del Módulo

```
bot/shop/
├── __init__.py                 # Inicialización del módulo
├── database/                   # Modelos de base de datos
│   ├── __init__.py
│   ├── enums.py                # Enumeraciones (ItemType, ItemRarity, etc.)
│   └── models.py               # Modelos ORM (categorias, items, inventario)
├── services/                   # Lógica de negocio
│   ├── __init__.py
│   ├── container.py            # Contenedor de inyección de dependencias
│   ├── shop.py                 # Servicio de gestión de la tienda
│   └── inventory.py            # Servicio de gestión del inventario
├── handlers/                   # Handlers de comandos y callbacks
│   ├── __init__.py
│   ├── admin/                  # Gestión de productos (admin)
│   └── user/                   # Interfaz de usuario (tienda e inventario)
├── states/                     # Estados FSM para configuración
└── utils/                      # Utilidades auxiliares
```

## 📊 Componentes Principales

### Tipos de Items (`ItemType`)
- `NARRATIVE` - Items que desbloquean contenido narrativo
- `DIGITAL` - Contenido digital descargable
- `CONSUMABLE` - Items que pueden usarse para obtener efectos
- `COSMETIC` - Items que pueden equiparse para personalización

### Rarezas de Items (`ItemRarity`)
- `COMMON` - Común ( Blanco)
- `UNCOMMON` - Poco común (Verde)
- `RARE` - Raro (Azul)
- `EPIC` - Épico (Morple)
- `LEGENDARY` - Legendario (Amarillo/Naranja)

### Modelos de Base de Datos

- `ItemCategory` - Categorías de productos
- `ShopItem` - Productos de la tienda
- `UserInventory` - Inventario del usuario
- `UserInventoryItem` - Items poseídos por usuarios
- `ItemPurchase` - Historial de compras

## 🛠️ Servicios del Módulo

### ShopService
Gestión de la tienda con operaciones CRUD para categorías y productos, validación de compras, procesamiento de transacciones y estadísticas de ventas.

### InventoryService
Gestión del inventario personal con operaciones CRUD para items poseídos, verificación de posesión, uso de consumibles y equipado de cosméticos.

## 🔄 Flujos de Usuario

### Flujo de Compra
1. Usuario navega `/tienda` y selecciona categoría
2. Usuario selecciona producto y verifica precio
3. Usuario confirma compra y se deducen besitos
4. Producto se agrega a la mochila

### Flujo de Uso de Item
1. Usuario accede a `/mochila` y selecciona categoría
2. Usuario elige item consumible
3. Sistema aplica efecto y decrementa cantidad

### Flujo de Equipo de Cosmético
1. Usuario accede a `/mochila` y selecciona cosméticos
2. Usuario selecciona item y elige equipar
3. Sistema marca como equipado

## 🔧 Integración con Otros Sistemas

- **Gamificación**: Precio en besitos, integración con BesitoService
- **Narrativa**: Items narrativos desbloquean contenido
- **Usuarios**: Sistema basado en usuario con control de acceso

## 📊 Estadísticas y Métricas

- Productos más vendidos
- Usuarios activos en compras
- Conversión por categoría
- Items más poseídos
- Uso de consumibles

---

**Última actualización:** 2025-12-27  
**Versión:** 1.0.0
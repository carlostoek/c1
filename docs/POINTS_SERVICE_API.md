# 💰 PointsService - API Reference

Documentación completa del Servicio de Puntos (Besitos).

## 📋 Índice

1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Uso Básico](#uso-básico)
4. [API Reference](#api-reference)
5. [Ejemplos Avanzados](#ejemplos-avanzados)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El **PointsService** es el servicio central del módulo de gamificación. Gestiona todo lo relacionado con puntos (besitos):

- ✅ Otorgamiento con multiplicadores automáticos
- ✅ Deducción con validación de saldo
- ✅ Histórico completo de transacciones
- ✅ Analytics y estadísticas
- ✅ Integración con sistema de niveles

### Características

- **Transacciones Atómicas**: Todo o nada, sin inconsistencias
- **Multiplicadores Dinámicos**: Nivel + VIP + Eventos
- **Histórico Inmutable**: Auditoría completa
- **Performance Optimizado**: Queries eficientes con índices

---

## 📦 Instalación

El servicio está disponible automáticamente a través del ServiceContainer:

```python
from bot.services.container import ServiceContainer

# En un handler
container = ServiceContainer(session, bot)
points_service = container.points
```

---

## 🚀 Uso Básico

### Otorgar Puntos

```python
# Con multiplicadores (recomendado)
success, new_balance = await container.points.award_points(
    user_id=123456,
    amount=10,
    reason="Reacción a publicación",
    multiplier=1.0,  # Se puede calcular con calculate_multiplier()
    metadata={"action": "reaction", "emoji": "❤️"}
)

if success:
    print(f"Otorgados: {new_balance - (balance_antes - amount)} 💋")
```

### Restar Puntos

```python
# Para canjes de recompensas
success, new_balance = await container.points.deduct_points(
    user_id=123456,
    amount=50,
    reason="Canje de Badge Oro",
    metadata={"reward_id": 5}
)

if success:
    print("Canje exitoso")
else:
    print("Saldo insuficiente")
```

### Consultar Saldo

```python
balance = await container.points.get_user_balance(user_id=123456)
print(f"Saldo: {balance} 💋")
```

---

## 📚 API Reference

### Gestión de Progress

#### `get_or_create_progress(user_id: int)`

Obtiene el UserProgress de un usuario o lo crea si no existe.

**Returns:** `Optional[UserProgress]`

```python
progress = await service.get_or_create_progress(123456)
```

#### `get_user_balance(user_id: int)`

Obtiene el saldo actual de besitos.

**Returns:** `int` (0 si no tiene progress)

```python
balance = await service.get_user_balance(123456)
```

#### `get_user_level(user_id: int)`

Obtiene el nivel actual.

**Returns:** `int` (1 si no tiene progress)

```python
level = await service.get_user_level(123456)
```

#### `update_level(user_id: int, new_level: int)`

Actualiza el nivel. **Llamado por LevelsService**, no directamente.

**Returns:** `bool`

```python
success = await service.update_level(123456, 5)
```

---

### Multiplicadores

#### `calculate_multiplier(user_id: int, is_vip: bool = False)`

Calcula el multiplicador total para un usuario basado en nivel y VIP.

**Returns:** `float`

```python
multiplier = await service.calculate_multiplier(123456, is_vip=True)
# Nivel 3 (1.2x) + VIP (1.5x) = 1.8x
```

#### `get_level_multiplier(level: int)`

Obtiene el multiplicador por nivel (sin async).

**Returns:** `float`

```python
level_mult = service.get_level_multiplier(5)  # 1.4x para nivel 5
```

#### `get_vip_multiplier(is_vip: bool)`

Obtiene el multiplicador por estado VIP (sin async).

**Returns:** `float`

```python
vip_mult = service.get_vip_multiplier(True)  # 1.5x para VIP
```

---

### Otorgamiento y Deducción

#### `award_points(user_id, amount, reason, multiplier=1.0, metadata=None)`

Otorga puntos a un usuario.

**Args:**
- `user_id` (int): ID del usuario
- `amount` (int): Cantidad base de puntos
- `reason` (str): Descripción
- `multiplier` (float): Multiplicador a aplicar (default=1.0)
- `metadata` (dict, optional): Metadata adicional

**Returns:** `Tuple[bool, Optional[int]]` (éxito, nuevo_balance)

```python
success, new_balance = await service.award_points(
    user_id=123456,
    amount=100,
    reason="Completó misión diaria",
    multiplier=1.5,  # Se puede calcular con calculate_multiplier()
    metadata={"mission_id": 5}
)

if success:
    print(f"Nuevo saldo: {new_balance}")
```

#### `deduct_points(user_id, amount, reason, metadata=None)`

Resta puntos (para canjes).

**Args:**
- `user_id` (int): ID del usuario
- `amount` (int): Cantidad a restar
- `reason` (str): Descripción
- `metadata` (dict, optional): Metadata adicional

**Returns:** `Tuple[bool, Optional[int]]` (éxito, nuevo_balance o None si falla)

```python
success, new_balance = await service.deduct_points(
    user_id=123456,
    amount=50,
    reason="Canje de recompensa"
)

if success:
    print("Canje exitoso")
else:
    print("Saldo insuficiente")
```

#### `can_afford(user_id, amount)`

Verifica si un usuario puede pagar una cantidad.

**Returns:** `bool`

```python
if await service.can_afford(123456, 100):
    # Procesar canje
    pass
```

---

### Histórico

#### `get_point_history_by_type(user_id, limit=10, transaction_type=None)`

Obtiene histórico de transacciones.

**Args:**
- `user_id` (int): ID del usuario
- `limit` (int): Cantidad máxima (default=10)
- `transaction_type` (TransactionType, optional): Filtro por tipo

**Returns:** `List[PointTransaction]`

```python
from bot.database.models import TransactionType

history = await service.get_point_history_by_type(123456, limit=20)
for tx in history:
    print(f"{tx.created_at}: {tx.amount} - {tx.reason}")
```

#### `get_earned_history(user_id, limit=10)`

Histórico de puntos ganados.

```python
earned = await service.get_earned_history(123456, limit=10)
```

#### `get_spent_history(user_id, limit=10)`

Histórico de puntos gastados.

```python
spent = await service.get_spent_history(123456, limit=10)
```

#### `get_point_history(user_id, limit=50, offset=0)`

Obtiene el histórico de transacciones de un usuario con más opciones.

**Returns:** `List[Dict]`

```python
history = await service.get_point_history(123456, limit=100, offset=0)
for tx in history:
    print(f"{tx['reason']}: {tx['amount']:+d}")
```

---

### Analytics

#### `get_user_stats(user_id)`

Estadísticas completas de un usuario.

**Returns:** `Optional[Dict]`

```python
stats = await service.get_user_stats(123456)
# {
#     'balance': 150,
#     'level': 3,
#     'total_earned': 500,
#     'total_spent': 350,
#     'net_points': 150,
#     'transaction_count': 25
# }
```

#### `get_total_points_in_system()`

Total de puntos en circulación.

**Returns:** `int`

```python
total = await service.get_total_points_in_system()
```

#### `get_richest_users(limit=10)`

Top usuarios con más puntos.

**Returns:** `List[Tuple[int, int, int]]` (user_id, balance, level)

```python
top = await service.get_richest_users(5)
for user_id, balance, level in top:
    print(f"User {user_id}: {balance} 💋 (Nivel {level})")
```

---

## 🎨 Ejemplos Avanzados

### Ejemplo 1: Handler de Reacción

```python
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram import F

router = Router()

@router.callback_query(F.data.startswith("react:"))
async def handle_reaction(callback: CallbackQuery, session):
    user_id = callback.from_user.id
    
    container = ServiceContainer(session, callback.bot)
    
    # Calcular multiplicador
    user = await container.user.get_user_by_id(user_id)
    is_vip = user.is_vip if user else False
    multiplier = await container.points.calculate_multiplier(user_id, is_vip=is_vip)
    
    # Otorgar puntos con multiplicadores
    success, new_balance = await container.points.award_points(
        user_id=user_id,
        amount=5,
        reason="Reacción a publicación",
        multiplier=multiplier,
        metadata={
            "action": "reaction",
            "emoji": callback.data.split(":")[1],
            "message_id": callback.message.message_id
        }
    )
    
    if success:
        await callback.answer(
            f"✅ +{int(5 * multiplier)} 💋",
            show_alert=False
        )
```

### Ejemplo 2: Sistema de Misiones

```python
async def complete_mission(user_id, mission_id, reward_points, session, bot):
    container = ServiceContainer(session, bot)
    
    # Otorgar puntos de misión (con multiplicadores normales)
    success, new_balance = await container.points.award_points(
        user_id=user_id,
        amount=reward_points,
        reason=f"Misión #{mission_id} completada",
        multiplier=1.0,  # Multiplicador predeterminado
        metadata={"mission_id": mission_id}
    )
    
    if success:
        # Verificar si subió de nivel
        stats = await container.points.get_user_stats(user_id)
        # ... lógica de level-up ...
        return True, f"Misión completada! +{reward_points} 💋"
    
    return False, "Error al otorgar recompensa"
```

### Ejemplo 3: Canje de Recompensa

```python
async def redeem_reward(user_id, reward_id, cost, session, bot):
    container = ServiceContainer(session, bot)
    
    # Verificar saldo
    if not await container.points.can_afford(user_id, cost):
        return False, "Saldo insuficiente"
    
    # Restar puntos
    success, new_balance = await container.points.deduct_points(
        user_id=user_id,
        amount=cost,
        reason=f"Canje de recompensa #{reward_id}",
        metadata={"reward_id": reward_id}
    )
    
    if success:
        # Entregar recompensa (ej: enviar mensaje, badge, etc.)
        await bot.send_message(
            user_id, 
            f"🎁 ¡Recompensa canjeada exitosamente! Nuevo saldo: {new_balance} 💋"
        )
        return True, "Canje exitoso"
    
    return False, "Error en canje"
```

---

## 🔧 Troubleshooting

### Usuario no tiene progress

**Solución:** Usar `get_or_create_progress()` en lugar de `get_user_progress()`

```python
# ❌ Puede retornar None
progress = await service.get_user_progress(user_id)

# ✅ Crea si no existe
progress = await service.get_or_create_progress(user_id)
```

### Saldo insuficiente

**Solución:** Verificar con `can_afford()` antes de restar

```python
if await service.can_afford(user_id, cost):
    success, new_balance = await service.deduct_points(user_id, cost, reason)
    if success:
        # Procesar canje
        pass
else:
    # Manejar error
    pass
```

### Multiplicadores no se aplican correctamente

**Verificar:** Calcular multiplicador explícitamente

```python
# Multiplicador basado en nivel y VIP
multiplier = await service.calculate_multiplier(user_id, is_vip=True)

# Aplicar manualmente
success, balance = await service.award_points(
    user_id=user_id,
    amount=10,
    reason="Test",
    multiplier=multiplier
)
```

### Método award_points o deduct_points devuelve False

**Causas comunes:**
- Usuario no existe o no tiene progress
- Problemas de base de datos
- Saldo insuficiente en deducción
- Parámetros incorrectos

```python
success, new_balance = await service.award_points(user_id, 10, "Test", 1.0)
if not success:
    print(f"Error: No se pudo otorgar puntos. Balance: {new_balance}")
```

---

## 📊 Mejores Prácticas

1. **Siempre usar ServiceContainer**
   ```python
   # ✅ Correcto
   container = ServiceContainer(session, bot)
   success, balance = await container.points.award_points(...)
   
   # ❌ Evitar
   service = PointsService(session, bot)
   ```

2. **Metadata descriptivo**
   ```python
   metadata = {
       "action": "reaction",
       "emoji": "❤️",
       "message_id": 12345,
       "channel_id": -1001234567890
   }
   ```

3. **Verificar retornos**
   ```python
   success, new_balance = await service.deduct_points(...)
   if not success:
       # Manejar error (saldo insuficiente)
       pass
   ```

4. **Calcular multiplicadores correctamente**
   ```python
   # Basado en datos reales del usuario
   user = await container.user.get_user_by_id(user_id)
   multiplier = await service.calculate_multiplier(user_id, is_vip=user.is_vip)
   ```

---

**💡 ¿Dudas?** Consulta los tests en `tests/test_points_service_complete.py` para más ejemplos.
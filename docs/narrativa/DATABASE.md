# Documentación de Base de Datos - Módulo Narrativo

## 📋 Resumen de Modelos

El módulo narrativo utiliza 6 modelos principales en SQLAlchemy 2.0 con soporte para relaciones y optimización de consultas:

| Modelo | Propósito | Registros por capítulo (estimado) |
|--------|----------|----------------------------------|
| `NarrativeChapter` | Capítulos narrativos | 1-100 |
| `NarrativeFragment` | Fragmentos dentro de capítulos | 1-50 |
| `FragmentDecision` | Opciones de decisión en fragmentos | 1-10 |
| `FragmentRequirement` | Requisitos para acceso a fragmentos | 0-5 |
| `UserNarrativeProgress` | Progreso individual de usuarios | 1 por usuario activo |
| `UserDecisionHistory` | Historial de decisiones | Variable (1-1000+) |

## Modelo 1: NarrativeChapter

**Descripción:** Capítulo narrativo que agrupa fragmentos relacionados.

**Tabla:** `narrative_chapters`

### Estructura

```python
class NarrativeChapter(Base):
    __tablename__ = "narrative_chapters"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Información básica
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    chapter_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ChapterType
    
    # Orden y estado
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Requisitos para acceder al capítulo
    requirements: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # Relaciones
    fragments: Mapped[List["NarrativeFragment"]] = relationship(
        "NarrativeFragment", 
        back_populates="chapter",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index('idx_chapter_order', 'order'),
        Index('idx_chapter_type', 'chapter_type'),
        Index('idx_chapter_active', 'active'),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único del capítulo |
| `title` | VARCHAR(200) | NOT NULL | Título del capítulo |
| `description` | TEXT | NULL | Descripción breve del capítulo |
| `chapter_type` | VARCHAR(50) | NOT NULL | Tipo del capítulo (INTRO, MAIN, CLIMAX, etc.) |
| `order` | INTEGER | NOT NULL | Orden de presentación |
| `active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Indica si capítulo está disponible |
| `requirements` | JSON | NULL | Requisitos necesarios para acceder |
| `created_at` | DATETIME | NOT NULL | Timestamp de creación |
| `updated_at` | DATETIME | NOT NULL | Timestamp de última actualización |

### Índices

```sql
-- Búsqueda por orden
CREATE INDEX idx_chapter_order ON narrative_chapters(order);

-- Búsqueda por tipo
CREATE INDEX idx_chapter_type ON narrative_chapters(chapter_type);

-- Filtrar capítulos activos
CREATE INDEX idx_chapter_active ON narrative_chapters(active);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "title": "Introducción",
    "description": "Capítulo introductorio de la historia",
    "chapter_type": "INTRO",
    "order": 1,
    "active": true,
    "requirements": [
        {"type": "BESITOS", "amount": 50}
    ],
    "created_at": "2025-12-26T10:00:00.000000",
    "updated_at": "2025-12-26T10:00:00.000000"
}
```

### Operaciones Comunes

```python
# Crear capítulo
chapter = NarrativeChapter(
    title="Capítulo 1",
    description="Descripción del capítulo",
    chapter_type="MAIN",
    order=1,
    requirements={"type": "VIP", "required": True}
)
session.add(chapter)
await session.commit()

# Buscar capítulo por tipo
from sqlalchemy import select
query = select(NarrativeChapter).where(NarrativeChapter.chapter_type == "INTRO")
result = await session.execute(query)
intro_chapters = result.scalars().all()

# Buscar capítulos activos ordenados
query = select(NarrativeChapter).where(NarrativeChapter.active == True).order_by(NarrativeChapter.order)
result = await session.execute(query)
active_chapters = result.scalars().all()
```

## Modelo 2: NarrativeFragment

**Descripción:** Fragmento narrativo dentro de un capítulo con contenido y decisiones.

**Tabla:** `narrative_fragments`

### Estructura

```python
class NarrativeFragment(Base):
    __tablename__ = "narrative_fragments"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Relación con capítulo
    chapter_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("narrative_chapters.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Información del fragmento
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Orden dentro del capítulo
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Requisitos para acceder
    requirements: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # Relaciones
    chapter: Mapped["NarrativeChapter"] = relationship(
        "NarrativeChapter", 
        back_populates="fragments"
    )
    decisions: Mapped[List["FragmentDecision"]] = relationship(
        "FragmentDecision", 
        back_populates="fragment",
        cascade="all, delete-orphan"
    )

    # Índices
    __table_args__ = (
        Index('idx_fragment_chapter_order', 'chapter_id', 'order'),
        Index('idx_fragment_chapter', 'chapter_id'),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único del fragmento |
| `chapter_id` | INTEGER | FK, NOT NULL | Referencia al capítulo padre |
| `title` | VARCHAR(200) | NOT NULL | Título del fragmento |
| `content` | TEXT | NOT NULL | Contenido narrativo |
| `order` | INTEGER | NOT NULL | Orden dentro del capítulo |
| `requirements` | JSON | NULL | Requisitos para acceder al fragmento |
| `created_at` | DATETIME | NOT NULL | Timestamp de creación |
| `updated_at` | DATETIME | NOT NULL | Timestamp de última actualización |

### Índices

```sql
-- Búsqueda rápida por capítulo y orden
CREATE INDEX idx_fragment_chapter_order ON narrative_fragments(chapter_id, order);

-- Búsqueda por capítulo
CREATE INDEX idx_fragment_chapter ON narrative_fragments(chapter_id);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "chapter_id": 1,
    "title": "Encuentro Inicial",
    "content": "Te encuentras en un bosque misterioso...",
    "order": 1,
    "requirements": [
        {"type": "COMPLETED_CHAPTER", "chapter_id": 0}
    ],
    "created_at": "2025-12-26T10:15:00.000000",
    "updated_at": "2025-12-26T10:15:00.000000"
}
```

### Operaciones Comunes

```python
# Crear fragmento
fragment = NarrativeFragment(
    chapter_id=1,
    title="Fragmento Inicial",
    content="Contenido del fragmento...",
    order=1,
    requirements={"type": "VIP", "required": True}
)
session.add(fragment)
await session.commit()

# Buscar fragmentos por capítulo
query = select(NarrativeFragment).where(
    NarrativeFragment.chapter_id == 1
).order_by(NarrativeFragment.order)
result = await session.execute(query)
fragments = result.scalars().all()

# Buscar fragmento por ID con capítulo
query = select(NarrativeFragment).where(NarrativeFragment.id == 5)
result = await session.execute(query)
fragment = result.scalar_one_or_none()
if fragment:
    print(f"Fragmento: {fragment.title} en capítulo {fragment.chapter.title}")
```

## Modelo 3: FragmentDecision

**Descripción:** Opción de decisión disponible en un fragmento que lleva a otro fragmento.

**Tabla:** `fragment_decisions`

### Estructura

```python
class FragmentDecision(Base):
    __tablename__ = "fragment_decisions"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Relación con fragmento original
    fragment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("narrative_fragments.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Texto visible de la decisión
    text: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Fragmento destino (siguiente en la narrativa)
    next_fragment_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("narrative_fragments.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Requisitos para tomar esta decisión
    requirements: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Costo en besitos (opcional)
    besitos_cost: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Orden de presentación
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # Relaciones
    fragment: Mapped["NarrativeFragment"] = relationship(
        "NarrativeFragment", 
        foreign_keys=[fragment_id],
        back_populates="decisions"
    )
    next_fragment: Mapped[Optional["NarrativeFragment"]] = relationship(
        "NarrativeFragment", 
        foreign_keys=[next_fragment_id]
    )

    # Índices
    __table_args__ = (
        Index('idx_decision_fragment', 'fragment_id'),
        Index('idx_decision_order', 'fragment_id', 'order'),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único de la decisión |
| `fragment_id` | INTEGER | FK, NOT NULL | Fragmento donde está disponible la decisión |
| `text` | VARCHAR(200) | NOT NULL | Texto visible de la opción de decisión |
| `next_fragment_id` | INTEGER | FK, NULL | Fragmento destino al tomar decisión |
| `requirements` | JSON | NULL | Requisitos para tomar esta decisión |
| `besitos_cost` | INTEGER | NULL | Costo en besitos (opcional) |
| `order` | INTEGER | DEFAULT 0 | Orden de presentación de la decisión |
| `created_at` | DATETIME | NOT NULL | Timestamp de creación |
| `updated_at` | DATETIME | NOT NULL | Timestamp de última actualización |

### Índices

```sql
-- Búsqueda rápida en fragmento
CREATE INDEX idx_decision_fragment ON fragment_decisions(fragment_id);

-- Orden de decisiones en fragmento
CREATE INDEX idx_decision_order ON fragment_decisions(fragment_id, order);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "fragment_id": 1,
    "text": "Tomar la puerta roja",
    "next_fragment_id": 2,
    "requirements": [
        {"type": "BESITOS", "amount": 10}
    ],
    "besitos_cost": 5,
    "order": 1,
    "created_at": "2025-12-26T10:30:00.000000",
    "updated_at": "2025-12-26T10:30:00.000000"
}
```

### Operaciones Comunes

```python
# Crear decisión
decision = FragmentDecision(
    fragment_id=1,
    text="Tomar la puerta roja",
    next_fragment_id=2,
    requirements={"type": "BESITOS", "amount": 10},
    besitos_cost=5,
    order=1
)
session.add(decision)
await session.commit()

# Buscar decisiones para un fragmento
query = select(FragmentDecision).where(
    FragmentDecision.fragment_id == 1
).order_by(FragmentDecision.order)
result = await session.execute(query)
decisions = result.scalars().all()

# Buscar decisión con siguiente fragmento
query = select(FragmentDecision).where(FragmentDecision.id == 1)
result = await session.execute(query)
decision = result.scalar_one_or_none()
if decision and decision.next_fragment:
    print(f"Siguiente: {decision.next_fragment.title}")
```

## Modelo 4: UserNarrativeProgress

**Descripción:** Progreso individual de un usuario en la narrativa.

**Tabla:** `user_narrative_progress`

### Estructura

```python
class UserNarrativeProgress(Base):
    __tablename__ = "user_narrative_progress"

    # Identificador de usuario (relación con tabla users)
    user_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    # Fragmento actual donde está el usuario
    current_fragment_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("narrative_fragments.id"),
        nullable=True
    )
    
    # Arquetipo detectado del usuario
    current_archetype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Estadísticas
    total_fragments_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_time_spent: Mapped[int] = mapped_column(Integer, default=0)  # en segundos
    chapters_completed: Mapped[List[int]] = mapped_column(JSON, default=list)
    
    # Estado de progreso
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="narrative_progress")
    current_fragment: Mapped[Optional["NarrativeFragment"]] = relationship("NarrativeFragment")

    # Índices
    __table_args__ = (
        Index('idx_user_progress_active', 'user_id', 'active'),
        Index('idx_user_progress_fragment', 'current_fragment_id'),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `user_id` | BIGINT | PK, FK, NOT NULL | ID del usuario |
| `current_fragment_id` | INTEGER | FK, NULL | Fragmento actual del usuario |
| `current_archetype` | VARCHAR(50) | NULL | Arquetipo detectado del usuario |
| `total_fragments_completed` | INTEGER | DEFAULT 0 | Total de fragmentos completados |
| `total_time_spent` | INTEGER | DEFAULT 0 | Tiempo total invertido (en segundos) |
| `chapters_completed` | JSON | DEFAULT [] | IDs de capítulos completados |
| `active` | BOOLEAN | DEFAULT TRUE | Indica si progreso está activo |
| `started_at` | DATETIME | NOT NULL | Timestamp de inicio de narrativa |
| `last_accessed_at` | DATETIME | NOT NULL | Timestamp de último acceso |
| `completed_at` | DATETIME | NULL | Timestamp de completación (si aplica) |

### Índices

```sql
-- Búsqueda por usuario y estado
CREATE INDEX idx_user_progress_active ON user_narrative_progress(user_id, active);

-- Búsqueda por fragmento actual
CREATE INDEX idx_user_progress_fragment ON user_narrative_progress(current_fragment_id);
```

### Ejemplo de Dato

```json
{
    "user_id": 123456789,
    "current_fragment_id": 5,
    "current_archetype": "IMPULSIVE",
    "total_fragments_completed": 3,
    "total_time_spent": 1800,
    "chapters_completed": [1],
    "active": true,
    "started_at": "2025-12-26T09:00:00.000000",
    "last_accessed_at": "2025-12-26T10:30:00.000000",
    "completed_at": null
}
```

### Operaciones Comunes

```python
# Crear registro de progreso
progress = UserNarrativeProgress(
    user_id=123456789,
    current_fragment_id=1,
    current_archetype=None,
    total_fragments_completed=0
)
session.add(progress)
await session.commit()

# Actualizar progreso
progress.current_fragment_id = 2
progress.total_fragments_completed += 1
progress.last_accessed_at = datetime.now(UTC)
await session.commit()

# Obtener progreso de usuario
query = select(UserNarrativeProgress).where(UserNarrativeProgress.user_id == 123456789)
result = await session.execute(query)
progress = result.scalar_one_or_none()

# Buscar usuarios activos en fragmento específico
query = select(UserNarrativeProgress).where(
    (UserNarrativeProgress.current_fragment_id == 5) &
    (UserNarrativeProgress.active == True)
)
result = await session.execute(query)
active_users = result.scalars().all()
```

## Modelo 5: UserDecisionHistory

**Descripción:** Historial de decisiones tomadas por usuarios en la narrativa.

**Tabla:** `user_decision_history`

### Estructura

```python
class UserDecisionHistory(Base):
    __tablename__ = "user_decision_history"

    # Identificador único
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Usuario que tomó la decisión
    user_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Fragmento donde se tomó la decisión
    fragment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("narrative_fragments.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Decisión que se tomó
    decision_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("fragment_decisions.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Fragmento destino (para registro)
    resulting_fragment_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("narrative_fragments.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamp de la decisión
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relaciones
    user: Mapped["User"] = relationship("User")
    fragment: Mapped["NarrativeFragment"] = relationship("NarrativeFragment")
    decision: Mapped["FragmentDecision"] = relationship("FragmentDecision")
    resulting_fragment: Mapped[Optional["NarrativeFragment"]] = relationship(
        "NarrativeFragment", 
        foreign_keys=[resulting_fragment_id]
    )

    # Índices
    __table_args__ = (
        Index('idx_decision_history_user', 'user_id'),
        Index('idx_decision_history_user_time', 'user_id', 'decided_at'),
        Index('idx_decision_history_fragment', 'fragment_id'),
    )
```

### Campos Detallados

| Campo | Tipo | Constraints | Descripción |
|-------|------|-----------|-------------|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único del historial |
| `user_id` | BIGINT | FK, NOT NULL | ID del usuario que tomó decisión |
| `fragment_id` | INTEGER | FK, NOT NULL | Fragmento donde se tomó la decisión |
| `decision_id` | INTEGER | FK, NOT NULL | ID de la decisión tomada |
| `resulting_fragment_id` | INTEGER | FK, NULL | Fragmento destino resultante |
| `decided_at` | DATETIME | NOT NULL | Timestamp de la decisión |
| `besitos_spent` | INTEGER | DEFAULT 0 | Besitos gastados en la decisión |

### Índices

```sql
-- Búsqueda por usuario
CREATE INDEX idx_decision_history_user ON user_decision_history(user_id);

-- Búsqueda cronológica por usuario
CREATE INDEX idx_decision_history_user_time ON user_decision_history(user_id, decided_at);

-- Búsqueda por fragmento
CREATE INDEX idx_decision_history_fragment ON user_decision_history(fragment_id);
```

### Ejemplo de Dato

```json
{
    "id": 1,
    "user_id": 123456789,
    "fragment_id": 1,
    "decision_id": 1,
    "resulting_fragment_id": 2,
    "decided_at": "2025-12-26T10:45:00.000000"
}
```

### Operaciones Comunes

```python
# Registrar decisión
decision_record = UserDecisionHistory(
    user_id=123456789,
    fragment_id=1,
    decision_id=1,
    resulting_fragment_id=2
)
session.add(decision_record)
await session.commit()

# Historial completo de usuario
query = select(UserDecisionHistory).where(
    UserDecisionHistory.user_id == 123456789
).order_by(UserDecisionHistory.decided_at.desc())
result = await session.execute(query)
history = result.scalars().all()

# Decisiones recientes en fragmento
from datetime import datetime, timedelta
recent_date = datetime.now(UTC) - timedelta(hours=24)
query = select(UserDecisionHistory).where(
    (UserDecisionHistory.fragment_id == 1) &
    (UserDecisionHistory.decided_at >= recent_date)
)
result = await session.execute(query)
recent_decisions = result.scalars().all()

# Análisis de decisión más popular
from sqlalchemy import func
query = select(
    UserDecisionHistory.decision_id,
    func.count(UserDecisionHistory.id).label('count')
).where(UserDecisionHistory.fragment_id == 1).group_by(UserDecisionHistory.decision_id)
result = await session.execute(query)
popularity_stats = result.fetchall()
```

## Relaciones Entre Modelos

### Diagrama de Relaciones

```
NarrativeChapter (1)
    ├─ Contiene múltiples NarrativeFragment (M)
    └─ Relación 1:M con NarrativeFragment

NarrativeFragment (M)
    ├─ Pertenence a un NarrativeChapter (1) 
    ├─ Tiene múltiples FragmentDecision (M)
    ├─ Puede ser destino de múltiples FragmentDecision (M)
    └─ Relación 1:M con FragmentDecision (origen y destino)

UserNarrativeProgress (1)
    ├─ Relación 1:1 con usuario
    └─ Apunta a un NarrativeFragment actual (M)

UserDecisionHistory (M)
    ├─ Relación M:1 con usuario
    ├─ Relación M:1 con fragmento origen
    ├─ Relación M:1 con decisión tomada
    └─ Relación M:1 opcional con fragmento destino
```

### Relación Chapter - Fragment

```python
# Chapter 1:M Fragments (un capítulo → muchos fragmentos)
chapter.fragments  # Todos los fragmentos en este capítulo

# Fragment M:1 Chapter (un fragmento → un capítulo)
fragment.chapter  # Capítulo al que pertenece el fragmento

# Ejemplo de uso
async with get_session() as session:
    chapter = await session.get(NarrativeChapter, 1)
    # Cargar relación
    from sqlalchemy.orm import selectinload
    query = select(NarrativeChapter).where(...).options(
        selectinload(NarrativeChapter.fragments)
    )
    result = await session.execute(query)
    chapter = result.scalar_one()

    # Acceder fragmentos
    for fragment in chapter.fragments:
        print(f"Fragmento: {fragment.title}")
```

## Cascadas y Limpieza

### Cascade Delete

Cuando se elimina un capítulo, sus fragmentos relacionados se eliminan:

```python
fragments = relationship(
    "NarrativeFragment",
    back_populates="chapter",
    cascade="all, delete-orphan"  # Elimina fragmentos huérfanos
)
```

**Uso:**
```python
async with get_session() as session:
    chapter = await session.get(NarrativeChapter, 1)
    await session.delete(chapter)
    await session.commit()
    # Todos los NarrativeFragment con chapter_id=1 se eliminan automáticamente
```

## Performance y Optimización

### Índices Actuales

1. **NarrativeChapter:**
   - `idx_chapter_order(order)` - Para ordenar capítulos
   - `idx_chapter_type(chapter_type)` - Para filtrar por tipo
   - `idx_chapter_active(active)` - Para filtrar activos

2. **NarrativeFragment:**
   - `idx_fragment_chapter_order(chapter_id, order)` - Para obtener fragmentos ordenados por capítulo
   - `idx_fragment_chapter(chapter_id)` - Para búsquedas por capítulo

3. **FragmentDecision:**
   - `idx_decision_fragment(fragment_id)` - Para obtener decisiones por fragmento
   - `idx_decision_order(fragment_id, order)` - Para ordenar decisiones en fragmento

4. **UserNarrativeProgress:**
   - `idx_user_progress_active(user_id, active)` - Para obtener progreso activo de usuario
   - `idx_user_progress_fragment(current_fragment_id)` - Para encontrar usuarios en fragmento

5. **UserDecisionHistory:**
   - `idx_decision_history_user(user_id)` - Para historial de usuario
   - `idx_decision_history_user_time(user_id, decided_at)` - Para historial cronológico
   - `idx_decision_history_fragment(fragment_id)` - Para decisiones por fragmento

### Queries Optimizadas

```python
# BUENO: Usa índices
query = select(NarrativeFragment).where(
    NarrativeFragment.chapter_id == 1
).order_by(NarrativeFragment.order)

# BUENO: Carga relaciones eficientemente
query = select(NarrativeChapter).options(
    selectinload(NarrativeChapter.fragments)
)

# MALO: N+1 query (lenta)
chapters = session.execute(select(NarrativeChapter)).scalars().all()
for chapter in chapters:
    print(chapter.fragments)  # Query adicional para cada capítulo
```

## Backup y Recovery

### Backup Manual

```bash
# Copiar archivo base de datos
cp bot.db bot.db.narrative_backup

# Backup con timestamp
cp bot.db "bot.db.narrative.$(date +%Y%m%d_%H%M%S).backup"
```

### Restore

```bash
# Restaurar backup narrativo
cp bot.db.narrative.backup bot.db

# Reiniciar bot
python main.py
```

## Consultas de Ejemplo

### Estadísticas Narrativas

```python
# Contar fragmentos por capítulo
from sqlalchemy import func

async with get_session() as session:
    query = select(
        NarrativeChapter.title,
        func.count(NarrativeFragment.id).label('fragment_count')
    ).join(
        NarrativeFragment, 
        NarrativeChapter.id == NarrativeFragment.chapter_id
    ).group_by(NarrativeChapter.id)
    result = await session.execute(query)
    stats = result.fetchall()

    for title, count in stats:
        print(f"Capítulo {title}: {count} fragmentos")

# Usuarios activos en narrativa
query = select(func.count(UserNarrativeProgress.user_id)).where(
    UserNarrativeProgress.active == True
)
result = await session.execute(query)
active_users = result.scalar()

# Decisiones más populares
query = select(
    FragmentDecision.text,
    func.count(UserDecisionHistory.id).label('times_chosen')
).join(
    UserDecisionHistory,
    FragmentDecision.id == UserDecisionHistory.decision_id
).where(
    UserDecisionHistory.decided_at >= datetime.now(UTC) - timedelta(days=7)
).group_by(FragmentDecision.id).order_by(
    func.count(UserDecisionHistory.id).desc()
).limit(5)
result = await session.execute(query)
popular_decisions = result.fetchall()
```

### Reportes Avanzados

```python
# Usuarios por arquetipo detectado
query = select(
    UserNarrativeProgress.current_archetype,
    func.count(UserNarrativeProgress.user_id).label('count')
).where(
    UserNarrativeProgress.current_archetype.isnot(None)
).group_by(UserNarrativeProgress.current_archetype)
result = await session.execute(query)
archetype_stats = result.fetchall()

# Tiempo promedio por capítulo
from sqlalchemy import case
query = select(
    NarrativeChapter.title,
    func.avg(UserNarrativeProgress.total_time_spent).label('avg_time_spent')
).join(
    UserNarrativeProgress,
    case(
        (UserNarrativeProgress.chapters_completed.contains([NarrativeChapter.id]), True),
        else_=False
    )
).where(
    UserNarrativeProgress.total_time_spent > 0
).group_by(NarrativeChapter.id)
result = await session.execute(query)
chapter_times = result.fetchall()
```

---

**Última actualización:** 2025-12-26  
**Versión:** 1.0.0
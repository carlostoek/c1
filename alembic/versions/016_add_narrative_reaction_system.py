"""add narrative reaction system

Revision ID: 016
Revises: 015
Create Date: 2026-01-10

Agrega sistema de reacciones narrativas con tracking de tiempo de respuesta:
- Extiende custom_reactions con campos para reacciones narrativas
- Crea narrative_reaction_waits para tracking de misiones de reacción
- Integra reacciones con sistema de arquetipos
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add narrative reaction system."""

    # 1. Extender tabla custom_reactions con campos narrativos
    op.add_column(
        'custom_reactions',
        sa.Column('response_time_seconds', sa.Integer(), nullable=True)
    )
    op.add_column(
        'custom_reactions',
        sa.Column('is_narrative_reaction', sa.Boolean(), nullable=False, server_default='0')
    )
    op.add_column(
        'custom_reactions',
        sa.Column('narrative_fragment_key', sa.String(length=50), nullable=True)
    )

    # Índices para optimizar queries de reacciones narrativas
    op.create_index(
        'idx_narrative_reaction',
        'custom_reactions',
        ['user_id', 'is_narrative_reaction']
    )
    op.create_index(
        'idx_narrative_response_time',
        'custom_reactions',
        ['user_id', 'response_time_seconds']
    )

    # 2. Crear tabla narrative_reaction_waits
    op.create_table(
        'narrative_reaction_waits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('fragment_key', sa.String(length=50), nullable=False),
        sa.Column('broadcast_message_id', sa.Integer(), nullable=False),
        sa.Column('required_emoji', sa.String(length=10), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('next_fragment_key', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Índices para narrative_reaction_waits
    op.create_index(
        'idx_narrative_reaction_wait_user',
        'narrative_reaction_waits',
        ['user_id'],
        unique=True
    )
    op.create_index(
        'idx_narrative_reaction_expires',
        'narrative_reaction_waits',
        ['expires_at']
    )
    op.create_index(
        op.f('ix_narrative_reaction_waits_user_id'),
        'narrative_reaction_waits',
        ['user_id']
    )


def downgrade() -> None:
    """Remove narrative reaction system."""

    # Eliminar tabla narrative_reaction_waits
    op.drop_index(op.f('ix_narrative_reaction_waits_user_id'), table_name='narrative_reaction_waits')
    op.drop_index('idx_narrative_reaction_expires', table_name='narrative_reaction_waits')
    op.drop_index('idx_narrative_reaction_wait_user', table_name='narrative_reaction_waits')
    op.drop_table('narrative_reaction_waits')

    # Eliminar índices de custom_reactions
    op.drop_index('idx_narrative_response_time', table_name='custom_reactions')
    op.drop_index('idx_narrative_reaction', table_name='custom_reactions')

    # Eliminar columnas de custom_reactions
    op.drop_column('custom_reactions', 'narrative_fragment_key')
    op.drop_column('custom_reactions', 'is_narrative_reaction')
    op.drop_column('custom_reactions', 'response_time_seconds')

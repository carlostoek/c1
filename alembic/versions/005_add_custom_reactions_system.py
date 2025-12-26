"""Add custom reactions system for broadcasting

Revision ID: 005
Revises: 004
Create Date: 2025-12-24 00:00:00.000000

Changes:
- Add broadcast_messages table for tracking broadcasts with gamification
- Add custom_reactions table for tracking user reactions via buttons
- Add UI fields to reactions table (button_emoji, button_label, sort_order)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agregar sistema de reacciones personalizadas para broadcasting.

    Orden de creación:
    1. broadcast_messages - Tracking de broadcasts con gamificación
    2. Modificar reactions - Agregar campos de UI para botones
    3. custom_reactions - Tracking de reacciones por botones
    """

    # 1. Crear tabla broadcast_messages
    op.create_table(
        'broadcast_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(20), nullable=False),
        sa.Column('content_text', sa.String(4096), nullable=True),
        sa.Column('media_file_id', sa.String(200), nullable=True),
        sa.Column('sent_by', sa.BigInteger(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('gamification_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('reaction_buttons', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('content_protected', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('total_reactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_reactors', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sent_by'], ['users.user_id'], ),
    )

    # Crear índices para broadcast_messages
    op.create_index('idx_chat_message', 'broadcast_messages', ['chat_id', 'message_id'], unique=True)
    op.create_index('idx_sent_at', 'broadcast_messages', ['sent_at'], unique=False)
    op.create_index('idx_gamification_enabled', 'broadcast_messages', ['gamification_enabled'], unique=False)

    # 2. Modificar tabla reactions - Agregar campos de UI
    op.add_column('reactions', sa.Column('button_emoji', sa.String(10), nullable=True))
    op.add_column('reactions', sa.Column('button_label', sa.String(50), nullable=True))
    op.add_column('reactions', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # 3. Crear tabla custom_reactions
    op.create_table(
        'custom_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('broadcast_message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reaction_type_id', sa.Integer(), nullable=False),
        sa.Column('emoji', sa.String(10), nullable=False),
        sa.Column('besitos_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['broadcast_message_id'], ['broadcast_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['reaction_type_id'], ['reactions.id'], ),
    )

    # Crear índices para custom_reactions
    op.create_index(
        'idx_unique_reaction',
        'custom_reactions',
        ['broadcast_message_id', 'user_id', 'reaction_type_id'],
        unique=True
    )
    op.create_index('idx_user_created', 'custom_reactions', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_broadcast_message', 'custom_reactions', ['broadcast_message_id'], unique=False)


def downgrade() -> None:
    """
    Revertir cambios del sistema de reacciones personalizadas.
    """
    # Eliminar tabla custom_reactions y sus índices
    op.drop_index('idx_broadcast_message', table_name='custom_reactions')
    op.drop_index('idx_user_created', table_name='custom_reactions')
    op.drop_index('idx_unique_reaction', table_name='custom_reactions')
    op.drop_table('custom_reactions')

    # Eliminar campos de UI de reactions
    op.drop_column('reactions', 'sort_order')
    op.drop_column('reactions', 'button_label')
    op.drop_column('reactions', 'button_emoji')

    # Eliminar tabla broadcast_messages y sus índices
    op.drop_index('idx_gamification_enabled', table_name='broadcast_messages')
    op.drop_index('idx_sent_at', table_name='broadcast_messages')
    op.drop_index('idx_chat_message', table_name='broadcast_messages')
    op.drop_table('broadcast_messages')

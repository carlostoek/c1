"""Add gamification module with 13 tables

Revision ID: 004_add_gamification_module
Revises: 003_add_users_and_roles
Create Date: 2025-12-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '004_add_gamification_module'
down_revision = '003_add_users_and_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Crea todas las tablas del módulo de gamificación.
    
    Orden:
    1. Tablas independientes
    2. Tablas con FKs
    3. Índices
    4. Seed data inicial
    """
    
    # NIVEL 1: Tablas sin FKs
    # -----------------------
    
    # 1. gamification_config (singleton)
    op.create_table(
        'gamification_config',
        sa.Column('id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('besitos_per_reaction', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_besitos_per_day', sa.Integer(), nullable=True),
        sa.Column('streak_reset_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. reactions
    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('besitos_value', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reactions_emoji', 'reactions', ['emoji'], unique=True)

    # 3. levels
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('min_besitos', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('benefits', sa.String(length=500), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_levels_min_besitos', 'levels', ['min_besitos'])
    op.create_index('ix_levels_order', 'levels', ['order'])
    op.create_index('ix_levels_name', 'levels', ['name'], unique=True)

    # 4. config_templates
    op.create_table(
        'config_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('template_data', sa.String(length=5000), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_config_templates_category', 'config_templates', ['category'])
    op.create_index('ix_config_templates_created_by', 'config_templates', ['created_by'])

    # NIVEL 2: Tablas con FKs a User del core + NIVEL 1
    # -------------------------------------------------

    # 5. user_gamification
    op.create_table(
        'user_gamification',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('total_besitos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('besitos_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('besitos_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_level_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['current_level_id'], ['levels.id'], name='fk_user_gamification_level_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name='fk_user_gamification_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index('ix_user_gamification_total_besitos', 'user_gamification', ['total_besitos'])

    # 6. user_streaks
    op.create_table(
        'user_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reaction_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], name='fk_user_streaks_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_streaks_user_id')
    )
    op.create_index('ix_user_streaks_user_id', 'user_streaks', ['user_id'])

    # NIVEL 3: Tablas con FKs a NIVEL 2
    # ---------------------------------

    # 7. user_reactions
    op.create_table(
        'user_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reaction_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('reacted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reaction_id'], ['reactions.id'], name='fk_user_reactions_reaction_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], name='fk_user_reactions_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_reactions_user_reacted_at', 'user_reactions', ['user_id', 'reacted_at'])
    op.create_index('ix_user_reactions_user_channel', 'user_reactions', ['user_id', 'channel_id'])

    # 8. missions
    op.create_table(
        'missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('mission_type', sa.String(length=50), nullable=False),
        sa.Column('criteria', sa.String(length=1000), nullable=False),
        sa.Column('besitos_reward', sa.Integer(), nullable=False),
        sa.Column('auto_level_up_id', sa.Integer(), nullable=True),
        sa.Column('unlock_rewards', sa.String(length=200), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('repeatable', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['auto_level_up_id'], ['levels.id'], name='fk_missions_auto_level_up_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_missions_active', 'missions', ['active'])
    op.create_index('ix_missions_created_by', 'missions', ['created_by'])

    # 9. rewards
    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('reward_type', sa.String(length=50), nullable=False),
        sa.Column('cost_besitos', sa.Integer(), nullable=True),
        sa.Column('unlock_conditions', sa.String(length=1000), nullable=True),
        sa.Column('reward_metadata', sa.String(length=1000), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rewards_active', 'rewards', ['active'])
    op.create_index('ix_rewards_reward_type', 'rewards', ['reward_type'])
    
    # NIVEL 4: Tablas con FKs a NIVEL 3
    # ---------------------------------

    # 10. user_missions
    op.create_table(
        'user_missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('progress', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], name='fk_user_missions_mission_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], name='fk_user_missions_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'mission_id', name='uc_user_mission')
    )
    op.create_index('ix_user_missions_user_status', 'user_missions', ['user_id', 'status'])

    # 11. user_rewards
    op.create_table(
        'user_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=False),
        sa.Column('obtained_at', sa.DateTime(), nullable=False),
        sa.Column('obtained_via', sa.String(length=50), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], name='fk_user_rewards_reward_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], name='fk_user_rewards_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'reward_id', name='uc_user_reward')
    )
    op.create_index('ix_user_rewards_user_id', 'user_rewards', ['user_id'])
    op.create_index('ix_user_rewards_obtained_via', 'user_rewards', ['obtained_via'])

    # NIVEL 5: Tablas con herencia de NIVEL 4
    # ----------------------------------------

    # 12. badges
    op.create_table(
        'badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('rarity', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['rewards.id'], name='fk_badges_reward_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_badges_rarity', 'badges', ['rarity'])

    # 13. user_badges
    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('displayed', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['id'], ['user_rewards.id'], name='fk_user_badges_user_reward_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_badges_displayed', 'user_badges', ['displayed'])
    
    # SEED DATA
    # ---------
    
    # Insertar configuración inicial
    op.execute(sa.text("""
        INSERT INTO gamification_config (id, besitos_per_reaction, streak_reset_hours, notifications_enabled, updated_at)
        VALUES (1, 1, 24, 1, CURRENT_TIMESTAMP)
    """))

    # Insertar reacciones por defecto
    op.execute(sa.text("""
        INSERT INTO reactions (emoji, besitos_value, active, created_at)
        VALUES
            ('❤️', 1, 1, CURRENT_TIMESTAMP),
            ('🔥', 1, 1, CURRENT_TIMESTAMP),
            ('👍', 1, 1, CURRENT_TIMESTAMP),
            ('💯', 2, 1, CURRENT_TIMESTAMP),
            ('🎉', 2, 1, CURRENT_TIMESTAMP)
    """))

    # Insertar niveles iniciales
    op.execute(sa.text("""
        INSERT INTO levels (name, min_besitos, "order", active, created_at)
        VALUES
            ('Novato', 0, 1, 1, CURRENT_TIMESTAMP),
            ('Regular', 500, 2, 1, CURRENT_TIMESTAMP),
            ('Entusiasta', 2000, 3, 1, CURRENT_TIMESTAMP),
            ('Fanático', 5000, 4, 1, CURRENT_TIMESTAMP),
            ('Leyenda', 10000, 5, 1, CURRENT_TIMESTAMP)
    """))


def downgrade() -> None:
    """
    Elimina todas las tablas del módulo.
    
    Orden inverso a upgrade (NIVEL 5 → NIVEL 1)
    """
    
    # NIVEL 5 (Herencia de NIVEL 4)
    op.drop_table('user_badges')
    op.drop_table('badges')
    
    # NIVEL 4 (FK a NIVEL 3)
    op.drop_table('user_rewards')
    op.drop_table('user_missions')
    
    # NIVEL 3 (FK a NIVEL 2)
    op.drop_table('rewards')
    op.drop_table('missions')
    op.drop_table('user_reactions')
    
    # NIVEL 2 (FK a User del core + NIVEL 1)
    op.drop_table('user_streaks')
    op.drop_table('user_gamification')
    
    # NIVEL 1 (sin FKs)
    op.drop_table('config_templates')
    op.drop_table('levels')
    op.drop_table('reactions')
    op.drop_table('gamification_config')
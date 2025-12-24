"""Add gamification module with 13 tables

Revision ID: 004
Revises: 003
Create Date: 2024-12-24 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Crea todas las tablas del módulo de gamificación.

    Orden de creación:
    NIVEL 1: Tablas sin FKs (GamificationConfig, Reaction, Level, ConfigTemplate)
    NIVEL 2: Tablas con FKs a User core (UserGamification, UserStreak)
    NIVEL 3: Tablas con FKs a NIVEL 1 y 2 (UserReaction, Mission, Reward)
    NIVEL 4: Tablas con FKs a NIVEL 3 (UserMission, UserReward)
    NIVEL 5: Herencia de NIVEL 4 (Badge, UserBadge)
    """

    # NIVEL 1: Tablas sin Foreign Keys
    # ================================

    # 1. gamification_config - Singleton de configuración
    op.create_table(
        'gamification_config',
        sa.Column('id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('besitos_per_reaction', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_besitos_per_day', sa.Integer(), nullable=True),
        sa.Column('streak_reset_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. reactions - Catálogo de emojis disponibles
    op.create_table(
        'reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('emoji', sa.String(10), nullable=False),
        sa.Column('besitos_value', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emoji')
    )

    # 3. levels - Niveles de progresión
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('min_besitos', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('benefits', sa.String(500), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Índices para Level
    op.create_index('ix_levels_min_besitos', 'levels', ['min_besitos'])
    op.create_index('ix_levels_order', 'levels', ['order'])

    # 4. config_templates - Plantillas predefinidas
    op.create_table(
        'config_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('template_data', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


    # NIVEL 2: FK a User core + NIVEL 1
    # =================================

    # 5. user_gamification - Perfil de gamificación por usuario
    op.create_table(
        'user_gamification',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('total_besitos', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('besitos_earned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('besitos_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_level_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['current_level_id'], ['levels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Índices para UserGamification
    op.create_index('ix_user_gamification_total_besitos', 'user_gamification', ['total_besitos'])

    # 6. user_streaks - Rachas de reacciones por usuario
    op.create_table(
        'user_streaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_reaction_date', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


    # NIVEL 3: FK a NIVEL 2 y NIVEL 1
    # ===============================

    # 7. user_reactions - Historial de reacciones
    op.create_table(
        'user_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reaction_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('reacted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reaction_id'], ['reactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Índices para UserReaction
    op.create_index('ix_user_reactions_user_reacted', 'user_reactions', ['user_id', 'reacted_at'])
    op.create_index('ix_user_reactions_user_channel', 'user_reactions', ['user_id', 'channel_id'])

    # 8. missions - Misiones configuradas
    op.create_table(
        'missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('mission_type', sa.String(50), nullable=False),
        sa.Column('criteria', sa.String(1000), nullable=False),
        sa.Column('besitos_reward', sa.Integer(), nullable=False),
        sa.Column('auto_level_up_id', sa.Integer(), nullable=True),
        sa.Column('unlock_rewards', sa.String(200), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('repeatable', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['auto_level_up_id'], ['levels.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. rewards - Recompensas disponibles
    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('reward_type', sa.String(50), nullable=False),
        sa.Column('cost_besitos', sa.Integer(), nullable=True),
        sa.Column('unlock_conditions', sa.String(1000), nullable=True),
        sa.Column('reward_metadata', sa.String(1000), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


    # NIVEL 4: FK a NIVEL 3
    # ====================

    # 10. user_missions - Progreso en misiones por usuario
    op.create_table(
        'user_missions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('mission_id', sa.Integer(), nullable=False),
        sa.Column('progress', sa.String(500), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Índices para UserMission
    op.create_index('ix_user_missions_user_mission', 'user_missions', ['user_id', 'mission_id'])
    op.create_index('ix_user_missions_user_status', 'user_missions', ['user_id', 'status'])

    # 11. user_rewards - Recompensas obtenidas por usuarios
    op.create_table(
        'user_rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=False),
        sa.Column('obtained_at', sa.DateTime(), nullable=False),
        sa.Column('obtained_via', sa.String(50), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user_gamification.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Índices para UserReward
    op.create_index('ix_user_rewards_user_reward', 'user_rewards', ['user_id', 'reward_id'])


    # NIVEL 5: Herencia (joined table)
    # ===============================

    # 12. badges - Extensión de rewards (badges específicos)
    op.create_table(
        'badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('icon', sa.String(10), nullable=False),
        sa.Column('rarity', sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['rewards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. user_badges - Extensión de user_rewards (badges obtenidos)
    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('displayed', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['id'], ['user_rewards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


    # SEED DATA
    # =========

    # Insertar configuración inicial
    op.execute("""
        INSERT INTO gamification_config (id, besitos_per_reaction, streak_reset_hours, notifications_enabled)
        VALUES (1, 1, 24, 1)
    """)

    # Insertar reacciones por defecto
    op.execute("""
        INSERT INTO reactions (emoji, besitos_value, active)
        VALUES
            ('❤️', 1, 1),
            ('🔥', 1, 1),
            ('👍', 1, 1)
    """)

    # Insertar niveles iniciales
    op.execute("""
        INSERT INTO levels (name, min_besitos, "order", active)
        VALUES
            ('Novato', 0, 1, 1),
            ('Regular', 500, 2, 1),
            ('Entusiasta', 2000, 3, 1),
            ('Fanático', 5000, 4, 1),
            ('Leyenda', 10000, 5, 1)
    """)


def downgrade() -> None:
    """
    Elimina todas las tablas del módulo en orden inverso.

    Orden inverso a upgrade (NIVEL 5 → NIVEL 1)
    """

    # NIVEL 5: Herencia
    op.drop_table('user_badges')
    op.drop_table('badges')

    # NIVEL 4: FK a NIVEL 3
    op.drop_table('user_rewards')
    op.drop_table('user_missions')

    # NIVEL 3: FK a NIVEL 1 y 2
    op.drop_table('rewards')
    op.drop_table('missions')
    op.drop_table('user_reactions')

    # NIVEL 2: FK a User core + NIVEL 1
    op.drop_table('user_streaks')
    op.drop_table('user_gamification')

    # NIVEL 1: Sin FKs
    op.drop_table('config_templates')
    op.drop_table('levels')
    op.drop_table('reactions')
    op.drop_table('gamification_config')

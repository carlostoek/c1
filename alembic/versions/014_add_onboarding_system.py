"""add onboarding system

Revision ID: 014
Revises: 013
Create Date: 2025-12-28

Sistema de onboarding narrativo post-aprobación:
- Tracking de progreso de onboarding por usuario
- Fragmentos de contenido editables para el onboarding
- Detección de arquetipo durante onboarding
- Otorgamiento de besitos de bienvenida
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for onboarding system."""

    # ============================================================
    # 1. USER ONBOARDING PROGRESS - Tracking de progreso
    # ============================================================
    op.create_table(
        'user_onboarding_progress',
        sa.Column('user_id', sa.BigInteger(), primary_key=True),
        sa.Column('started', sa.Boolean(), default=False, nullable=False),
        sa.Column('completed', sa.Boolean(), default=False, nullable=False),
        sa.Column('current_step', sa.Integer(), default=0, nullable=False),
        sa.Column('archetype_scores', sa.Text(), nullable=True),
        sa.Column('decisions_made', sa.Text(), nullable=True),
        sa.Column('besitos_granted', sa.Integer(), default=0, nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # ============================================================
    # 2. ONBOARDING FRAGMENTS - Contenido editable del onboarding
    # ============================================================
    op.create_table(
        'onboarding_fragments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('step', sa.Integer(), unique=True, nullable=False),
        sa.Column('speaker', sa.String(50), default='diana', nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('decisions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_onboarding_step', 'onboarding_fragments', ['step'])


def downgrade() -> None:
    """Remove onboarding tables."""
    op.drop_index('idx_onboarding_step', 'onboarding_fragments')
    op.drop_table('onboarding_fragments')
    op.drop_table('user_onboarding_progress')

"""Migration para añadir tablas de tracking de conversiones (F6.7)

Añade las siguientes tablas:
- conversion_events: Eventos de conversión y ventas
- conversion_funnels: Seguimiento de embudo de conversión
- lead_qualifications: Calificación de leads/probabilidad de conversión
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '020_add_conversion_tracking_tables'
down_revision = '019_add_gabinete_features'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla conversion_events
    op.create_table(
        'conversion_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('product_type', sa.String(length=50), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('referrer', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_conversion_user_event', 'user_id', 'event_type'),
        sa.Index('idx_conversion_event_created', 'event_type', 'created_at'),
        sa.Index('idx_conversion_user_created', 'user_id', 'created_at'),
        sa.Index('idx_conversion_product', 'product_type', 'product_id')
    )

    # Crear tabla conversion_funnels
    op.create_table(
        'conversion_funnels',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('last_conversion_step', sa.String(length=50), nullable=True),
        sa.Column('conversion_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('vip_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('premium_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('mapa_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('objections_raised', sa.Integer(), server_default='0', nullable=False),
        sa.Column('objections_handled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('payment_initiated_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('payment_confirmed_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('payment_approved_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversion_value', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('conversion_currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('last_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('first_interaction_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.Index('idx_conversion_funnel_step', 'last_conversion_step'),
        sa.Index('idx_conversion_funnel_updated', 'updated_at')
    )

    # Crear tabla lead_qualifications
    op.create_table(
        'lead_qualifications',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('conversion_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('qualification_level', sa.String(length=20), server_default='none', nullable=False),
        sa.Column('last_scored_at', sa.DateTime(), nullable=True),
        sa.Column('engagement_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('intent_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('budget_indicator', sa.String(length=20), server_default='unknown', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.Index('idx_lead_qualification_score', 'conversion_score'),
        sa.Index('idx_lead_qualification_level', 'qualification_level')
    )


def downgrade():
    # Eliminar tablas en orden inverso
    op.drop_table('lead_qualifications')
    op.drop_table('conversion_funnels')
    op.drop_table('conversion_events')
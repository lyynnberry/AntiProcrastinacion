"""perfil: idioma, flujo de primer uso, preferencia de recordatorios y foto

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14 12:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('usuario', sa.Column('idioma', sa.String(length=5), server_default='es', nullable=False))
    op.add_column('usuario', sa.Column('personalizacion_completada_en', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuario', sa.Column('tutorial_completado_en', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuario', sa.Column('foto_actualizada_en', sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(op.f('ck_usuario_idioma_valido'), 'usuario', "idioma IN ('es', 'en')")

    op.create_table('preferencia_notificacion',
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('perfil_recordatorios', sa.String(length=12), server_default='equilibrado', nullable=False),
    sa.Column('notificaciones_activas', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("perfil_recordatorios IN ('tranquilo', 'equilibrado', 'insistente')", name=op.f('ck_preferencia_notificacion_perfil_valido')),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_preferencia_notificacion_id_usuario_usuario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id_usuario', name=op.f('pk_preferencia_notificacion'))
    )
    op.create_table('foto_perfil',
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('contenido', sa.LargeBinary(), nullable=False),
    sa.Column('tipo_mime', sa.String(length=32), nullable=False),
    sa.Column('tamano_bytes', sa.Integer(), nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_foto_perfil_id_usuario_usuario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id_usuario', name=op.f('pk_foto_perfil'))
    )


def downgrade() -> None:
    op.drop_table('foto_perfil')
    op.drop_table('preferencia_notificacion')
    op.drop_constraint(op.f('ck_usuario_idioma_valido'), 'usuario', type_='check')
    op.drop_column('usuario', 'foto_actualizada_en')
    op.drop_column('usuario', 'tutorial_completado_en')
    op.drop_column('usuario', 'personalizacion_completada_en')
    op.drop_column('usuario', 'idioma')

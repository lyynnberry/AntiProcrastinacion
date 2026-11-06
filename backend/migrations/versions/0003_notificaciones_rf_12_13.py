"""notificaciones RF-12/RF-13: tabla notificacion e historial_evento.id_notificacion

Toma la parte de notificaciones del parche `entregas/paso1_migracion_0003.patch` (revisada) y agrega
fecha_generacion, fecha_sincronizacion, fecha_cancelacion, es_aviso_final y el índice único parcial contra
duplicados. NO incluye sesion_enfoque, gamificación ni análisis de riesgo (fuera de alcance). Solo agrega
estructura: no modifica ni borra datos existentes.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-06 04:30:00
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('notificacion',
    sa.Column('id_notificacion', sa.Uuid(), nullable=False),
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('id_tarea', sa.Uuid(), nullable=True),
    sa.Column('tipo', sa.String(length=20), nullable=False),
    sa.Column('nivel_intensidad', sa.SmallInteger(), nullable=True),
    sa.Column('mensaje', sa.Text(), nullable=False),
    sa.Column('requiere_accion', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('es_aviso_final', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('estado', sa.String(length=15), server_default='PROGRAMADA', nullable=False),
    sa.Column('fecha_generacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('fecha_programada', sa.DateTime(timezone=True), nullable=False),
    sa.Column('fecha_sincronizacion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('fecha_envio', sa.DateTime(timezone=True), nullable=True),
    sa.Column('fecha_cancelacion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('accion_respuesta', sa.String(length=20), nullable=True),
    sa.Column('fecha_respuesta', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("tipo IN ('RECORDATORIO', 'URGENTE', 'CRITICA', 'CORRECTIVA', 'ACUMULACION')", name=op.f('ck_notificacion_tipo_valido')),
    sa.CheckConstraint("estado IN ('PROGRAMADA', 'ENVIADA', 'RESPONDIDA', 'IGNORADA', 'CANCELADA')", name=op.f('ck_notificacion_estado_valido')),
    sa.CheckConstraint("accion_respuesta IN ('COMPLETAR', 'INICIAR_ENFOQUE', 'POSPONER', 'CONTINUAR_DESPUES')", name=op.f('ck_notificacion_accion_respuesta_valida')),
    sa.CheckConstraint('nivel_intensidad BETWEEN 1 AND 4', name=op.f('ck_notificacion_nivel_intensidad_valido')),
    sa.CheckConstraint("id_tarea IS NOT NULL OR tipo = 'ACUMULACION'", name=op.f('ck_notificacion_tarea_obligatoria_salvo_acumulacion')),
    sa.CheckConstraint('length(trim(mensaje)) > 0', name=op.f('ck_notificacion_mensaje_no_vacio')),
    sa.ForeignKeyConstraint(['id_tarea', 'id_usuario'], ['tarea.id_tarea', 'tarea.id_usuario'], name='fk_notificacion_tarea_del_mismo_usuario'),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_notificacion_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_notificacion', name=op.f('pk_notificacion')),
    sa.UniqueConstraint('id_notificacion', 'id_usuario', name='uq_notificacion_id_usuario')
    )
    op.create_index('ix_notificacion_tarea_estado', 'notificacion', ['id_tarea', 'estado'], unique=False)
    op.create_index('ix_notificacion_usuario_estado_programada', 'notificacion', ['id_usuario', 'estado', 'fecha_programada'], unique=False)
    op.create_index('uq_notificacion_tarea_momento_vigente', 'notificacion', ['id_tarea', 'fecha_programada'], unique=True, postgresql_where=sa.text("estado <> 'CANCELADA'"))

    op.add_column('historial_evento', sa.Column('id_notificacion', sa.Uuid(), nullable=True))
    op.create_foreign_key('fk_historial_notificacion_del_mismo_usuario', 'historial_evento', 'notificacion', ['id_notificacion', 'id_usuario'], ['id_notificacion', 'id_usuario'])
    op.create_index('ix_historial_evento_usuario_fecha', 'historial_evento', ['id_usuario', 'fecha_evento'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_historial_evento_usuario_fecha', table_name='historial_evento')
    op.drop_constraint('fk_historial_notificacion_del_mismo_usuario', 'historial_evento', type_='foreignkey')
    op.drop_column('historial_evento', 'id_notificacion')
    op.drop_index('uq_notificacion_tarea_momento_vigente', table_name='notificacion', postgresql_where=sa.text("estado <> 'CANCELADA'"))
    op.drop_index('ix_notificacion_usuario_estado_programada', table_name='notificacion')
    op.drop_index('ix_notificacion_tarea_estado', table_name='notificacion')
    op.drop_table('notificacion')

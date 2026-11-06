"""gamificación RF-21 a RF-27: perfil, días de racha, transacciones, logros, recuperación y tarea.fecha_programada

Crea las 6 tablas de gamificación de V6 §4.2 (con las extensiones de DECISIONES.md), agrega la columna opcional
tarea.fecha_programada (RF-21: compromiso de un día) y carga el catálogo inicial de 12 logros. Solo agrega
estructura y datos de catálogo: no modifica ni borra datos existentes. `downgrade` lo revierte.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-06 17:16:35.692726
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

LOGROS_INICIALES = [
    ('RACHA_3', 'Arranque', 'Mantén una racha de 3 días.', 'Kick-off', 'Keep a 3-day streak.', 'RACHA', 'DIAS_RACHA', 3, 15),
    ('RACHA_7', 'Semana firme', 'Mantén una racha de 7 días.', 'Solid week', 'Keep a 7-day streak.', 'RACHA', 'DIAS_RACHA', 7, 40),
    ('RACHA_30', 'Mes imparable', 'Mantén una racha de 30 días.', 'Unstoppable month', 'Keep a 30-day streak.', 'RACHA', 'DIAS_RACHA', 30, 150),
    ('A_TIEMPO_1', 'Primera entrega', 'Completa tu primera tarea a tiempo.', 'First delivery', 'Complete your first task on time.', 'PRODUCTIVIDAD', 'TAREAS_A_TIEMPO', 1, 5),
    ('A_TIEMPO_10', 'Productivo', 'Completa 10 tareas a tiempo.', 'Productive', 'Complete 10 tasks on time.', 'PRODUCTIVIDAD', 'TAREAS_A_TIEMPO', 10, 30),
    ('A_TIEMPO_50', 'Máquina de entregas', 'Completa 50 tareas a tiempo.', 'Delivery machine', 'Complete 50 tasks on time.', 'PRODUCTIVIDAD', 'TAREAS_A_TIEMPO', 50, 100),
    ('PUNTOS_100', 'Centenario', 'Acumula 100 puntos.', 'Centurion', 'Earn 100 points.', 'CONSTANCIA', 'PUNTOS_TOTALES', 100, 10),
    ('PUNTOS_500', 'Constante', 'Acumula 500 puntos.', 'Consistent', 'Earn 500 points.', 'CONSTANCIA', 'PUNTOS_TOTALES', 500, 25),
    ('PUNTOS_1000', 'Leyenda', 'Acumula 1000 puntos.', 'Legend', 'Earn 1000 points.', 'CONSTANCIA', 'PUNTOS_TOTALES', 1000, 50),
    ('ANTICIPADA_1', 'Adelantado', 'Completa una tarea al menos 24 h antes de su fecha límite.', 'Ahead of time', 'Complete a task at least 24 h before its deadline.', 'VELOCIDAD', 'TAREAS_ANTICIPADAS', 1, 10),
    ('ANTICIPADA_5', 'Previsor', 'Completa 5 tareas al menos 24 h antes de su fecha límite.', 'Planner', 'Complete 5 tasks at least 24 h before their deadline.', 'VELOCIDAD', 'TAREAS_ANTICIPADAS', 5, 30),
    ('ANTICIPADA_20', 'Relámpago', 'Completa 20 tareas al menos 24 h antes de su fecha límite.', 'Lightning', 'Complete 20 tasks at least 24 h before their deadline.', 'VELOCIDAD', 'TAREAS_ANTICIPADAS', 20, 80),
]


def upgrade() -> None:
    op.create_table('logro',
    sa.Column('id_logro', sa.Uuid(), nullable=False),
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('nombre_en', sa.String(length=100), nullable=False),
    sa.Column('descripcion_en', sa.Text(), nullable=False),
    sa.Column('categoria', sa.String(length=20), nullable=False),
    sa.Column('tipo_condicion', sa.String(length=30), nullable=False),
    sa.Column('valor_condicion', sa.Integer(), nullable=False),
    sa.Column('recompensa_puntos', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.CheckConstraint("categoria IN ('RACHA', 'VELOCIDAD', 'PRODUCTIVIDAD', 'CONSTANCIA')", name=op.f('ck_logro_categoria_valida')),
    sa.CheckConstraint("tipo_condicion IN ('DIAS_RACHA', 'PUNTOS_TOTALES', 'TAREAS_A_TIEMPO', 'TAREAS_ANTICIPADAS')", name=op.f('ck_logro_tipo_condicion_valido')),
    sa.CheckConstraint('recompensa_puntos >= 0', name=op.f('ck_logro_recompensa_no_negativa')),
    sa.CheckConstraint('valor_condicion > 0', name=op.f('ck_logro_valor_condicion_positivo')),
    sa.PrimaryKeyConstraint('id_logro', name=op.f('pk_logro')),
    sa.UniqueConstraint('codigo', name=op.f('uq_logro_codigo'))
    )
    op.create_table('dia_racha',
    sa.Column('id_dia_racha', sa.Uuid(), nullable=False),
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False),
    sa.Column('resultado', sa.String(length=20), nullable=False),
    sa.Column('tareas_comprometidas', sa.SmallInteger(), nullable=False),
    sa.Column('tareas_cumplidas_a_tiempo', sa.SmallInteger(), nullable=False),
    sa.Column('racha_previa', sa.Integer(), nullable=False),
    sa.Column('racha_resultante', sa.Integer(), nullable=False),
    sa.Column('fecha_evaluacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("resultado IN ('CUMPLIDO', 'INCUMPLIDO', 'PROTEGIDO', 'SIN_COMPROMISOS')", name=op.f('ck_dia_racha_resultado_valido')),
    sa.CheckConstraint('racha_resultante >= 0 AND racha_previa >= 0', name=op.f('ck_dia_racha_rachas_no_negativas')),
    sa.CheckConstraint('tareas_comprometidas >= 0', name=op.f('ck_dia_racha_comprometidas_no_negativas')),
    sa.CheckConstraint('tareas_cumplidas_a_tiempo BETWEEN 0 AND tareas_comprometidas', name=op.f('ck_dia_racha_cumplidas_validas')),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_dia_racha_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_dia_racha', name=op.f('pk_dia_racha')),
    sa.UniqueConstraint('id_dia_racha', 'id_usuario', name='uq_dia_racha_id_usuario'),
    sa.UniqueConstraint('id_usuario', 'fecha', name='uq_dia_racha_usuario_fecha')
    )
    op.create_index(op.f('ix_dia_racha_id_usuario'), 'dia_racha', ['id_usuario'], unique=False)
    op.create_table('logro_usuario',
    sa.Column('id_logro_usuario', sa.Uuid(), nullable=False),
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('id_logro', sa.Uuid(), nullable=False),
    sa.Column('fecha_desbloqueo', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['id_logro'], ['logro.id_logro'], name=op.f('fk_logro_usuario_id_logro_logro')),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_logro_usuario_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_logro_usuario', name=op.f('pk_logro_usuario')),
    sa.UniqueConstraint('id_usuario', 'id_logro', name='uq_logro_usuario')
    )
    op.create_index(op.f('ix_logro_usuario_id_usuario'), 'logro_usuario', ['id_usuario'], unique=False)
    op.create_table('perfil_gamificacion',
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('puntos_totales', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('nivel', sa.SmallInteger(), server_default=sa.text('1'), nullable=False),
    sa.Column('racha_actual', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('racha_maxima', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('protecciones_disponibles', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('ultima_fecha_evaluada', sa.Date(), nullable=True),
    sa.Column('primer_dia_evaluable', sa.Date(), nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('nivel >= 1', name=op.f('ck_perfil_gamificacion_nivel_valido')),
    sa.CheckConstraint('protecciones_disponibles >= 0', name=op.f('ck_perfil_gamificacion_protecciones_no_negativas')),
    sa.CheckConstraint('puntos_totales >= 0', name=op.f('ck_perfil_gamificacion_puntos_no_negativos')),
    sa.CheckConstraint('racha_actual >= 0', name=op.f('ck_perfil_gamificacion_racha_no_negativa')),
    sa.CheckConstraint('racha_maxima >= racha_actual', name=op.f('ck_perfil_gamificacion_racha_maxima_valida')),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_perfil_gamificacion_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_usuario', name=op.f('pk_perfil_gamificacion'))
    )
    op.create_table('recuperacion_racha',
    sa.Column('id_recuperacion', sa.Uuid(), nullable=False),
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('id_dia_perdido', sa.Uuid(), nullable=False),
    sa.Column('racha_perdida', sa.Integer(), nullable=False),
    sa.Column('tareas_atrasadas', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=False),
    sa.Column('fecha_fin_prevista', sa.Date(), nullable=False),
    sa.Column('estado', sa.String(length=15), server_default='ACTIVA', nullable=False),
    sa.Column('racha_restaurada', sa.Integer(), nullable=True),
    sa.Column('motivo_resolucion', sa.String(length=40), nullable=True),
    sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('fecha_resolucion', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("estado IN ('ACTIVA', 'EXITOSA', 'FALLIDA', 'CANCELADA')", name=op.f('ck_recuperacion_racha_estado_valido')),
    sa.CheckConstraint('fecha_fin_prevista >= fecha_inicio', name=op.f('ck_recuperacion_racha_fin_posterior_a_inicio')),
    sa.CheckConstraint('racha_perdida > 0', name=op.f('ck_recuperacion_racha_racha_perdida_positiva')),
    sa.ForeignKeyConstraint(['id_dia_perdido', 'id_usuario'], ['dia_racha.id_dia_racha', 'dia_racha.id_usuario'], name='fk_recuperacion_dia_del_mismo_usuario'),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_recuperacion_racha_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_recuperacion', name=op.f('pk_recuperacion_racha')),
    sa.UniqueConstraint('id_dia_perdido', name='uq_recuperacion_dia_perdido')
    )
    op.create_index(op.f('ix_recuperacion_racha_id_usuario'), 'recuperacion_racha', ['id_usuario'], unique=False)
    op.create_index('uq_recuperacion_usuario_activa', 'recuperacion_racha', ['id_usuario'], unique=True, postgresql_where=sa.text("estado = 'ACTIVA'"))
    op.create_table('transaccion_gamificacion',
    sa.Column('id_transaccion', sa.Uuid(), nullable=False),
    sa.Column('id_usuario', sa.Uuid(), nullable=False),
    sa.Column('recurso', sa.String(length=20), nullable=False),
    sa.Column('cantidad', sa.Integer(), nullable=False),
    sa.Column('motivo', sa.String(length=40), nullable=False),
    sa.Column('codigo_recompensa', sa.String(length=40), nullable=True),
    sa.Column('id_tarea', sa.Uuid(), nullable=True),
    sa.Column('id_logro', sa.Uuid(), nullable=True),
    sa.Column('id_dia_racha', sa.Uuid(), nullable=True),
    sa.Column('clave_idempotencia', sa.String(length=120), nullable=False),
    sa.Column('fecha', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("motivo IN ('TAREA_A_TIEMPO', 'LOGRO_DESBLOQUEADO', 'RECOMPENSA', 'PROTECCION_USADA')", name=op.f('ck_transaccion_gamificacion_motivo_valido')),
    sa.CheckConstraint("recurso IN ('PUNTOS', 'PROTECCION_RACHA')", name=op.f('ck_transaccion_gamificacion_recurso_valido')),
    sa.CheckConstraint('cantidad <> 0', name=op.f('ck_transaccion_gamificacion_cantidad_no_cero')),
    sa.ForeignKeyConstraint(['id_dia_racha', 'id_usuario'], ['dia_racha.id_dia_racha', 'dia_racha.id_usuario'], name='fk_transaccion_dia_del_mismo_usuario'),
    sa.ForeignKeyConstraint(['id_logro'], ['logro.id_logro'], name=op.f('fk_transaccion_gamificacion_id_logro_logro')),
    sa.ForeignKeyConstraint(['id_tarea', 'id_usuario'], ['tarea.id_tarea', 'tarea.id_usuario'], name='fk_transaccion_tarea_del_mismo_usuario'),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario.id_usuario'], name=op.f('fk_transaccion_gamificacion_id_usuario_usuario')),
    sa.PrimaryKeyConstraint('id_transaccion', name=op.f('pk_transaccion_gamificacion')),
    sa.UniqueConstraint('id_usuario', 'clave_idempotencia', name='uq_transaccion_usuario_clave')
    )
    op.create_index('ix_transaccion_usuario_fecha', 'transaccion_gamificacion', ['id_usuario', 'fecha'], unique=False)
    op.add_column('tarea', sa.Column('fecha_programada', sa.Date(), nullable=True))

    # Catálogo inicial de logros (RF-23). 4 categorías x 3 niveles; textos en español e inglés.
    logro = sa.table(
        'logro',
        sa.column('id_logro', sa.Uuid()), sa.column('codigo', sa.String()), sa.column('nombre', sa.String()),
        sa.column('descripcion', sa.Text()), sa.column('nombre_en', sa.String()), sa.column('descripcion_en', sa.Text()),
        sa.column('categoria', sa.String()), sa.column('tipo_condicion', sa.String()),
        sa.column('valor_condicion', sa.Integer()), sa.column('recompensa_puntos', sa.Integer()),
    )
    op.bulk_insert(logro, [
        {'id_logro': uuid.uuid4(), 'codigo': c, 'nombre': n, 'descripcion': d, 'nombre_en': ne, 'descripcion_en': de,
         'categoria': cat, 'tipo_condicion': tc, 'valor_condicion': v, 'recompensa_puntos': r}
        for c, n, d, ne, de, cat, tc, v, r in LOGROS_INICIALES
    ])


def downgrade() -> None:
    op.drop_column('tarea', 'fecha_programada')
    op.drop_index('ix_transaccion_usuario_fecha', table_name='transaccion_gamificacion')
    op.drop_table('transaccion_gamificacion')
    op.drop_index('uq_recuperacion_usuario_activa', table_name='recuperacion_racha', postgresql_where=sa.text("estado = 'ACTIVA'"))
    op.drop_index(op.f('ix_recuperacion_racha_id_usuario'), table_name='recuperacion_racha')
    op.drop_table('recuperacion_racha')
    op.drop_table('perfil_gamificacion')
    op.drop_index(op.f('ix_logro_usuario_id_usuario'), table_name='logro_usuario')
    op.drop_table('logro_usuario')
    op.drop_index(op.f('ix_dia_racha_id_usuario'), table_name='dia_racha')
    op.drop_table('dia_racha')
    op.drop_table('logro')

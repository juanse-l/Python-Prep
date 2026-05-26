"""
Migration 0008 — Módulo Padres/Tutores
Depende de la última migración del proyecto: 0007_conversacion_ia_publicacion_foro

Agrega:
  - Nuevos choices al campo Perfil.rol  (padre, tutor)
  - VinculoPadreTutor       – Relación padre ↔ hijo con privacidad configurable
  - NotificacionPadre       – Alertas para padres
  - CitaPadre               – Citas padre-psicóloga / padre-hijo-psicóloga
  - MensajePadre            – Mensajería padre ↔ psicóloga
  - ForoTemapadres          – Foro exclusivo para padres (temas)
  - ForoRespuestaPadres     – Respuestas del foro de padres
  - ReaccionForoPadres      – Reacciones del foro de padres
  - RecomendacionPadre      – Recomendaciones inteligentes
  - ReportePadre            – Reportes emocionales resumidos para padres
  - ConfigPrivacidadPadre   – Control de privacidad por perfil de hijo
  - LogActividadPadre       – Auditoría de acciones del padre
"""
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0007_conversacion_ia_publicacion_foro'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Ampliar choices de Perfil.rol ────────────────────────────────
        migrations.AlterField(
            model_name='perfil',
            name='rol',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('psicologo', 'Psicólogo/a'),
                    ('estudiante', 'Estudiante'),
                    ('padre', 'Padre/Madre'),
                    ('tutor', 'Tutor/a Legal'),
                ],
                default='psicologo',
            ),
        ),

        # ── 2. VinculoPadreTutor ─────────────────────────────────────────────
        migrations.CreateModel(
            name='VinculoPadreTutor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('padre', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vinculos_hijos',
                    verbose_name='Padre/Tutor',
                )),
                ('hijo', models.ForeignKey(
                    'psicoasis.Estudiante',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vinculos_padres',
                    verbose_name='Estudiante/Hijo',
                )),
                ('tipo_relacion', models.CharField(
                    max_length=20,
                    choices=[
                        ('padre', 'Padre'),
                        ('madre', 'Madre'),
                        ('tutor', 'Tutor/a Legal'),
                        ('abuelo', 'Abuelo/a'),
                        ('otro', 'Otro Acudiente'),
                    ],
                    default='padre',
                )),
                ('activo', models.BooleanField(default=True)),
                ('es_principal', models.BooleanField(
                    default=False,
                    help_text='Acudiente principal (recibe todas las alertas)',
                )),
                ('puede_ver_emociones', models.BooleanField(default=True)),
                ('puede_ver_citas', models.BooleanField(default=True)),
                ('puede_agendar_citas', models.BooleanField(default=True)),
                ('puede_enviar_mensajes', models.BooleanField(default=True)),
                ('fecha_vinculo', models.DateTimeField(default=django.utils.timezone.now)),
                ('vinculado_por', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='vinculos_creados',
                    verbose_name='Registrado por (psicóloga)',
                )),
            ],
            options={
                'verbose_name': 'Vínculo Padre-Hijo',
                'verbose_name_plural': 'Vínculos Padre-Hijo',
                'unique_together': {('padre', 'hijo')},
                'ordering': ['-es_principal', 'hijo__apellido'],
            },
        ),

        # ── 3. ConfigPrivacidadPadre ─────────────────────────────────────────
        migrations.CreateModel(
            name='ConfigPrivacidadPadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('vinculo', models.OneToOneField(
                    'psicoasis.VinculoPadreTutor',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='privacidad',
                )),
                ('mostrar_estado_emocional', models.BooleanField(default=True)),
                ('mostrar_historial_emocional', models.BooleanField(default=True)),
                ('mostrar_tendencias', models.BooleanField(default=True)),
                ('mostrar_alertas_riesgo', models.BooleanField(default=True)),
                ('mostrar_citas', models.BooleanField(default=True)),
                ('mostrar_informes_resumidos', models.BooleanField(default=False)),
                ('mostrar_notas_privadas', models.BooleanField(default=False)),
                ('nivel_detalle', models.CharField(
                    max_length=20,
                    choices=[
                        ('basico', 'Básico — solo estado general'),
                        ('intermedio', 'Intermedio — estado + tendencias'),
                        ('completo', 'Completo — todo lo permitido'),
                    ],
                    default='intermedio',
                )),
                ('configurado_por', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='configs_privacidad_creadas',
                )),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Configuración de Privacidad'},
        ),

        # ── 4. NotificacionPadre ─────────────────────────────────────────────
        migrations.CreateModel(
            name='NotificacionPadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('padre', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notificaciones_padre',
                )),
                ('hijo', models.ForeignKey(
                    'psicoasis.Estudiante',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notificaciones_padres',
                    null=True, blank=True,
                )),
                ('tipo', models.CharField(
                    max_length=40,
                    choices=[
                        ('emocion_critica', '🚨 Estado emocional crítico'),
                        ('riesgo_alto', '⚠️ Riesgo emocional alto'),
                        ('cambio_brusco', '📊 Cambio emocional brusco'),
                        ('cita_programada', '📅 Cita programada'),
                        ('cita_cancelada', '❌ Cita cancelada'),
                        ('cita_recordatorio', '🔔 Recordatorio de cita'),
                        ('observacion_psicologa', '💬 Observación de la psicóloga'),
                        ('inasistencia', '📋 Inasistencia a actividad'),
                        ('mensaje_nuevo', '✉️ Nuevo mensaje'),
                        ('informe_disponible', '📄 Informe disponible'),
                        ('sistema', 'ℹ️ Sistema'),
                    ],
                    default='sistema',
                )),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('leida', models.BooleanField(default=False)),
                ('prioridad', models.CharField(
                    max_length=10,
                    choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')],
                    default='media',
                )),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('datos_extra', models.JSONField(default=dict, blank=True)),
            ],
            options={'ordering': ['-fecha'], 'verbose_name': 'Notificación para Padre'},
        ),

        # ── 5. CitaPadre ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='CitaPadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('padre', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='citas_como_padre',
                )),
                ('hijo', models.ForeignKey(
                    'psicoasis.Estudiante',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='citas_con_padre',
                    null=True, blank=True,
                    help_text='Requerido solo para citas Padre+Hijo+Psicóloga',
                )),
                ('psicologo', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='citas_con_padres',
                )),
                ('tipo_cita', models.CharField(
                    max_length=20,
                    choices=[
                        ('padre_psicologo', '👤 Padre + Psicóloga'),
                        ('familiar', '👨‍👩‍👧 Padre + Hijo + Psicóloga'),
                    ],
                    default='padre_psicologo',
                )),
                ('motivo', models.CharField(
                    max_length=50,
                    choices=[
                        ('crianza', 'Consulta de crianza'),
                        ('conducta', 'Problemas de conducta'),
                        ('familia', 'Problemas familiares'),
                        ('orientacion', 'Orientación general'),
                        ('seguimiento_emocional', 'Seguimiento emocional'),
                        ('intervencion_familiar', 'Intervención familiar'),
                        ('mediacion', 'Mediación'),
                        ('acompanamiento', 'Proceso de acompañamiento'),
                        ('otro', 'Otro'),
                    ],
                    default='orientacion',
                )),
                ('descripcion_motivo', models.TextField(blank=True)),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('estado', models.CharField(
                    max_length=20,
                    choices=[
                        ('pendiente', 'Pendiente'),
                        ('confirmada', 'Confirmada'),
                        ('realizada', 'Realizada'),
                        ('cancelada', 'Cancelada'),
                        ('reagendada', 'Reagendada'),
                    ],
                    default='pendiente',
                )),
                ('notas_psicologo', models.TextField(blank=True, verbose_name='Notas de la psicóloga')),
                ('recordatorio_enviado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['fecha', 'hora'], 'verbose_name': 'Cita de Padre'},
        ),

        # ── 6. MensajePadre ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='MensajePadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('remitente', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mensajes_padre_enviados',
                )),
                ('destinatario', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mensajes_padre_recibidos',
                )),
                ('hijo_referencia', models.ForeignKey(
                    'psicoasis.Estudiante',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='mensajes_con_padre',
                    help_text='Hijo sobre quien se habla (opcional)',
                )),
                ('contenido', models.TextField()),
                ('archivo_adjunto', models.FileField(
                    upload_to='mensajes_padres/', blank=True, null=True,
                )),
                ('estado', models.CharField(
                    max_length=20,
                    choices=[('enviado', 'Enviado'), ('leido', 'Leído')],
                    default='enviado',
                )),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['fecha'], 'verbose_name': 'Mensaje Padre-Psicóloga'},
        ),

        # ── 7. ForoTemaPadres ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='ForoTemaPadres',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=300)),
                ('descripcion', models.TextField(blank=True)),
                ('categoria', models.CharField(
                    max_length=30,
                    choices=[
                        ('crianza', '👨‍👩‍👧 Crianza'),
                        ('emociones', '💚 Manejo emocional'),
                        ('conducta', '🧠 Conducta adolescente'),
                        ('comunicacion', '💬 Comunicación familiar'),
                        ('conflictos', '🤝 Resolución de conflictos'),
                        ('educacion_emocional', '📚 Educación emocional'),
                        ('tecnologia', '📱 Uso saludable de tecnología'),
                        ('ansiedad', '😰 Ansiedad y estrés'),
                        ('autoestima', '⭐ Autoestima en hijos'),
                        ('general', '🌿 General'),
                    ],
                    default='general',
                )),
                ('autor', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='temas_foro_padres',
                )),
                ('es_anonimo', models.BooleanField(default=False)),
                ('activo', models.BooleanField(default=True)),
                ('fijado', models.BooleanField(default=False)),
                ('destacado', models.BooleanField(default=False)),
                ('moderado', models.BooleanField(default=False)),
                ('reportado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-fijado', '-destacado', '-fecha_creacion'],
                'verbose_name': 'Tema Foro Padres',
            },
        ),

        # ── 8. ForoRespuestaPadres ────────────────────────────────────────────
        migrations.CreateModel(
            name='ForoRespuestaPadres',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tema', models.ForeignKey(
                    'psicoasis.ForoTemaPadres',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='respuestas',
                )),
                ('autor', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='respuestas_foro_padres',
                )),
                ('contenido', models.TextField()),
                ('es_anonimo', models.BooleanField(default=False)),
                ('moderado', models.BooleanField(default=False)),
                ('reportado', models.BooleanField(default=False)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['fecha'], 'verbose_name': 'Respuesta Foro Padres'},
        ),

        # ── 9. ReaccionForoPadres ─────────────────────────────────────────────
        migrations.CreateModel(
            name='ReaccionForoPadres',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('usuario', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reacciones_foro_padres',
                )),
                ('tema', models.ForeignKey(
                    'psicoasis.ForoTemaPadres',
                    on_delete=django.db.models.deletion.CASCADE,
                    null=True, blank=True,
                    related_name='reacciones',
                )),
                ('respuesta', models.ForeignKey(
                    'psicoasis.ForoRespuestaPadres',
                    on_delete=django.db.models.deletion.CASCADE,
                    null=True, blank=True,
                    related_name='reacciones',
                )),
                ('tipo', models.CharField(
                    max_length=20,
                    choices=[
                        ('me_ayudo', '👍 Me ayudó'),
                        ('gracias', '❤️ Gracias'),
                        ('importante', '⭐ Importante'),
                    ],
                    default='me_ayudo',
                )),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'verbose_name': 'Reacción Foro Padres'},
        ),

        # ── 10. RecomendacionPadre ────────────────────────────────────────────
        migrations.CreateModel(
            name='RecomendacionPadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('padre', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recomendaciones_padre',
                )),
                ('hijo', models.ForeignKey(
                    'psicoasis.Estudiante',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recomendaciones_para_padre',
                    null=True, blank=True,
                )),
                ('tipo', models.CharField(
                    max_length=30,
                    choices=[
                        ('articulo', '📖 Artículo'),
                        ('consejo', '💡 Consejo de crianza'),
                        ('estrategia', '🛠️ Estrategia'),
                        ('tecnica', '🧘 Técnica de comunicación'),
                        ('recurso', '📎 Recurso externo'),
                        ('actividad', '🎯 Actividad sugerida'),
                    ],
                    default='consejo',
                )),
                ('titulo', models.CharField(max_length=300)),
                ('contenido', models.TextField()),
                ('url_recurso', models.URLField(blank=True)),
                ('trigger_emocion', models.CharField(
                    max_length=30, blank=True,
                    help_text='Emoción del hijo que originó esta recomendación',
                )),
                ('generada_por', models.CharField(
                    max_length=20,
                    choices=[('psicologa', 'Psicóloga'), ('sistema', 'Sistema automático')],
                    default='psicologa',
                )),
                ('activo', models.BooleanField(default=True)),
                ('leida', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Recomendación para Padre'},
        ),

        # ── 11. LogActividadPadre ─────────────────────────────────────────────
        migrations.CreateModel(
            name='LogActividadPadre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('padre', models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs_actividad',
                )),
                ('accion', models.CharField(
                    max_length=50,
                    choices=[
                        ('login', 'Inicio de sesión'),
                        ('ver_dashboard', 'Ver dashboard'),
                        ('ver_emociones_hijo', 'Ver emociones del hijo'),
                        ('ver_citas', 'Ver citas'),
                        ('crear_cita', 'Crear cita'),
                        ('cancelar_cita', 'Cancelar cita'),
                        ('enviar_mensaje', 'Enviar mensaje'),
                        ('ver_reporte', 'Ver reporte'),
                        ('foro_crear_tema', 'Crear tema en foro'),
                        ('foro_comentar', 'Comentar en foro'),
                    ],
                )),
                ('descripcion', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['-fecha'], 'verbose_name': 'Log de Actividad del Padre'},
        ),
    ]

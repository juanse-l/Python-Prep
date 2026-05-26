from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0008_modulo_padres'),
    ]

    operations = [
        # Agregar rol 'profesor' al Perfil
        migrations.AlterField(
            model_name='perfil',
            name='rol',
            field=models.CharField(
                choices=[
                    ('psicologo', 'Psicólogo/a'),
                    ('estudiante', 'Estudiante'),
                    ('padre', 'Padre de familia'),
                    ('tutor', 'Tutor/Acudiente'),
                    ('profesor', 'Profesor/a'),
                ],
                default='psicologo',
                max_length=20,
            ),
        ),

        # PerfilProfesor
        migrations.CreateModel(
            name='PerfilProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('acepta_acompanamiento', models.BooleanField(default=True)),
                ('fecha_registro', models.DateTimeField(default=django.utils.timezone.now)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_profesor', to='auth.user')),
                ('docente', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario_vinculado', to='psicoasis.docente')),
            ],
            options={'verbose_name': 'Perfil de Profesor', 'verbose_name_plural': 'Perfiles de Profesores'},
        ),

        # AlertaEstudianteProfesor
        migrations.CreateModel(
            name='AlertaEstudianteProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('categoria', models.CharField(choices=[
                    ('rendimiento', '📉 Bajo rendimiento / desmotivación'),
                    ('conducta', '⚠️ Cambio de conducta'),
                    ('ausentismo', '📅 Ausentismo o evasión'),
                    ('convivencia', '🤝 Problema de convivencia / bullying'),
                    ('emocional', '💔 Señales emocionales preocupantes'),
                    ('familia', '🏠 Situación familiar'),
                    ('autolesion', '🚨 Posible autolesión / riesgo'),
                    ('otro', '📋 Otro'),
                ], max_length=30)),
                ('urgencia', models.CharField(choices=[
                    ('informativa', '🟡 Informativa'),
                    ('moderada', '🟠 Moderada — requiere atención pronto'),
                    ('urgente', '🔴 Urgente — atención prioritaria'),
                ], default='informativa', max_length=20)),
                ('descripcion', models.TextField()),
                ('conductas_observadas', models.TextField(blank=True)),
                ('estado', models.CharField(choices=[
                    ('pendiente', 'Pendiente'),
                    ('en_revision', 'En revisión'),
                    ('atendida', 'Atendida'),
                    ('derivada', 'Derivada a caso'),
                ], default='pendiente', max_length=20)),
                ('respuesta_psicologo', models.TextField(blank=True)),
                ('fecha_respuesta', models.DateTimeField(blank=True, null=True)),
                ('es_confidencial', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_enviadas_prof', to='auth.user')),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_docentes', to='psicoasis.estudiante')),
                ('caso_generado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='origen_alerta_docente', to='psicoasis.caso')),
            ],
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Alerta Docente'},
        ),

        # CitaProfesor
        migrations.CreateModel(
            name='CitaProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[
                    ('bienestar_propio', '💆 Bienestar / apoyo personal'),
                    ('orientacion_caso', '🎓 Orientación sobre un estudiante'),
                    ('estrategias_aula', '📚 Estrategias pedagógicas y de aula'),
                    ('coordinacion', '🤝 Coordinación institucional'),
                    ('otro', '📋 Otro'),
                ], default='bienestar_propio', max_length=30)),
                ('motivo_detalle', models.TextField()),
                ('fecha_propuesta', models.DateField(blank=True, null=True)),
                ('hora_propuesta', models.TimeField(blank=True, null=True)),
                ('fecha_confirmada', models.DateField(blank=True, null=True)),
                ('hora_confirmada', models.TimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[
                    ('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'),
                    ('realizada', 'Realizada'), ('cancelada', 'Cancelada'), ('reagendada', 'Reagendada'),
                ], default='pendiente', max_length=20)),
                ('notas_psicologo', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas_profesor', to='auth.user')),
                ('estudiante_relacionado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citas_prof_relacionadas', to='psicoasis.estudiante')),
            ],
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Cita Profesor'},
        ),

        # MensajeProfesor
        migrations.CreateModel(
            name='MensajeProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('contenido', models.TextField()),
                ('leido', models.BooleanField(default=False)),
                ('archivo_adjunto', models.FileField(blank=True, null=True, upload_to='mensajes_profesores/')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('remitente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_prof_enviados', to='auth.user')),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_prof_recibidos', to='auth.user')),
                ('hilo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='respuestas', to='psicoasis.mensajeprofesor')),
            ],
            options={'ordering': ['fecha'], 'verbose_name': 'Mensaje Profesor'},
        ),

        # NotificacionProfesor
        migrations.CreateModel(
            name='NotificacionProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[
                    ('alerta_respondida', '✅ Tu alerta fue respondida'),
                    ('cita_confirmada', '📅 Cita confirmada'),
                    ('cita_cancelada', '❌ Cita cancelada'),
                    ('mensaje_nuevo', '💬 Mensaje nuevo'),
                    ('recurso_compartido', '📎 Recurso compartido contigo'),
                    ('caso_derivado', '🗂️ Estudiante derivado a caso'),
                    ('sistema', '🔔 Sistema'),
                ], default='sistema', max_length=30)),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('leida', models.BooleanField(default=False)),
                ('prioridad', models.CharField(choices=[('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')], default='media', max_length=10)),
                ('url_accion', models.CharField(blank=True, max_length=200)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones_profesor', to='auth.user')),
            ],
            options={'ordering': ['-fecha'], 'verbose_name': 'Notificación Profesor'},
        ),

        # RecursoProfesor
        migrations.CreateModel(
            name='RecursoProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=300)),
                ('descripcion', models.TextField()),
                ('categoria', models.CharField(choices=[
                    ('manejo_aula', '🏫 Manejo de aula y convivencia'),
                    ('deteccion_temprana', '🔍 Detección temprana de señales'),
                    ('estres_burnout', '🧘 Manejo del estrés y burnout docente'),
                    ('inclusion', '♿ Educación inclusiva'),
                    ('comunicacion', '🗣️ Comunicación asertiva'),
                    ('crisis', '🚨 Protocolos de crisis'),
                    ('aprendizaje', '📚 Dificultades de aprendizaje'),
                    ('general', '🌿 General'),
                ], default='general', max_length=30)),
                ('tipo', models.CharField(choices=[
                    ('guia', '📄 Guía / Documento'), ('estrategia', '🛠️ Estrategia práctica'),
                    ('protocolo', '📋 Protocolo'), ('video', '🎥 Video / Webinar'), ('infografia', '🖼️ Infografía'),
                ], default='guia', max_length=20)),
                ('contenido', models.TextField(blank=True)),
                ('url_externo', models.URLField(blank=True)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='recursos_profesores/')),
                ('para_todos', models.BooleanField(default=True)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recursos_creados_prof', to='auth.user')),
                ('profesores_especificos', models.ManyToManyField(blank=True, related_name='recursos_asignados', to='auth.user')),
            ],
            options={'ordering': ['-fecha_creacion'], 'verbose_name': 'Recurso Profesor'},
        ),

        # AutoevaluacionProfesor
        migrations.CreateModel(
            name='AutoevaluacionProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('bienestar', models.CharField(choices=[
                    ('excelente', '😄 Excelente'), ('bien', '🙂 Bien'),
                    ('regular', '😐 Regular'), ('agotado', '😔 Agotado/a'), ('en_crisis', '😢 En crisis'),
                ], max_length=20)),
                ('carga_laboral', models.CharField(choices=[
                    ('manejable', 'Manejable'), ('alta', 'Alta'), ('muy_alta', 'Muy alta — me desborda'),
                ], default='manejable', max_length=20)),
                ('nota_privada', models.TextField(blank=True)),
                ('solicita_atencion', models.BooleanField(default=False)),
                ('semana', models.DateField(default=django.utils.timezone.now)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='autoevaluaciones_profesor', to='auth.user')),
            ],
            options={'ordering': ['-semana'], 'unique_together': {('profesor', 'semana')}},
        ),

        # LogActividadProfesor
        migrations.CreateModel(
            name='LogActividadProfesor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('accion', models.CharField(choices=[
                    ('login', 'Inicio de sesión'), ('alerta_enviada', 'Alerta enviada'),
                    ('cita_solicitada', 'Cita solicitada'), ('mensaje_enviado', 'Mensaje enviado'),
                    ('recurso_visto', 'Recurso consultado'), ('autoevaluacion', 'Autoevaluación completada'),
                ], max_length=30)),
                ('descripcion', models.TextField(blank=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs_actividad_profesor', to='auth.user')),
            ],
            options={'ordering': ['-fecha'], 'verbose_name': 'Log Actividad Profesor'},
        ),
    ]

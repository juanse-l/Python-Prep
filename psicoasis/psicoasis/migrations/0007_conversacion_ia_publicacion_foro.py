from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0006_perfil_rol_mensajes_autoevaluacion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversacionIA',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('pregunta', models.TextField()),
                ('respuesta', models.TextField()),
                ('tema_detectado', models.CharField(blank=True, max_length=100)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversaciones_ia', to=settings.AUTH_USER_MODEL)),
                ('cita_sugerida', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='origen_ia', to='psicoasis.citapublica')),
            ],
            options={'ordering': ['fecha']},
        ),
        migrations.CreateModel(
            name='PublicacionForo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('titulo', models.CharField(max_length=300)),
                ('contenido', models.TextField()),
                ('categoria', models.CharField(choices=[('ansiedad','😰 Manejo de ansiedad'),('emociones','💚 Gestión emocional'),('autoestima','⭐ Autoestima'),('convivencia','🤝 Convivencia y relaciones'),('estudio','📚 Técnicas de estudio'),('duelo','🕊️ Afrontamiento y duelo'),('motivacion','🚀 Motivación'),('general','🌿 General')], default='general', max_length=30)),
                ('tipo', models.CharField(choices=[('estrategia','🛠️ Estrategia'),('mensaje','💌 Mensaje'),('recurso','📎 Recurso'),('reflexion','🌀 Reflexión')], default='mensaje', max_length=20)),
                ('fijado', models.BooleanField(default=False)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('imagen_url', models.URLField(blank=True)),
                ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='publicaciones_foro', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-fijado', '-fecha_creacion']},
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('cita_publica', 'Nueva cita desde formulario público'), ('sistema', 'Sistema')], default='sistema', max_length=30)),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('leida', models.BooleanField(default=False)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('nombre_solicitante', models.CharField(blank=True, max_length=200)),
                ('email_solicitante', models.EmailField(blank=True)),
                ('telefono_solicitante', models.CharField(blank=True, max_length=30)),
                ('rol_solicitante', models.CharField(blank=True, max_length=30)),
                ('motivo_consulta', models.TextField(blank=True)),
                ('fecha_solicitada', models.DateField(blank=True, null=True)),
                ('hora_solicitada', models.TimeField(blank=True, null=True)),
            ],
            options={'ordering': ['-fecha']},
        ),
        migrations.CreateModel(
            name='CitaPublica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True)),
                ('telefono', models.CharField(blank=True, max_length=30)),
                ('rol', models.CharField(choices=[('estudiante', 'Estudiante'), ('docente', 'Docente'), ('acudiente', 'Acudiente / Padre de familia'), ('otro', 'Otro')], default='estudiante', max_length=20)),
                ('motivo', models.TextField()),
                ('fecha_preferida', models.DateField(blank=True, null=True)),
                ('hora_preferida', models.TimeField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('atendida', 'Atendida'), ('cancelada', 'Cancelada')], default='pendiente', max_length=20)),
                ('fecha_solicitud', models.DateTimeField(default=django.utils.timezone.now)),
                ('notas_internas', models.TextField(blank=True)),
            ],
            options={'ordering': ['-fecha_solicitud']},
        ),
        migrations.CreateModel(
            name='Docente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('apellido', models.CharField(max_length=200)),
                ('area', models.CharField(choices=[('matematicas', 'Matemáticas'), ('ciencias', 'Ciencias Naturales'), ('sociales', 'Ciencias Sociales'), ('lenguaje', 'Lenguaje y Literatura'), ('ingles', 'Inglés'), ('educacion_fisica', 'Educación Física'), ('artes', 'Artes'), ('tecnologia', 'Tecnología e Informática'), ('religion', 'Religión / Ética'), ('orientacion', 'Orientación Escolar'), ('coordinacion', 'Coordinación'), ('otro', 'Otro')], default='otro', max_length=30)),
                ('email', models.EmailField(blank=True, null=True)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('grados_a_cargo', models.CharField(blank=True, max_length=200)),
                ('fecha_registro', models.DateTimeField(default=django.utils.timezone.now)),
                ('activo', models.BooleanField(default=True)),
                ('notas_generales', models.TextField(blank=True)),
            ],
            options={'ordering': ['apellido', 'nombre']},
        ),
        migrations.CreateModel(
            name='SeguimientoDocente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.CharField(choices=[('estres_laboral', 'Estrés Laboral'), ('burnout', 'Burnout / Agotamiento'), ('conflicto_estudiantes', 'Conflicto con Estudiantes'), ('conflicto_colegas', 'Conflicto con Colegas'), ('dificultades_personales', 'Dificultades Personales'), ('orientacion_pedagogica', 'Orientación Pedagógica'), ('otro', 'Otro')], max_length=30)),
                ('descripcion', models.TextField()),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('cerrado', 'Cerrado')], default='activo', max_length=20)),
                ('fecha_apertura', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('docente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seguimientos', to='psicoasis.docente')),
                ('psicologo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-fecha_apertura']},
        ),
        migrations.CreateModel(
            name='ForoTema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=300)),
                ('descripcion', models.TextField(blank=True)),
                ('categoria', models.CharField(choices=[('general', 'General'), ('estudiantes', 'Para Estudiantes'), ('docentes', 'Para Docentes'), ('familias', 'Para Familias'), ('bienestar', 'Bienestar Emocional'), ('academico', 'Rendimiento Académico')], default='general', max_length=30)),
                ('activo', models.BooleanField(default=True)),
                ('fijado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-fijado', '-fecha_creacion']},
        ),
        migrations.CreateModel(
            name='ForoRespuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.TextField()),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('tema', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='psicoasis.forotema')),
                ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['fecha']},
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Estudiante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('apellido', models.CharField(max_length=200)),
                ('grado', models.CharField(choices=[('1A', '1A'), ('1B', '1B'), ('2A', '2A'), ('2B', '2B'), ('3A', '3A'), ('3B', '3B'), ('4A', '4A'), ('4B', '4B'), ('5A', '5A'), ('5B', '5B'), ('6A', '6A'), ('6B', '6B'), ('7A', '7A'), ('7B', '7B'), ('8A', '8A'), ('8B', '8B'), ('9A', '9A'), ('9B', '9B'), ('10A', '10A'), ('10B', '10B'), ('11A', '11A'), ('11B', '11B')], max_length=5)),
                ('edad', models.PositiveIntegerField()),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('telefono_acudiente', models.CharField(blank=True, max_length=20)),
                ('nombre_acudiente', models.CharField(blank=True, max_length=200)),
                ('fecha_registro', models.DateTimeField(default=django.utils.timezone.now)),
                ('activo', models.BooleanField(default=True)),
                ('notas_generales', models.TextField(blank=True)),
            ],
            options={'ordering': ['apellido', 'nombre']},
        ),
        migrations.CreateModel(
            name='Caso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motivo', models.CharField(choices=[('ansiedad_academica', 'Ansiedad Académica'), ('problemas_familiares', 'Problemas Familiares'), ('conflicto_compañeros', 'Conflicto con Compañeros'), ('baja_autoestima', 'Baja Autoestima'), ('dificultades_aprendizaje', 'Dificultades de Aprendizaje'), ('conducta', 'Problemas de Conducta'), ('organizacion_escolar', 'Organización Escolar'), ('dificultades_familiares', 'Dificultades Familiares'), ('otro', 'Otro')], max_length=50)),
                ('descripcion', models.TextField()),
                ('tipo_atencion', models.CharField(choices=[('urgente', 'Urgente'), ('prioritario', 'Prioritario'), ('regular', 'Regular'), ('seguimiento', 'Seguimiento')], default='regular', max_length=20)),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('cerrado', 'Cerrado'), ('suspendido', 'Suspendido')], default='activo', max_length=20)),
                ('fecha_apertura', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='casos', to='psicoasis.estudiante')),
                ('psicologo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='casos', to='auth.user')),
            ],
            options={'ordering': ['-fecha_apertura']},
        ),
        migrations.CreateModel(
            name='Reunion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('motivo', models.CharField(max_length=200)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('realizada', 'Realizada'), ('cancelada', 'Cancelada')], default='pendiente', max_length=20)),
                ('notas', models.TextField(blank=True)),
                ('tipo_atencion', models.CharField(choices=[('urgente', 'Urgente'), ('prioritario', 'Prioritario'), ('regular', 'Regular'), ('seguimiento', 'Seguimiento')], default='regular', max_length=20)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('caso', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reuniones', to='psicoasis.caso')),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reuniones', to='psicoasis.estudiante')),
                ('psicologo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'ordering': ['fecha', 'hora']},
        ),
        migrations.CreateModel(
            name='Informe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=300)),
                ('tipo', models.CharField(choices=[('individual', 'Individual'), ('grupal', 'Grupal'), ('mensual', 'Mensual')], default='individual', max_length=20)),
                ('contenido', models.TextField()),
                ('recomendaciones', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('estudiante', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='psicoasis.estudiante')),
                ('psicologo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'ordering': ['-fecha_creacion']},
        ),
        migrations.CreateModel(
            name='RecursoWellness',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=300)),
                ('descripcion', models.TextField()),
                ('categoria', models.CharField(choices=[('herramienta_autocuidado', 'Herramientas de Autocuidado'), ('biblioteca_emocional', 'Biblioteca Emocional'), ('recursos_multimedia', 'Recursos Multimedia'), ('mini_planes', 'Mini Planes de Autocuidado'), ('vlog', 'Vlog Salud Mental'), ('foros', 'Foros y Espacios')], max_length=50)),
                ('tipo_media', models.CharField(choices=[('texto', 'Texto'), ('video', 'Video'), ('audio', 'Audio'), ('pdf', 'PDF')], default='texto', max_length=20)),
                ('url_media', models.URLField(blank=True)),
                ('contenido', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={'ordering': ['-fecha_creacion']},
        ),
        migrations.CreateModel(
            name='Perfil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('foto', models.ImageField(blank=True, null=True, upload_to='perfiles/')),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('cargo', models.CharField(default='Psicóloga Escolar', max_length=100)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to='auth.user')),
            ],
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0005_reunion_aplazada'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='perfil',
            name='rol',
            field=models.CharField(choices=[('psicologo', 'Psicólogo/a'), ('estudiante', 'Estudiante')], default='psicologo', max_length=20),
        ),
        migrations.AddField(
            model_name='perfil',
            name='estudiante_vinculado',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario_vinculado', to='psicoasis.estudiante'),
        ),
        migrations.AlterField(
            model_name='perfil',
            name='cargo',
            field=models.CharField(default='Psicólogo/a Escolar', max_length=100),
        ),
        migrations.CreateModel(
            name='MensajeEstudiante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('contenido', models.TextField()),
                ('estado', models.CharField(choices=[('enviado', 'Enviado'), ('leido', 'Leído')], default='enviado', max_length=20)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('es_anonimo', models.BooleanField(default=False)),
                ('remitente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_enviados', to=settings.AUTH_USER_MODEL)),
                ('destinatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_recibidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['fecha']},
        ),
        migrations.CreateModel(
            name='AutoevaluacionEstudiante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('emocion', models.CharField(choices=[('muy_bien', '😄 Muy bien'), ('bien', '🙂 Bien'), ('regular', '😐 Regular'), ('mal', '😔 Mal'), ('muy_mal', '😢 Muy mal')], max_length=20)),
                ('nota_privada', models.TextField(blank=True)),
                ('fecha', models.DateField(default=django.utils.timezone.now)),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='autoevaluaciones', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-fecha'], 'unique_together': {('estudiante', 'fecha')}},
        ),
    ]

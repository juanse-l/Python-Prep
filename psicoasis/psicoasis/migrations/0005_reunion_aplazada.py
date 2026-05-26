from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('psicoasis', '0004_add_personal_aseo'),
    ]

    operations = [
        migrations.AddField(
            model_name='reunion',
            name='fecha_aplazada',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reunion',
            name='hora_aplazada',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='reunion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('confirmada', 'Confirmada'),
                    ('realizada', 'Realizada'),
                    ('cancelada', 'Cancelada'),
                    ('aplazada', 'Aplazada'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
    ]

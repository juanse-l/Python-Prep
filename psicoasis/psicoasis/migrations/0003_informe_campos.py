from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('psicoasis', '0002_new_models'),
    ]

    operations = [
        migrations.AddField(model_name='informe', name='motivo_consulta', field=models.TextField(blank=True, verbose_name='Motivo de consulta')),
        migrations.AddField(model_name='informe', name='antecedentes', field=models.TextField(blank=True, verbose_name='Antecedentes relevantes')),
        migrations.AddField(model_name='informe', name='situacion_familiar', field=models.TextField(blank=True, verbose_name='Situación familiar')),
        migrations.AddField(model_name='informe', name='descripcion_conducta', field=models.TextField(blank=True, verbose_name='Descripción de la conducta observada')),
        migrations.AddField(model_name='informe', name='estado_emocional', field=models.TextField(blank=True, verbose_name='Estado emocional')),
        migrations.AddField(model_name='informe', name='relaciones_sociales', field=models.TextField(blank=True, verbose_name='Relaciones sociales y pares')),
        migrations.AddField(model_name='informe', name='rendimiento_academico', field=models.TextField(blank=True, verbose_name='Rendimiento académico')),
        migrations.AddField(model_name='informe', name='fortalezas', field=models.TextField(blank=True, verbose_name='Fortalezas y recursos personales')),
        migrations.AddField(model_name='informe', name='factores_riesgo', field=models.TextField(blank=True, verbose_name='Factores de riesgo identificados')),
        migrations.AddField(model_name='informe', name='nivel_riesgo', field=models.CharField(blank=True, choices=[('', 'Sin clasificar'), ('bajo', 'Bajo'), ('medio', 'Medio'), ('alto', 'Alto'), ('critico', 'Crítico — requiere intervención inmediata')], default='', max_length=20)),
        migrations.AddField(model_name='informe', name='plan_intervencion', field=models.TextField(blank=True, verbose_name='Plan de intervención')),
        migrations.AddField(model_name='informe', name='acuerdos', field=models.TextField(blank=True, verbose_name='Acuerdos y compromisos')),
        migrations.AddField(model_name='informe', name='proxima_sesion', field=models.TextField(blank=True, verbose_name='Próxima sesión / seguimiento')),
        migrations.AddField(model_name='informe', name='requiere_remision', field=models.BooleanField(default=False, verbose_name='Requiere remisión externa')),
        migrations.AddField(model_name='informe', name='entidad_remision', field=models.CharField(blank=True, max_length=200, verbose_name='Entidad de remisión')),
        migrations.AddField(model_name='informe', name='confidencial', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='informe', name='fecha_sesion', field=models.DateField(blank=True, null=True, verbose_name='Fecha de la sesión')),
        migrations.AlterField(model_name='informe', name='tipo', field=models.CharField(choices=[('individual', 'Individual'), ('grupal', 'Grupal'), ('mensual', 'Mensual'), ('remision', 'Remisión'), ('seguimiento', 'Seguimiento'), ('valoracion', 'Valoración Psicológica')], default='individual', max_length=20)),
    ]

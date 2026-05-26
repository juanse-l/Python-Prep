"""
psicoasis/signals_profesores.py
Conectar en PsicoasisConfig.ready():
    import psicoasis.signals_profesores  # noqa
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AlertaEstudianteProfesor, CitaProfesor, AutoevaluacionProfesor
from .services_profesores import (
    generar_alerta_bienestar_docente,
    notificar_cambio_cita_profesor,
    notificar_psicologo_alerta,
)
from django.contrib.auth.models import User


# ── Alerta docente creada ──────────────────────────────────────────────────────

@receiver(post_save, sender=AlertaEstudianteProfesor)
def on_alerta_docente_guardada(sender, instance, created, **kwargs):
    if created:
        # Notificar a la psicóloga (primer User con perfil psicologo)
        from .models import Perfil
        psicologo = User.objects.filter(perfil__rol='psicologo').first()
        if psicologo:
            notificar_psicologo_alerta(instance, psicologo)


# ── Cita profesor: cambio de estado ───────────────────────────────────────────

@receiver(post_save, sender=CitaProfesor)
def on_cita_profesor_guardada(sender, instance, created, **kwargs):
    if not created and instance.estado in ('confirmada', 'cancelada', 'reagendada'):
        notificar_cambio_cita_profesor(instance)


# ── Autoevaluación de bienestar ────────────────────────────────────────────────

@receiver(post_save, sender=AutoevaluacionProfesor)
def on_autoevaluacion_profesor_guardada(sender, instance, created, **kwargs):
    if created:
        generar_alerta_bienestar_docente(instance)

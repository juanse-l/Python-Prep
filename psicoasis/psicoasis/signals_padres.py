"""
psicoasis/signals_padres.py
===========================
Señales del módulo Padres/Tutores.

Registra en psicoasis/apps.py así:

    class PsicoasisConfig(AppConfig):
        name = 'psicoasis'
        def ready(self):
            import psicoasis.signals_padres  # noqa

O simplemente importa este archivo desde psicoasis/__init__.py:
    default_app_config = 'psicoasis.apps.PsicoasisConfig'
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='psicoasis.AutoevaluacionEstudiante')
def alerta_emocion_al_padre(sender, instance, created, **kwargs):
    """
    Cuando el estudiante hace un check-in emocional,
    genera alertas automáticas para los padres vinculados.
    """
    if not created:
        return
    try:
        from .services_padres import generar_alerta_por_emocion, generar_recomendaciones_automaticas
        from .models import Perfil, VinculoPadreTutor

        # Obtener el estudiante vinculado al usuario
        perfil = Perfil.objects.select_related('estudiante_vinculado').get(
            usuario=instance.estudiante
        )
        if not perfil.estudiante_vinculado:
            return
        hijo = perfil.estudiante_vinculado

        # Generar alertas
        generar_alerta_por_emocion(instance)

        # Generar recomendaciones para cada padre vinculado
        vinculos = VinculoPadreTutor.objects.filter(hijo=hijo, activo=True)
        for vinculo in vinculos:
            generar_recomendaciones_automaticas(hijo=hijo, padre=vinculo.padre)

    except Exception:
        # Nunca dejar que un signal rompa el flujo principal
        pass


@receiver(post_save, sender='psicoasis.CitaPadre')
def notificar_cambio_estado_cita(sender, instance, created, **kwargs):
    """
    Cuando la psicóloga cambia el estado de una cita del padre,
    envía notificación automática.
    """
    if created:
        # Cita nueva: notificar al padre que fue recibida
        try:
            from .services_padres import crear_notificacion_padre
            crear_notificacion_padre(
                padre=instance.padre,
                tipo='sistema',
                titulo='✅ Solicitud de cita recibida',
                mensaje=(
                    f'Tu solicitud de cita para el '
                    f'{instance.fecha.strftime("%d/%m/%Y")} a las '
                    f'{instance.hora.strftime("%I:%M %p")} fue recibida. '
                    f'La psicóloga la confirmará próximamente.'
                ),
                prioridad='baja',
                datos_extra={'cita_id': instance.id},
            )
        except Exception:
            pass
    else:
        # Cambio de estado
        try:
            from .services_padres import generar_alerta_cita
            if instance.estado in ('confirmada', 'cancelada', 'reagendada'):
                generar_alerta_cita(instance)
        except Exception:
            pass


@receiver(post_save, sender='psicoasis.MensajePadre')
def notificar_mensaje_padre(sender, instance, created, **kwargs):
    """
    Cuando la psicóloga envía un mensaje al padre,
    crea una notificación interna.
    """
    if not created:
        return
    try:
        from .models import Perfil
        from .services_padres import crear_notificacion_padre

        # Solo si el destinatario es un padre/tutor
        perfil_dest = Perfil.objects.get(usuario=instance.destinatario)
        if perfil_dest.rol not in ('padre', 'tutor'):
            return

        crear_notificacion_padre(
            padre=instance.destinatario,
            tipo='mensaje_nuevo',
            titulo=f'✉️ Nuevo mensaje de la psicóloga',
            mensaje='Tienes un nuevo mensaje privado. Ingresa al sistema para leerlo.',
            prioridad='media',
        )
    except Exception:
        pass

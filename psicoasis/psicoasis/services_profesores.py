"""
psicoasis/services_profesores.py
Lógica de negocio del módulo Profesores.
"""
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    PerfilProfesor, AlertaEstudianteProfesor, CitaProfesor,
    NotificacionProfesor, AutoevaluacionProfesor, LogActividadProfesor,
)


# ── Helpers de perfil ──────────────────────────────────────────────────────────

def get_perfil_profesor(user):
    """Devuelve PerfilProfesor o None."""
    return getattr(user, 'perfil_profesor', None)


def es_profesor(user):
    rol = getattr(getattr(user, 'perfil', None), 'rol', None)
    return rol == 'profesor'


# ── Notificaciones ─────────────────────────────────────────────────────────────

def crear_notificacion_profesor(profesor, tipo, titulo, mensaje,
                                 prioridad='media', url_accion=''):
    """Crea una NotificacionProfesor."""
    return NotificacionProfesor.objects.create(
        profesor=profesor,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        prioridad=prioridad,
        url_accion=url_accion,
    )


def notif_no_leidas_profesor(user):
    """Cuenta notificaciones no leídas del profesor."""
    return NotificacionProfesor.objects.filter(profesor=user, leida=False).count()


# ── Alertas ────────────────────────────────────────────────────────────────────

def get_alertas_activas_profesor(user):
    """Alertas enviadas por el profesor que aún no están atendidas."""
    return AlertaEstudianteProfesor.objects.filter(
        profesor=user
    ).exclude(estado='atendida').order_by('-fecha_creacion')


def notificar_psicologo_alerta(alerta, psicologo_user):
    """Notifica a la psicóloga cuando se crea una alerta docente."""
    from .models import Notificacion
    urgencia_label = alerta.get_urgencia_display()
    Notificacion.objects.create(
        tipo='sistema',
        titulo=f'🚨 Nueva alerta docente [{urgencia_label}]',
        mensaje=(
            f"El/la profesor/a {alerta.profesor.get_full_name() or alerta.profesor.username} "
            f"ha enviado una alerta sobre {alerta.estudiante.get_full_name()}. "
            f"Categoría: {alerta.get_categoria_display()}."
        ),
    )


# ── Citas ──────────────────────────────────────────────────────────────────────

def notificar_cambio_cita_profesor(cita):
    """Notifica al profesor cuando la psicóloga gestiona su cita."""
    tipo_map = {
        'confirmada': ('cita_confirmada', 'alta',
                       '📅 Tu cita fue confirmada',
                       f"La cita del {cita.fecha_confirmada} a las {cita.hora_confirmada} está confirmada."),
        'cancelada': ('cita_cancelada', 'media',
                      '❌ Cita cancelada',
                      'La psicóloga canceló la cita. Puedes solicitar una nueva.'),
        'reagendada': ('cita_confirmada', 'media',
                       '🔄 Cita reagendada',
                       f"Tu cita fue reagendada para el {cita.fecha_confirmada} a las {cita.hora_confirmada}."),
    }
    if cita.estado in tipo_map:
        tipo, prioridad, titulo, mensaje = tipo_map[cita.estado]
        crear_notificacion_profesor(cita.profesor, tipo, titulo, mensaje, prioridad)


# ── Bienestar / Autoevaluación ─────────────────────────────────────────────────

ESTADOS_CRITICOS = ('agotado', 'en_crisis')


def generar_alerta_bienestar_docente(autoevaluacion):
    """Si el docente reporta estado crítico o solicita atención, notifica a la psicóloga."""
    if autoevaluacion.bienestar in ESTADOS_CRITICOS or autoevaluacion.solicita_atencion:
        from .models import Notificacion
        nombre = (autoevaluacion.profesor.get_full_name()
                  or autoevaluacion.profesor.username)
        estado_label = autoevaluacion.get_bienestar_display()
        Notificacion.objects.create(
            tipo='sistema',
            titulo=f'🧘 Alerta de bienestar docente — {nombre}',
            mensaje=(
                f"{nombre} reportó su estado como «{estado_label}» "
                f"(carga: {autoevaluacion.get_carga_laboral_display()}). "
                + ("Ha solicitado atención personalizada." if autoevaluacion.solicita_atencion else "")
            ),
        )


def obtener_historial_bienestar(user, semanas=8):
    """Devuelve las últimas N autoevaluaciones del profesor."""
    return AutoevaluacionProfesor.objects.filter(
        profesor=user
    ).order_by('-semana')[:semanas]


def get_contadores_dashboard_profesor(user):
    """Contadores para el dashboard del profesor."""
    return {
        'notif_no_leidas': notif_no_leidas_profesor(user),
        'alertas_pendientes': AlertaEstudianteProfesor.objects.filter(
            profesor=user, estado='pendiente'
        ).count(),
        'citas_proximas': CitaProfesor.objects.filter(
            profesor=user, estado='confirmada',
            fecha_confirmada__gte=timezone.now().date()
        ).count(),
        'mensajes_no_leidos': _mensajes_no_leidos(user),
    }


def _mensajes_no_leidos(user):
    from .models import MensajeProfesor
    return MensajeProfesor.objects.filter(destinatario=user, leido=False).count()


# ── Log ────────────────────────────────────────────────────────────────────────

def registrar_log_profesor(user, accion, descripcion='', request=None):
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    LogActividadProfesor.objects.create(
        profesor=user, accion=accion, descripcion=descripcion, ip=ip
    )

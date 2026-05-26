"""
psicoasis/services_padres.py
============================
Capa de servicios del módulo Padres/Tutores.
Centraliza la lógica de negocio: alertas, privacidad, estadísticas.

Uso:
    from .services_padres import (
        crear_notificacion_padre,
        obtener_resumen_emocional_hijo,
        verificar_acceso_padre,
        generar_alerta_por_emocion,
        registrar_log_padre,
    )
"""
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta


# ─── Importaciones de modelos (lazy para evitar imports circulares) ───────────

def _modelos():
    from .models import (
        VinculoPadreTutor, ConfigPrivacidadPadre,
        NotificacionPadre, AutoevaluacionEstudiante,
        CitaPadre, MensajePadre, LogActividadPadre,
        RecomendacionPadre, Estudiante,
    )
    return {
        'VinculoPadreTutor': VinculoPadreTutor,
        'ConfigPrivacidadPadre': ConfigPrivacidadPadre,
        'NotificacionPadre': NotificacionPadre,
        'AutoevaluacionEstudiante': AutoevaluacionEstudiante,
        'CitaPadre': CitaPadre,
        'MensajePadre': MensajePadre,
        'LogActividadPadre': LogActividadPadre,
        'RecomendacionPadre': RecomendacionPadre,
        'Estudiante': Estudiante,
    }


# ─── Verificación de acceso ───────────────────────────────────────────────────

def verificar_acceso_padre(padre: User, hijo_id: int, permiso: str = 'activo') -> bool:
    """
    Verifica que el padre tenga vínculo activo con el hijo y el permiso requerido.
    permiso puede ser: 'activo', 'puede_ver_emociones', 'puede_ver_citas',
                       'puede_agendar_citas', 'puede_enviar_mensajes'
    """
    m = _modelos()
    try:
        vinculo = m['VinculoPadreTutor'].objects.get(padre=padre, hijo_id=hijo_id, activo=True)
        if permiso == 'activo':
            return True
        return getattr(vinculo, permiso, False)
    except m['VinculoPadreTutor'].DoesNotExist:
        return False


def get_hijos_de_padre(padre: User):
    """Retorna queryset de Estudiante(s) vinculados a este padre."""
    m = _modelos()
    hijos_ids = m['VinculoPadreTutor'].objects.filter(
        padre=padre, activo=True
    ).values_list('hijo_id', flat=True)
    return m['Estudiante'].objects.filter(id__in=hijos_ids)


def get_vinculos_de_padre(padre: User):
    """Retorna queryset de VinculoPadreTutor con privacidad prefetched."""
    m = _modelos()
    return m['VinculoPadreTutor'].objects.filter(
        padre=padre, activo=True
    ).select_related('hijo', 'privacidad')


# ─── Notificaciones ───────────────────────────────────────────────────────────

def crear_notificacion_padre(padre: User, tipo: str, titulo: str, mensaje: str,
                              hijo=None, prioridad: str = 'media', datos_extra: dict = None):
    """Crea una NotificacionPadre."""
    m = _modelos()
    return m['NotificacionPadre'].objects.create(
        padre=padre,
        hijo=hijo,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        prioridad=prioridad,
        datos_extra=datos_extra or {},
    )


def notificar_todos_padres_de_hijo(hijo, tipo: str, titulo: str, mensaje: str,
                                    prioridad: str = 'media', datos_extra: dict = None):
    """
    Envía notificación a todos los padres/tutores vinculados a un hijo.
    Solo a padres activos.
    """
    m = _modelos()
    vinculos = m['VinculoPadreTutor'].objects.filter(hijo=hijo, activo=True)
    notificaciones = []
    for v in vinculos:
        n = m['NotificacionPadre'](
            padre=v.padre,
            hijo=hijo,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            datos_extra=datos_extra or {},
        )
        notificaciones.append(n)
    if notificaciones:
        m['NotificacionPadre'].objects.bulk_create(notificaciones)


# ─── Alertas automáticas por emoción ─────────────────────────────────────────

EMOCIONES_CRITICAS = {'muy_mal', 'mal'}
EMOCION_LABELS = {
    'muy_bien': '😄 Muy bien',
    'bien': '🙂 Bien',
    'regular': '😐 Regular',
    'mal': '😔 Mal',
    'muy_mal': '😢 Muy mal',
}

def generar_alerta_por_emocion(autoevaluacion):
    """
    Llamar desde un signal de AutoevaluacionEstudiante.
    Genera notificaciones si la emoción es crítica o si hay cambio brusco.
    """
    m = _modelos()
    estudiante_user = autoevaluacion.estudiante
    # Obtener perfil del estudiante vinculado
    try:
        from .models import Perfil
        perfil = Perfil.objects.get(usuario=estudiante_user)
        if not perfil.estudiante_vinculado:
            return
        hijo = perfil.estudiante_vinculado
    except Exception:
        return

    emocion_actual = autoevaluacion.emocion
    emocion_label = EMOCION_LABELS.get(emocion_actual, emocion_actual)

    # ── Alerta emoción crítica ──
    if emocion_actual in EMOCIONES_CRITICAS:
        notificar_todos_padres_de_hijo(
            hijo=hijo,
            tipo='emocion_critica',
            titulo=f'🚨 {hijo.get_full_name()} reportó estado emocional bajo',
            mensaje=(
                f'Tu hijo/a {hijo.get_full_name()} registró hoy '
                f'un estado emocional de "{emocion_label}". '
                f'La psicóloga ya fue notificada. Te recomendamos estar atento/a.'
            ),
            prioridad='alta',
            datos_extra={'emocion': emocion_actual, 'fecha': str(autoevaluacion.fecha)},
        )

    # ── Alerta cambio brusco (estaba bien ayer, hoy está mal) ──
    ayer = autoevaluacion.fecha - timedelta(days=1)
    try:
        anterior = m['AutoevaluacionEstudiante'].objects.get(
            estudiante=estudiante_user, fecha=ayer
        )
        emociones_orden = ['muy_bien', 'bien', 'regular', 'mal', 'muy_mal']
        idx_anterior = emociones_orden.index(anterior.emocion)
        idx_actual = emociones_orden.index(emocion_actual)
        if idx_actual - idx_anterior >= 2:  # caída de 2+ niveles
            notificar_todos_padres_de_hijo(
                hijo=hijo,
                tipo='cambio_brusco',
                titulo=f'📊 Cambio emocional brusco detectado — {hijo.get_full_name()}',
                mensaje=(
                    f'{hijo.get_full_name()} pasó de "{EMOCION_LABELS[anterior.emocion]}" '
                    f'a "{emocion_label}" en un día. '
                    f'Es recomendable conversar con tu hijo/a.'
                ),
                prioridad='alta',
                datos_extra={
                    'emocion_anterior': anterior.emocion,
                    'emocion_actual': emocion_actual,
                },
            )
    except m['AutoevaluacionEstudiante'].DoesNotExist:
        pass


def generar_alerta_cita(cita_padre):
    """
    Genera una notificación al padre cuando su cita cambia de estado.
    Llamar desde la vista de gestión de citas.
    """
    estado = cita_padre.estado
    tipo_map = {
        'confirmada': ('cita_programada', '📅 Cita confirmada', 'media'),
        'cancelada': ('cita_cancelada', '❌ Cita cancelada', 'alta'),
        'reagendada': ('cita_recordatorio', '🔄 Cita reagendada', 'media'),
    }
    if estado not in tipo_map:
        return
    tipo, titulo_base, prioridad = tipo_map[estado]
    fecha_str = cita_padre.fecha.strftime('%d/%m/%Y')
    hora_str = cita_padre.hora.strftime('%I:%M %p')
    crear_notificacion_padre(
        padre=cita_padre.padre,
        tipo=tipo,
        titulo=f'{titulo_base} — {fecha_str}',
        mensaje=f'Tu cita del {fecha_str} a las {hora_str} fue {cita_padre.get_estado_display().lower()}.',
        prioridad=prioridad,
        datos_extra={'cita_id': cita_padre.id},
    )


# ─── Resumen emocional del hijo ───────────────────────────────────────────────

def obtener_resumen_emocional_hijo(hijo, padre: User, dias: int = 7) -> dict:
    """
    Retorna un resumen emocional del hijo para mostrar en el dashboard del padre.
    Respeta la configuración de privacidad del vínculo.
    """
    m = _modelos()
    resultado = {
        'tiene_acceso': False,
        'estado_hoy': None,
        'historial': [],
        'tendencia': None,
        'alertas': 0,
        'nivel_privacidad': 'basico',
    }

    # Verificar acceso
    if not verificar_acceso_padre(padre, hijo.id, 'puede_ver_emociones'):
        return resultado

    # Obtener configuración de privacidad
    try:
        vinculo = m['VinculoPadreTutor'].objects.get(padre=padre, hijo=hijo, activo=True)
        privacidad = getattr(vinculo, 'privacidad', None)
        nivel = privacidad.nivel_detalle if privacidad else 'intermedio'
    except m['VinculoPadreTutor'].DoesNotExist:
        return resultado

    resultado['tiene_acceso'] = True
    resultado['nivel_privacidad'] = nivel

    # Obtener autoevaluaciones del hijo (via User vinculado)
    try:
        from .models import Perfil
        usuario_hijo = Perfil.objects.get(estudiante_vinculado=hijo).usuario
    except Exception:
        return resultado

    hoy = timezone.now().date()
    desde = hoy - timedelta(days=dias)
    evaluaciones = m['AutoevaluacionEstudiante'].objects.filter(
        estudiante=usuario_hijo,
        fecha__gte=desde,
    ).order_by('fecha')

    # Estado hoy
    try:
        hoy_eval = m['AutoevaluacionEstudiante'].objects.get(estudiante=usuario_hijo, fecha=hoy)
        resultado['estado_hoy'] = {
            'emocion': hoy_eval.emocion,
            'label': EMOCION_LABELS.get(hoy_eval.emocion, hoy_eval.emocion),
        }
    except m['AutoevaluacionEstudiante'].DoesNotExist:
        pass

    # Historial (solo si nivel >= intermedio)
    if nivel in ('intermedio', 'completo'):
        resultado['historial'] = [
            {
                'fecha': str(e.fecha),
                'emocion': e.emocion,
                'label': EMOCION_LABELS.get(e.emocion, e.emocion),
            }
            for e in evaluaciones
        ]

    # Tendencia
    emociones_orden = ['muy_bien', 'bien', 'regular', 'mal', 'muy_mal']
    if evaluaciones.count() >= 3:
        vals = [emociones_orden.index(e.emocion) for e in evaluaciones]
        primera_mitad = sum(vals[:len(vals)//2]) / (len(vals)//2)
        segunda_mitad = sum(vals[len(vals)//2:]) / (len(vals) - len(vals)//2)
        if segunda_mitad < primera_mitad - 0.5:
            resultado['tendencia'] = 'mejorando'
        elif segunda_mitad > primera_mitad + 0.5:
            resultado['tendencia'] = 'empeorando'
        else:
            resultado['tendencia'] = 'estable'

    # Alertas no leídas
    resultado['alertas'] = m['NotificacionPadre'].objects.filter(
        padre=padre, hijo=hijo, leida=False, prioridad='alta'
    ).count()

    return resultado


# ─── Recomendaciones automáticas ─────────────────────────────────────────────

RECOMENDACIONES_AUTO = {
    'muy_mal': [
        {
            'titulo': '¿Cómo hablar con tu hijo/a cuando está triste?',
            'contenido': (
                'Cuando tu hijo/a está pasando por un momento difícil, lo más importante '
                'es estar presente sin juzgar. Escucha más de lo que hablas. '
                'Pregunta: "¿Cómo te sientes?" en lugar de "¿Qué pasó?". '
                'Valida sus emociones diciendo: "Entiendo que estás muy triste, eso es válido."'
            ),
            'tipo': 'tecnica',
        },
        {
            'titulo': '5 señales de que tu hijo/a necesita apoyo psicológico',
            'contenido': (
                'Presta atención si ves: cambios en el sueño o apetito, '
                'aislamiento de amigos, bajo rendimiento académico repentino, '
                'irritabilidad constante o pérdida de interés en actividades que antes disfrutaba. '
                'Si notas 3 o más de estas señales por más de 2 semanas, considera una cita con la psicóloga.'
            ),
            'tipo': 'articulo',
        },
    ],
    'mal': [
        {
            'titulo': 'Estrategia: Conexión antes de corrección',
            'contenido': (
                'Antes de abordar cualquier problema de conducta o rendimiento, '
                'conecta emocionalmente con tu hijo/a. '
                'Dedica 10 minutos al día a hablar de sus intereses, sin agenda. '
                'Un hijo que se siente conectado con sus padres responde mejor a los límites y orientaciones.'
            ),
            'tipo': 'estrategia',
        },
    ],
    'regular': [
        {
            'titulo': 'Cómo fortalecer la comunicación familiar',
            'contenido': (
                'Las familias que comparten al menos una comida al día sin pantallas '
                'reportan mayor bienestar emocional en sus hijos. '
                'Crea rituales simples: preguntas de conversación en la cena, '
                'una caminata semanal, o 15 minutos de lectura compartida.'
            ),
            'tipo': 'consejo',
        },
    ],
}


def generar_recomendaciones_automaticas(hijo, padre: User):
    """
    Genera recomendaciones para el padre basadas en el estado emocional reciente del hijo.
    Evita duplicar recomendaciones del mismo título en los últimos 7 días.
    """
    m = _modelos()
    try:
        from .models import Perfil
        usuario_hijo = Perfil.objects.get(estudiante_vinculado=hijo).usuario
    except Exception:
        return

    hoy = timezone.now().date()
    hace_7 = hoy - timedelta(days=7)

    # Obtener emoción más reciente
    ultima_eval = m['AutoevaluacionEstudiante'].objects.filter(
        estudiante=usuario_hijo
    ).order_by('-fecha').first()

    if not ultima_eval:
        return

    recomendaciones_sugeridas = RECOMENDACIONES_AUTO.get(ultima_eval.emocion, [])

    for rec_data in recomendaciones_sugeridas:
        # No repetir si ya existe en los últimos 7 días
        ya_existe = m['RecomendacionPadre'].objects.filter(
            padre=padre, hijo=hijo,
            titulo=rec_data['titulo'],
            fecha_creacion__date__gte=hace_7,
        ).exists()
        if not ya_existe:
            m['RecomendacionPadre'].objects.create(
                padre=padre,
                hijo=hijo,
                tipo=rec_data['tipo'],
                titulo=rec_data['titulo'],
                contenido=rec_data['contenido'],
                trigger_emocion=ultima_eval.emocion,
                generada_por='sistema',
            )


# ─── Log de actividad ─────────────────────────────────────────────────────────

def registrar_log_padre(padre: User, accion: str, descripcion: str = '', request=None):
    """Registra una acción del padre en el log de auditoría."""
    m = _modelos()
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    m['LogActividadPadre'].objects.create(
        padre=padre,
        accion=accion,
        descripcion=descripcion,
        ip_address=ip,
    )


# ─── Contadores para el dashboard ────────────────────────────────────────────

def get_contadores_dashboard_padre(padre: User) -> dict:
    """Retorna contadores para el dashboard del padre."""
    m = _modelos()
    notif_no_leidas = m['NotificacionPadre'].objects.filter(padre=padre, leida=False).count()
    citas_pendientes = m['CitaPadre'].objects.filter(
        padre=padre, estado__in=['pendiente', 'confirmada'],
        fecha__gte=timezone.now().date()
    ).count()
    mensajes_no_leidos = m['MensajePadre'].objects.filter(
        destinatario=padre, estado='enviado'
    ).count()
    recomendaciones_nuevas = m['RecomendacionPadre'].objects.filter(
        padre=padre, leida=False, activo=True
    ).count()
    return {
        'notificaciones': notif_no_leidas,
        'citas_pendientes': citas_pendientes,
        'mensajes': mensajes_no_leidos,
        'recomendaciones': recomendaciones_nuevas,
    }

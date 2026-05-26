from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Notificaciones
    path('notificaciones/', views.notificaciones_view, name='notificaciones'),
    path('notificaciones/<int:pk>/leida/', views.notificacion_marcar_leida, name='notificacion_leida'),
    path('citas-publicas/', views.citas_publicas_view, name='citas_publicas'),
    path('citas-publicas/<int:pk>/', views.cita_publica_atender, name='cita_publica_atender'),

    # Estudiantes
    path('estudiantes/', views.estudiantes_list, name='estudiantes_list'),
    path('estudiantes/nuevo/', views.estudiante_nuevo, name='estudiante_nuevo'),
    path('estudiantes/<int:pk>/', views.estudiante_detalle, name='estudiante_detalle'),
    path('estudiantes/<int:pk>/editar/', views.estudiante_editar, name='estudiante_editar'),

    # Docentes
    path('docentes/', views.docentes_list, name='docentes_list'),
    path('docentes/nuevo/', views.docente_nuevo, name='docente_nuevo'),
    path('docentes/<int:pk>/', views.docente_detalle, name='docente_detalle'),
    path('docentes/<int:pk>/editar/', views.docente_editar, name='docente_editar'),
    path('docentes/seguimiento/nuevo/', views.seguimiento_docente_nuevo, name='seguimiento_docente_nuevo'),

    # Casos (CRUD completo)
    path('casos/nuevo/', views.caso_nuevo, name='caso_nuevo'),
    path('casos/<int:pk>/editar/', views.caso_editar, name='caso_editar'),
    path('casos/<int:pk>/eliminar/', views.caso_eliminar, name='caso_eliminar'),

    # Reuniones
    path('reuniones/', views.reuniones_list, name='reuniones_list'),
    path('reuniones/nueva/', views.reunion_nueva, name='reunion_nueva'),
    path('reuniones/<int:pk>/editar/', views.reunion_editar, name='reunion_editar'),
    path('reuniones/<int:pk>/estado/', views.reunion_cambiar_estado, name='reunion_estado'),

    # Calendario
    path('calendario/', views.calendario_view, name='calendario'),
    path('agenda-cita/', views.agenda_cita_view, name='agenda_cita'),

    # Informes (CRUD completo)
    path('informes/', views.informes_list, name='informes_list'),
    path('informes/nuevo/', views.informe_nuevo, name='informe_nuevo'),
    path('informes/<int:pk>/', views.informe_detalle, name='informe_detalle'),
    path('informes/<int:pk>/editar/', views.informe_editar, name='informe_editar'),
    path('informes/<int:pk>/eliminar/', views.informe_eliminar, name='informe_eliminar'),

    # Descarga/impresión de todos los informes de un estudiante
    path('estudiantes/<int:pk>/informes/todos/', views.informes_estudiante_todos, name='informes_estudiante_todos'),

    # Bienestar
    path('bienestar/', views.bienestar_view, name='bienestar'),
    path('bienestar/herramientas/', views.herramientas_autocuidado, name='herramientas_autocuidado'),
    path('bienestar/biblioteca/', views.biblioteca_emocional, name='biblioteca_emocional'),
    path('bienestar/multimedia/', views.recursos_multimedia, name='recursos_multimedia'),
    path('bienestar/mini-planes/', views.mini_planes, name='mini_planes'),
    path('bienestar/vlog/', views.vlog_salud_mental, name='vlog_salud_mental'),

    # Foros
    path('bienestar/foros/', views.foros_view, name='foros'),
    path('bienestar/foros/nuevo/', views.foro_nuevo_tema, name='foro_nuevo_tema'),
    path('bienestar/foros/<int:pk>/', views.foro_tema_view, name='foro_tema'),

    # Búsqueda
    path('buscar/', views.buscar_view, name='buscar'),

    # Servicio de Aseo
    path('aseo/', views.aseo_list, name='aseo_list'),
    path('aseo/nuevo/', views.aseo_nuevo, name='aseo_nuevo'),
    path('aseo/<int:pk>/', views.aseo_detalle, name='aseo_detalle'),
    path('aseo/<int:pk>/editar/', views.aseo_editar, name='aseo_editar'),

    # Asistente IA
    path('asistente/', views.asistente_ia_view, name='asistente_ia'),
    path('asistente/chat/', views.asistente_ia_chat, name='asistente_ia_chat'),
    # Panel del Estudiante
    path('mi-panel/', views.dashboard_estudiante, name='dashboard_estudiante'),
    path('mi-panel/checkin/', views.checkin_emocional, name='checkin_emocional'),
    path('mi-panel/citas/', views.mis_citas_estudiante, name='mis_citas_estudiante'),
    path('mi-panel/mensajes/', views.mis_mensajes_estudiante, name='mis_mensajes_estudiante'),
    path('mi-panel/bienestar/', views.bienestar_estudiante, name='bienestar_estudiante'),
    path('mi-panel/solicitar-cita/', views.solicitar_cita_estudiante, name='solicitar_cita_estudiante'),

    # Mensajes para la psicóloga
    path('mensajes/', views.bandeja_mensajes_psicologo, name='bandeja_mensajes_psicologo'),

    # Gestión de cuentas estudiante
    path('cuentas-estudiantes/', views.cuentas_estudiantes, name='cuentas_estudiantes'),
    path('cuentas-estudiantes/vincular/<int:user_id>/', views.vincular_estudiante, name='vincular_estudiante'),

    # IA para estudiantes
    path('mi-panel/ia/', views.chat_ia_estudiante, name='chat_ia_estudiante'),

    # Foro emocional
    path('mi-panel/foro-emocional/', views.foro_emocional_estudiante, name='foro_emocional_estudiante'),
    path('mi-panel/foro-emocional/<int:pk>/', views.foro_publicacion_detalle, name='foro_publicacion_detalle'),
    path('foro-emocional/', views.foro_emocional_psicologo, name='foro_emocional_psicologo'),

    # ============================================================
    # MÓDULO PADRES/TUTORES
    # ============================================================

    # ── Panel del Padre/Tutor ──────────────────────────────────────────────
    path('mi-panel-padre/', views.dashboard_padre, name='dashboard_padre'),
    path('mi-panel-padre/notificaciones/', views.notificaciones_padre, name='notificaciones_padre'),
    path('mi-panel-padre/notificaciones/<int:pk>/leida/', views.notificacion_padre_leida, name='notificacion_padre_leida'),
    path('mi-panel-padre/hijo/<int:hijo_id>/emociones/', views.seguimiento_emocional_hijo, name='seguimiento_emocional_hijo'),
    path('mi-panel-padre/hijo/<int:hijo_id>/reporte/', views.reporte_emocional_padre, name='reporte_emocional_padre'),
    path('mi-panel-padre/citas/', views.citas_padre, name='citas_padre'),
    path('mi-panel-padre/citas/<int:pk>/cancelar/', views.cancelar_cita_padre, name='cancelar_cita_padre'),
    path('mi-panel-padre/mensajes/', views.mensajes_padre, name='mensajes_padre'),
    path('mi-panel-padre/foro/', views.foro_padres, name='foro_padres'),
    path('mi-panel-padre/foro/<int:pk>/', views.foro_padres_tema, name='foro_padres_tema'),
    path('mi-panel-padre/recomendaciones/', views.recomendaciones_padre, name='recomendaciones_padre'),

    # ── Gestión de padres (Psicóloga) ─────────────────────────────────────
    path('padres/', views.padres_list, name='padres_list'),
    path('padres/nuevo/', views.padre_nuevo, name='padre_nuevo'),
    path('padres/<int:user_id>/vincular/', views.padre_vincular, name='padre_vincular'),
    path('padres/vinculo/<int:vinculo_id>/privacidad/', views.padre_privacidad, name='padre_privacidad'),
    path('padres/citas/', views.citas_padres_psicologo, name='citas_padres_psicologo'),
    path('padres/citas/<int:pk>/gestionar/', views.gestionar_cita_padre, name='gestionar_cita_padre'),
    path('padres/mensajes/', views.bandeja_mensajes_padres_psicologo, name='bandeja_mensajes_padres'),
    path('padres/recomendaciones/enviar/', views.enviar_recomendacion, name='enviar_recomendacion'),
    path('padres/foro/<int:pk>/moderar/', views.foro_padres_moderar, name='foro_padres_moderar'),

    # ============================================================
    # MÓDULO PROFESORES
    # ============================================================

    # ── Panel del Profesor/a ───────────────────────────────────────────────
    path('mi-panel-docente/', views.dashboard_profesor, name='dashboard_profesor'),
    path('mi-panel-docente/alertas/', views.mis_alertas, name='mis_alertas_profesor'),
    path('mi-panel-docente/alertas/<int:pk>/', views.alerta_detalle, name='alerta_detalle_profesor'),
    path('mi-panel-docente/citas/', views.citas_profesor, name='citas_profesor'),
    path('mi-panel-docente/citas/<int:pk>/cancelar/', views.cancelar_cita_profesor, name='cancelar_cita_profesor'),
    path('mi-panel-docente/mensajes/', views.mensajes_profesor, name='mensajes_profesor'),
    path('mi-panel-docente/notificaciones/', views.notificaciones_profesor, name='notificaciones_profesor'),
    path('mi-panel-docente/recursos/', views.recursos_profesor, name='recursos_profesor'),
    path('mi-panel-docente/bienestar/', views.bienestar_profesor, name='bienestar_profesor'),

    # ── Gestión de Profesores (Psicóloga) ─────────────────────────────────
    path('profesores/', views.profesores_list, name='profesores_list'),
    path('profesores/nuevo/', views.profesor_nuevo, name='profesor_nuevo'),
    path('profesores/<int:user_id>/vincular/', views.profesor_vincular, name='profesor_vincular'),
    path('profesores/alertas/', views.alertas_docentes_psicologo, name='alertas_docentes_psicologo'),
    path('profesores/alertas/<int:pk>/responder/', views.responder_alerta, name='responder_alerta'),
    path('profesores/citas/', views.citas_profesores_psicologo, name='citas_profesores_psicologo'),
    path('profesores/citas/<int:pk>/gestionar/', views.gestionar_cita_profesor, name='gestionar_cita_profesor'),
    path('profesores/mensajes/', views.bandeja_mensajes_prof_psicologo, name='bandeja_mensajes_prof_psicologo'),
    path('profesores/recursos/crear/', views.crear_recurso_profesor, name='crear_recurso_profesor'),
    path('profesores/bienestar/', views.bienestar_docentes_psicologo, name='bienestar_docentes_psicologo'),
]

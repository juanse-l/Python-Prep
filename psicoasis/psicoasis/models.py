from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Notificacion(models.Model):
    TIPOS = [
        ('cita_publica', 'Nueva cita desde formulario público'),
        ('sistema', 'Sistema'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPOS, default='sistema')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=timezone.now)
    # datos extra para citas públicas
    nombre_solicitante = models.CharField(max_length=200, blank=True)
    email_solicitante = models.EmailField(blank=True)
    telefono_solicitante = models.CharField(max_length=30, blank=True)
    rol_solicitante = models.CharField(max_length=30, blank=True)  # estudiante/docente/acudiente
    motivo_consulta = models.TextField(blank=True)
    fecha_solicitada = models.DateField(null=True, blank=True)
    hora_solicitada = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.titulo} — {self.fecha.strftime('%d/%m/%Y')}"


class CitaPublica(models.Model):
    """Citas solicitadas desde el formulario público de la página de inicio"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('atendida', 'Atendida'),
        ('cancelada', 'Cancelada'),
    ]
    ROLES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('acudiente', 'Acudiente / Padre de familia'),
        ('otro', 'Otro'),
    ]
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='estudiante')
    motivo = models.TextField()
    fecha_preferida = models.DateField(null=True, blank=True)
    hora_preferida = models.TimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    notas_internas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Cita solicitada por {self.nombre} — {self.fecha_solicitud.strftime('%d/%m/%Y')}"


class Docente(models.Model):
    AREAS = [
        ('matematicas', 'Matemáticas'),
        ('ciencias', 'Ciencias Naturales'),
        ('sociales', 'Ciencias Sociales'),
        ('lenguaje', 'Lenguaje y Literatura'),
        ('ingles', 'Inglés'),
        ('educacion_fisica', 'Educación Física'),
        ('artes', 'Artes'),
        ('tecnologia', 'Tecnología e Informática'),
        ('religion', 'Religión / Ética'),
        ('orientacion', 'Orientación Escolar'),
        ('coordinacion', 'Coordinación'),
        ('otro', 'Otro'),
    ]
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    area = models.CharField(max_length=30, choices=AREAS, default='otro')
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    grados_a_cargo = models.CharField(max_length=200, blank=True, help_text='Ej: 6A, 7B, 8A')
    fecha_registro = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)
    notas_generales = models.TextField(blank=True)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} — {self.get_area_display()}"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"


class SeguimientoDocente(models.Model):
    """Seguimiento / atención psicológica a docentes"""
    MOTIVOS = [
        ('estres_laboral', 'Estrés Laboral'),
        ('burnout', 'Burnout / Agotamiento'),
        ('conflicto_estudiantes', 'Conflicto con Estudiantes'),
        ('conflicto_colegas', 'Conflicto con Colegas'),
        ('dificultades_personales', 'Dificultades Personales'),
        ('orientacion_pedagogica', 'Orientación Pedagógica'),
        ('otro', 'Otro'),
    ]
    ESTADOS = [
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado'),
    ]
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='seguimientos')
    psicologo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    motivo = models.CharField(max_length=30, choices=MOTIVOS)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Seguimiento {self.docente.get_full_name()} — {self.get_motivo_display()}"


class ForoTema(models.Model):
    CATEGORIAS = [
        ('general', 'General'),
        ('estudiantes', 'Para Estudiantes'),
        ('docentes', 'Para Docentes'),
        ('familias', 'Para Familias'),
        ('bienestar', 'Bienestar Emocional'),
        ('academico', 'Rendimiento Académico'),
    ]
    titulo = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='general')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    activo = models.BooleanField(default=True)
    fijado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fijado', '-fecha_creacion']

    def __str__(self):
        return self.titulo

    def total_respuestas(self):
        return self.respuestas.count()


class ForoRespuesta(models.Model):
    tema = models.ForeignKey(ForoTema, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"Respuesta en '{self.tema.titulo}' por {self.autor}"


class Perfil(models.Model):
    ROLES = [
        ('psicologo', 'Psicólogo/a'),
        ('estudiante', 'Estudiante'),
        ('padre', 'Padre de familia'),
        ('tutor', 'Tutor/Acudiente'),
        ('profesor', 'Profesor/a'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='psicologo')
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default='Psicólogo/a Escolar')
    estudiante_vinculado = models.OneToOneField(
        'Estudiante', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuario_vinculado'
    )

    def es_psicologo(self):
        return self.rol == 'psicologo'

    def es_estudiante(self):
        return self.rol == 'estudiante'

    def es_padre(self):
        return self.rol == 'padre'

    def es_tutor(self):
        return self.rol == 'tutor'

    def es_padre_o_tutor(self):
        return self.rol in ('padre', 'tutor')

    def es_profesor(self):
        return self.rol == 'profesor'

    def __str__(self):
        return f"Perfil de {self.usuario.get_full_name() or self.usuario.username} ({self.get_rol_display()})"


class Estudiante(models.Model):
    GRADOS = [
        ('1A', '1A'), ('1B', '1B'), ('2A', '2A'), ('2B', '2B'),
        ('3A', '3A'), ('3B', '3B'), ('4A', '4A'), ('4B', '4B'),
        ('5A', '5A'), ('5B', '5B'), ('6A', '6A'), ('6B', '6B'),
        ('7A', '7A'), ('7B', '7B'), ('8A', '8A'), ('8B', '8B'),
        ('9A', '9A'), ('9B', '9B'), ('10A', '10A'), ('10B', '10B'),
        ('11A', '11A'), ('11B', '11B'),
    ]

    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    grado = models.CharField(max_length=5, choices=GRADOS)
    edad = models.PositiveIntegerField()
    email = models.EmailField(blank=True, null=True)
    telefono_acudiente = models.CharField(max_length=20, blank=True)
    nombre_acudiente = models.CharField(max_length=200, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)
    notas_generales = models.TextField(blank=True)

    class Meta:
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.grado}"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"


class Caso(models.Model):
    TIPOS_ATENCION = [
        ('urgente', 'Urgente'),
        ('prioritario', 'Prioritario'),
        ('regular', 'Regular'),
        ('seguimiento', 'Seguimiento'),
    ]
    ESTADOS = [
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado'),
        ('suspendido', 'Suspendido'),
    ]
    MOTIVOS = [
        ('ansiedad_academica', 'Ansiedad Académica'),
        ('problemas_familiares', 'Problemas Familiares'),
        ('conflicto_compañeros', 'Conflicto con Compañeros'),
        ('baja_autoestima', 'Baja Autoestima'),
        ('dificultades_aprendizaje', 'Dificultades de Aprendizaje'),
        ('conducta', 'Problemas de Conducta'),
        ('organizacion_escolar', 'Organización Escolar'),
        ('dificultades_familiares', 'Dificultades Familiares'),
        ('otro', 'Otro'),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='casos')
    psicologo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='casos')
    motivo = models.CharField(max_length=50, choices=MOTIVOS)
    descripcion = models.TextField()
    tipo_atencion = models.CharField(max_length=20, choices=TIPOS_ATENCION, default='regular')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo')
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Caso {self.estudiante.get_full_name()} - {self.get_motivo_display()}"


class Reunion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('aplazada', 'Aplazada'),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='reuniones')
    caso = models.ForeignKey(Caso, on_delete=models.SET_NULL, null=True, blank=True, related_name='reuniones')
    psicologo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    notas = models.TextField(blank=True)
    tipo_atencion = models.CharField(max_length=20, choices=Caso.TIPOS_ATENCION, default='regular')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    # Campos para aplazamiento
    fecha_aplazada = models.DateField(null=True, blank=True)
    hora_aplazada = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ['fecha', 'hora']

    def __str__(self):
        return f"Reunión {self.estudiante.get_full_name()} - {self.fecha} {self.hora}"


class Informe(models.Model):
    TIPOS = [
        ('individual', 'Individual'),
        ('grupal', 'Grupal'),
        ('mensual', 'Mensual'),
        ('remision', 'Remisión'),
        ('seguimiento', 'Seguimiento'),
        ('valoracion', 'Valoración Psicológica'),
    ]
    NIVELES_RIESGO = [
        ('', 'Sin clasificar'),
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico — requiere intervención inmediata'),
    ]

    titulo = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='individual')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.SET_NULL, null=True, blank=True)
    psicologo = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Motivo y contexto
    motivo_consulta = models.TextField(blank=True, verbose_name='Motivo de consulta')
    antecedentes = models.TextField(blank=True, verbose_name='Antecedentes relevantes')
    situacion_familiar = models.TextField(blank=True, verbose_name='Situación familiar')

    # Observaciones clínicas
    descripcion_conducta = models.TextField(blank=True, verbose_name='Descripción de la conducta observada')
    estado_emocional = models.TextField(blank=True, verbose_name='Estado emocional')
    relaciones_sociales = models.TextField(blank=True, verbose_name='Relaciones sociales y pares')
    rendimiento_academico = models.TextField(blank=True, verbose_name='Rendimiento académico')

    # Análisis
    contenido = models.TextField(verbose_name='Análisis e impresión psicológica')
    fortalezas = models.TextField(blank=True, verbose_name='Fortalezas y recursos personales')
    factores_riesgo = models.TextField(blank=True, verbose_name='Factores de riesgo identificados')
    nivel_riesgo = models.CharField(max_length=20, choices=NIVELES_RIESGO, blank=True, default='')

    # Plan
    recomendaciones = models.TextField(blank=True, verbose_name='Recomendaciones')
    plan_intervencion = models.TextField(blank=True, verbose_name='Plan de intervención')
    acuerdos = models.TextField(blank=True, verbose_name='Acuerdos y compromisos')
    proxima_sesion = models.TextField(blank=True, verbose_name='Próxima sesión / seguimiento')

    # Remisión
    requiere_remision = models.BooleanField(default=False, verbose_name='Requiere remisión externa')
    entidad_remision = models.CharField(max_length=200, blank=True, verbose_name='Entidad de remisión')

    # Confidencialidad
    confidencial = models.BooleanField(default=True)

    fecha_sesion = models.DateField(null=True, blank=True, verbose_name='Fecha de la sesión')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.fecha_creacion.strftime('%d/%m/%Y')}"


class RecursoWellness(models.Model):
    CATEGORIAS = [
        ('herramienta_autocuidado', 'Herramientas de Autocuidado'),
        ('biblioteca_emocional', 'Biblioteca Emocional'),
        ('recursos_multimedia', 'Recursos Multimedia'),
        ('mini_planes', 'Mini Planes de Autocuidado'),
        ('vlog', 'Vlog Salud Mental'),
        ('foros', 'Foros y Espacios'),
    ]
    TIPOS_MEDIA = [
        ('texto', 'Texto'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('pdf', 'PDF'),
    ]

    titulo = models.CharField(max_length=300)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    tipo_media = models.CharField(max_length=20, choices=TIPOS_MEDIA, default='texto')
    url_media = models.URLField(blank=True)
    contenido = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"


class PersonalAseo(models.Model):
    AREAS = [
        ('pisos_1', 'Pisos 1'),
        ('pisos_2', 'Pisos 2'),
        ('pisos_3', 'Pisos 3'),
        ('patios', 'Patios y exteriores'),
        ('banos', 'Baños'),
        ('cafeteria', 'Cafetería'),
        ('general', 'General'),
    ]
    TURNOS = [
        ('manana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('completo', 'Jornada completa'),
    ]

    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    area_asignada = models.CharField(max_length=30, choices=AREAS, default='general')
    turno = models.CharField(max_length=20, choices=TURNOS, default='manana')
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    fecha_ingreso = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    notas_generales = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = 'Personal de Aseo'
        verbose_name_plural = 'Personal de Aseo'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"


class MensajeEstudiante(models.Model):
    """Mensajes privados entre estudiante y psicóloga"""
    ESTADOS = [
        ('enviado', 'Enviado'),
        ('leido', 'Leído'),
    ]
    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_recibidos')
    contenido = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='enviado')
    fecha = models.DateTimeField(default=timezone.now)
    es_anonimo = models.BooleanField(default=False, help_text="Si el estudiante quiere enviar de forma anónima")

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"Mensaje de {self.remitente} a {self.destinatario} — {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class AutoevaluacionEstudiante(models.Model):
    """Check-in emocional diario del estudiante"""
    EMOCIONES = [
        ('muy_bien', '😄 Muy bien'),
        ('bien', '🙂 Bien'),
        ('regular', '😐 Regular'),
        ('mal', '😔 Mal'),
        ('muy_mal', '😢 Muy mal'),
    ]
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='autoevaluaciones')
    emocion = models.CharField(max_length=20, choices=EMOCIONES)
    nota_privada = models.TextField(blank=True, help_text="Nota privada del estudiante (solo la ve la psicóloga)")
    fecha = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        unique_together = ['estudiante', 'fecha']

    def __str__(self):
        return f"{self.estudiante} — {self.get_emocion_display()} — {self.fecha}"


class ConversacionIA(models.Model):
    """Historial de conversaciones del estudiante con la IA"""
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversaciones_ia')
    pregunta = models.TextField()
    respuesta = models.TextField()
    tema_detectado = models.CharField(max_length=100, blank=True)
    cita_sugerida = models.ForeignKey(
        'CitaPublica', on_delete=models.SET_NULL, null=True, blank=True, related_name='origen_ia'
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"IA chat — {self.estudiante.username} — {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class PublicacionForo(models.Model):
    """Publicaciones de la psicóloga visibles para estudiantes: estrategias, mensajes, recursos"""
    CATEGORIAS = [
        ('ansiedad', '😰 Manejo de ansiedad'),
        ('emociones', '💚 Gestión emocional'),
        ('autoestima', '⭐ Autoestima'),
        ('convivencia', '🤝 Convivencia y relaciones'),
        ('estudio', '📚 Técnicas de estudio'),
        ('duelo', '🕊️ Afrontamiento y duelo'),
        ('motivacion', '🚀 Motivación'),
        ('general', '🌿 General'),
    ]
    TIPOS = [
        ('estrategia', '🛠️ Estrategia'),
        ('mensaje', '💌 Mensaje'),
        ('recurso', '📎 Recurso'),
        ('reflexion', '🌀 Reflexión'),
    ]
    titulo = models.CharField(max_length=300)
    contenido = models.TextField()
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='general')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='mensaje')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='publicaciones_foro')
    fijado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    imagen_url = models.URLField(blank=True, help_text="URL de imagen ilustrativa (opcional)")

    class Meta:
        ordering = ['-fijado', '-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} — {self.get_categoria_display()}"
"""
MODELOS A AGREGAR AL FINAL DE psicoasis/models.py
==================================================
Copia todo este bloque y pégalo al final de tu models.py existente.
No modifiques los modelos ya existentes excepto Perfil.rol (ver nota).

NOTA PERFIL.ROL: Actualiza el campo rol de Perfil así:
    ROLES = [
        ('psicologo', 'Psicólogo/a'),
        ('estudiante', 'Estudiante'),
        ('padre', 'Padre/Madre'),
        ('tutor', 'Tutor/a Legal'),
    ]
"""


class VinculoPadreTutor(models.Model):
    """Relación entre un usuario Padre/Tutor y un Estudiante (hijo)."""

    TIPO_RELACION_CHOICES = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('tutor', 'Tutor/a Legal'),
        ('abuelo', 'Abuelo/a'),
        ('otro', 'Otro Acudiente'),
    ]

    padre = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='vinculos_hijos',
        verbose_name='Padre/Tutor'
    )
    hijo = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='vinculos_padres',
        verbose_name='Estudiante/Hijo'
    )
    tipo_relacion = models.CharField(max_length=20, choices=TIPO_RELACION_CHOICES, default='padre')
    activo = models.BooleanField(default=True)
    es_principal = models.BooleanField(
        default=False,
        help_text='Acudiente principal — recibe todas las alertas'
    )
    # Permisos granulares (pueden ajustarse por la psicóloga)
    puede_ver_emociones = models.BooleanField(default=True)
    puede_ver_citas = models.BooleanField(default=True)
    puede_agendar_citas = models.BooleanField(default=True)
    puede_enviar_mensajes = models.BooleanField(default=True)
    fecha_vinculo = models.DateTimeField(default=timezone.now)
    vinculado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vinculos_creados',
        verbose_name='Registrado por (psicóloga)'
    )

    class Meta:
        verbose_name = 'Vínculo Padre-Hijo'
        verbose_name_plural = 'Vínculos Padre-Hijo'
        unique_together = [('padre', 'hijo')]
        ordering = ['-es_principal', 'hijo__apellido']

    def __str__(self):
        return f"{self.padre.get_full_name()} → {self.hijo.get_full_name()} ({self.get_tipo_relacion_display()})"


class ConfigPrivacidadPadre(models.Model):
    """Controla qué información del hijo puede ver el padre. Configurado por la psicóloga."""

    NIVEL_DETALLE_CHOICES = [
        ('basico', 'Básico — solo estado general'),
        ('intermedio', 'Intermedio — estado + tendencias'),
        ('completo', 'Completo — todo lo permitido'),
    ]

    vinculo = models.OneToOneField(
        VinculoPadreTutor, on_delete=models.CASCADE, related_name='privacidad'
    )
    mostrar_estado_emocional = models.BooleanField(default=True)
    mostrar_historial_emocional = models.BooleanField(default=True)
    mostrar_tendencias = models.BooleanField(default=True)
    mostrar_alertas_riesgo = models.BooleanField(default=True)
    mostrar_citas = models.BooleanField(default=True)
    mostrar_informes_resumidos = models.BooleanField(
        default=False,
        help_text='Resumen genérico de informes (sin contenido clínico detallado)'
    )
    mostrar_notas_privadas = models.BooleanField(
        default=False,
        help_text='Nunca activar sin consentimiento del estudiante'
    )
    nivel_detalle = models.CharField(
        max_length=20, choices=NIVEL_DETALLE_CHOICES, default='intermedio'
    )
    configurado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='configs_privacidad_creadas'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Privacidad del Padre'

    def __str__(self):
        return f"Privacidad: {self.vinculo}"


class NotificacionPadre(models.Model):
    """Alertas y notificaciones enviadas a los padres/tutores."""

    TIPO_CHOICES = [
        ('emocion_critica', '🚨 Estado emocional crítico'),
        ('riesgo_alto', '⚠️ Riesgo emocional alto'),
        ('cambio_brusco', '📊 Cambio emocional brusco'),
        ('cita_programada', '📅 Cita programada'),
        ('cita_cancelada', '❌ Cita cancelada'),
        ('cita_recordatorio', '🔔 Recordatorio de cita'),
        ('observacion_psicologa', '💬 Observación de la psicóloga'),
        ('inasistencia', '📋 Inasistencia a actividad'),
        ('mensaje_nuevo', '✉️ Nuevo mensaje'),
        ('informe_disponible', '📄 Informe disponible'),
        ('sistema', 'ℹ️ Sistema'),
    ]
    PRIORIDAD_CHOICES = [('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')]

    padre = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notificaciones_padre'
    )
    hijo = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='notificaciones_padres',
        null=True, blank=True
    )
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES, default='sistema')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    fecha = models.DateTimeField(default=timezone.now)
    datos_extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Notificación para Padre'

    def __str__(self):
        return f"[{self.get_prioridad_display()}] {self.titulo} → {self.padre.get_full_name()}"


class CitaPadre(models.Model):
    """Citas agendadas por el padre: padre-psicóloga o padre-hijo-psicóloga."""

    TIPO_CITA_CHOICES = [
        ('padre_psicologo', '👤 Padre + Psicóloga'),
        ('familiar', '👨‍👩‍👧 Padre + Hijo + Psicóloga'),
    ]
    MOTIVO_CHOICES = [
        ('crianza', 'Consulta de crianza'),
        ('conducta', 'Problemas de conducta'),
        ('familia', 'Problemas familiares'),
        ('orientacion', 'Orientación general'),
        ('seguimiento_emocional', 'Seguimiento emocional'),
        ('intervencion_familiar', 'Intervención familiar'),
        ('mediacion', 'Mediación'),
        ('acompanamiento', 'Proceso de acompañamiento'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reagendada', 'Reagendada'),
    ]

    padre = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='citas_como_padre'
    )
    hijo = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='citas_con_padre',
        null=True, blank=True,
        help_text='Requerido solo para citas Padre+Hijo+Psicóloga'
    )
    psicologo = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='citas_con_padres'
    )
    tipo_cita = models.CharField(max_length=20, choices=TIPO_CITA_CHOICES, default='padre_psicologo')
    motivo = models.CharField(max_length=50, choices=MOTIVO_CHOICES, default='orientacion')
    descripcion_motivo = models.TextField(blank=True, verbose_name='Descripción adicional del motivo')
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas_psicologo = models.TextField(blank=True, verbose_name='Notas de la psicóloga')
    recordatorio_enviado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora']
        verbose_name = 'Cita de Padre'

    def __str__(self):
        tipo = self.get_tipo_cita_display()
        return f"{tipo} — {self.padre.get_full_name()} [{self.fecha} {self.hora}]"

    def get_participantes(self):
        p = [self.padre.get_full_name()]
        if self.hijo:
            p.append(self.hijo.get_full_name())
        if self.psicologo:
            p.append(f"Psicóloga: {self.psicologo.get_full_name()}")
        return ', '.join(p)


class MensajePadre(models.Model):
    """Mensajes privados entre padre/tutor y psicóloga."""

    ESTADO_CHOICES = [('enviado', 'Enviado'), ('leido', 'Leído')]

    remitente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensajes_padre_enviados'
    )
    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensajes_padre_recibidos'
    )
    hijo_referencia = models.ForeignKey(
        Estudiante, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mensajes_con_padre',
        help_text='Hijo sobre quien trata el mensaje (opcional)'
    )
    contenido = models.TextField()
    archivo_adjunto = models.FileField(
        upload_to='mensajes_padres/', blank=True, null=True,
        verbose_name='Archivo adjunto'
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='enviado')
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Mensaje Padre-Psicóloga'

    def __str__(self):
        return f"Msg: {self.remitente.get_full_name()} → {self.destinatario.get_full_name()} [{self.fecha:%d/%m/%Y}]"


class ForoTemaPadres(models.Model):
    """Temas del foro exclusivo para padres — separado del foro estudiantil."""

    CATEGORIA_CHOICES = [
        ('crianza', '👨‍👩‍👧 Crianza'),
        ('emociones', '💚 Manejo emocional'),
        ('conducta', '🧠 Conducta adolescente'),
        ('comunicacion', '💬 Comunicación familiar'),
        ('conflictos', '🤝 Resolución de conflictos'),
        ('educacion_emocional', '📚 Educación emocional'),
        ('tecnologia', '📱 Uso saludable de tecnología'),
        ('ansiedad', '😰 Ansiedad y estrés en hijos'),
        ('autoestima', '⭐ Autoestima en hijos'),
        ('general', '🌿 General'),
    ]

    titulo = models.CharField(max_length=300)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, default='general')
    autor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='temas_foro_padres'
    )
    es_anonimo = models.BooleanField(default=False, help_text='Publicar sin revelar nombre')
    activo = models.BooleanField(default=True)
    fijado = models.BooleanField(default=False)
    destacado = models.BooleanField(default=False, help_text='Marcado como destacado por la psicóloga')
    moderado = models.BooleanField(default=False, help_text='Revisado y aprobado por psicóloga')
    reportado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fijado', '-destacado', '-fecha_creacion']
        verbose_name = 'Tema Foro Padres'

    def __str__(self):
        return self.titulo

    def total_respuestas(self):
        return self.respuestas.count()

    def autor_display(self):
        if self.es_anonimo:
            return 'Padre anónimo'
        return self.autor.get_full_name() if self.autor else 'Desconocido'


class ForoRespuestaPadres(models.Model):
    """Respuestas en el foro de padres."""

    tema = models.ForeignKey(
        ForoTemaPadres, on_delete=models.CASCADE, related_name='respuestas'
    )
    autor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='respuestas_foro_padres'
    )
    contenido = models.TextField()
    es_anonimo = models.BooleanField(default=False)
    moderado = models.BooleanField(default=False)
    reportado = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Respuesta Foro Padres'

    def __str__(self):
        return f"Respuesta en '{self.tema.titulo}' — {self.fecha:%d/%m/%Y}"

    def autor_display(self):
        if self.es_anonimo:
            return 'Padre anónimo'
        return self.autor.get_full_name() if self.autor else 'Desconocido'


class ReaccionForoPadres(models.Model):
    """Reacciones (me ayudó, gracias, importante) en el foro de padres."""

    TIPO_CHOICES = [
        ('me_ayudo', '👍 Me ayudó'),
        ('gracias', '❤️ Gracias'),
        ('importante', '⭐ Importante'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reacciones_foro_padres'
    )
    tema = models.ForeignKey(
        ForoTemaPadres, on_delete=models.CASCADE, null=True, blank=True,
        related_name='reacciones'
    )
    respuesta = models.ForeignKey(
        ForoRespuestaPadres, on_delete=models.CASCADE, null=True, blank=True,
        related_name='reacciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='me_ayudo')
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Reacción Foro Padres'

    def __str__(self):
        return f"{self.usuario} reaccionó con {self.tipo}"


class RecomendacionPadre(models.Model):
    """Recomendaciones de crianza/recursos enviadas al padre, automáticas o por la psicóloga."""

    TIPO_CHOICES = [
        ('articulo', '📖 Artículo'),
        ('consejo', '💡 Consejo de crianza'),
        ('estrategia', '🛠️ Estrategia'),
        ('tecnica', '🧘 Técnica de comunicación'),
        ('recurso', '📎 Recurso externo'),
        ('actividad', '🎯 Actividad sugerida'),
    ]
    GENERADA_POR_CHOICES = [
        ('psicologa', 'Psicóloga'),
        ('sistema', 'Sistema automático'),
    ]

    padre = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recomendaciones_padre'
    )
    hijo = models.ForeignKey(
        Estudiante, on_delete=models.CASCADE, related_name='recomendaciones_para_padre',
        null=True, blank=True
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='consejo')
    titulo = models.CharField(max_length=300)
    contenido = models.TextField()
    url_recurso = models.URLField(blank=True)
    trigger_emocion = models.CharField(
        max_length=30, blank=True,
        help_text='Emoción del hijo que originó esta recomendación'
    )
    generada_por = models.CharField(max_length=20, choices=GENERADA_POR_CHOICES, default='psicologa')
    activo = models.BooleanField(default=True)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Recomendación para Padre'

    def __str__(self):
        return f"{self.titulo} → {self.padre.get_full_name()}"


class LogActividadPadre(models.Model):
    """Auditoría de acciones del padre en el sistema."""

    ACCION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('ver_dashboard', 'Ver dashboard'),
        ('ver_emociones_hijo', 'Ver emociones del hijo'),
        ('ver_citas', 'Ver citas'),
        ('crear_cita', 'Crear cita'),
        ('cancelar_cita', 'Cancelar cita'),
        ('enviar_mensaje', 'Enviar mensaje'),
        ('ver_reporte', 'Ver reporte'),
        ('foro_crear_tema', 'Crear tema en foro'),
        ('foro_comentar', 'Comentar en foro'),
    ]

    padre = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='logs_actividad'
    )
    accion = models.CharField(max_length=50, choices=ACCION_CHOICES)
    descripcion = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Actividad del Padre'

    def __str__(self):
        return f"{self.padre.username} — {self.accion} — {self.fecha:%d/%m/%Y %H:%M}"
"""
MODELOS DEL MÓDULO PROFESORES — agregar al final de psicoasis/models.py
"""


class PerfilProfesor(models.Model):
    """Perfil extendido del usuario con rol 'profesor'.
    Vincula el User con el registro Docente existente."""

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='perfil_profesor'
    )
    docente = models.OneToOneField(
        'Docente', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='usuario_vinculado',
        help_text='Registro Docente asociado a esta cuenta'
    )
    # Bienestar personal del profesor
    acepta_acompanamiento = models.BooleanField(
        default=True,
        help_text='El profesor acepta recibir seguimiento de bienestar'
    )
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Perfil de Profesor'
        verbose_name_plural = 'Perfiles de Profesores'

    def __str__(self):
        return f"Profesor: {self.usuario.get_full_name() or self.usuario.username}"

    def get_grados(self):
        """Devuelve lista de grados a cargo desde el Docente vinculado."""
        if self.docente and self.docente.grados_a_cargo:
            return [g.strip() for g in self.docente.grados_a_cargo.split(',') if g.strip()]
        return []


class AlertaEstudianteProfesor(models.Model):
    """Alerta que un profesor envía a la psicóloga sobre un estudiante.
    Canal formal de derivación docente → orientación."""

    NIVEL_URGENCIA = [
        ('informativa', '🟡 Informativa'),
        ('moderada', '🟠 Moderada — requiere atención pronto'),
        ('urgente', '🔴 Urgente — atención prioritaria'),
    ]
    CATEGORIAS = [
        ('rendimiento', '📉 Bajo rendimiento / desmotivación'),
        ('conducta', '⚠️ Cambio de conducta'),
        ('ausentismo', '📅 Ausentismo o evasión'),
        ('convivencia', '🤝 Problema de convivencia / bullying'),
        ('emocional', '💔 Señales emocionales preocupantes'),
        ('familia', '🏠 Situación familiar'),
        ('autolesion', '🚨 Posible autolesión / riesgo'),
        ('otro', '📋 Otro'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('atendida', 'Atendida'),
        ('derivada', 'Derivada a caso'),
    ]

    profesor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='alertas_enviadas_prof'
    )
    estudiante = models.ForeignKey(
        'Estudiante', on_delete=models.CASCADE, related_name='alertas_docentes'
    )
    categoria = models.CharField(max_length=30, choices=CATEGORIAS)
    urgencia = models.CharField(max_length=20, choices=NIVEL_URGENCIA, default='informativa')
    descripcion = models.TextField(verbose_name='Descripción de la situación observada')
    conductas_observadas = models.TextField(
        blank=True,
        verbose_name='Conductas específicas observadas (cuándo, dónde, con qué frecuencia)'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    # Respuesta de la psicóloga
    respuesta_psicologo = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    caso_generado = models.ForeignKey(
        'Caso', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='origen_alerta_docente'
    )
    # Metadatos
    es_confidencial = models.BooleanField(
        default=True,
        help_text='Si es True el nombre del profesor no se mostrará al estudiante'
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Alerta Docente'
        verbose_name_plural = 'Alertas Docentes'

    def __str__(self):
        return f"Alerta [{self.get_urgencia_display()}] {self.estudiante} — {self.get_categoria_display()}"


class CitaProfesor(models.Model):
    """Cita entre un profesor y la psicóloga (para el propio bienestar del docente
    o para coordinación sobre un estudiante)."""

    TIPOS = [
        ('bienestar_propio', '💆 Bienestar / apoyo personal'),
        ('orientacion_caso', '🎓 Orientación sobre un estudiante'),
        ('estrategias_aula', '📚 Estrategias pedagógicas y de aula'),
        ('coordinacion', '🤝 Coordinación institucional'),
        ('otro', '📋 Otro'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('reagendada', 'Reagendada'),
    ]

    profesor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='citas_profesor'
    )
    tipo = models.CharField(max_length=30, choices=TIPOS, default='bienestar_propio')
    motivo_detalle = models.TextField(verbose_name='Detalle del motivo')
    # Estudiante relacionado (solo para tipo orientacion_caso / estrategias)
    estudiante_relacionado = models.ForeignKey(
        'Estudiante', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='citas_prof_relacionadas'
    )
    # Fecha propuesta
    fecha_propuesta = models.DateField(null=True, blank=True)
    hora_propuesta = models.TimeField(null=True, blank=True)
    # Fecha confirmada por psicóloga
    fecha_confirmada = models.DateField(null=True, blank=True)
    hora_confirmada = models.TimeField(null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    notas_psicologo = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Cita Profesor'
        verbose_name_plural = 'Citas Profesores'

    def __str__(self):
        return f"Cita {self.profesor.get_full_name()} — {self.get_tipo_display()} [{self.get_estado_display()}]"


class MensajeProfesor(models.Model):
    """Mensajería privada entre un profesor y la psicóloga."""

    remitente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensajes_prof_enviados'
    )
    destinatario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='mensajes_prof_recibidos'
    )
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    archivo_adjunto = models.FileField(
        upload_to='mensajes_profesores/', blank=True, null=True
    )
    # Hilo de conversación (para agrupar respuestas)
    hilo = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='respuestas'
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['fecha']
        verbose_name = 'Mensaje Profesor'
        verbose_name_plural = 'Mensajes Profesores'

    def __str__(self):
        return f"Msg {self.remitente.username} → {self.destinatario.username} ({self.fecha.strftime('%d/%m/%Y')})"


class NotificacionProfesor(models.Model):
    """Notificaciones del sistema para el profesor."""

    TIPOS = [
        ('alerta_respondida', '✅ Tu alerta fue respondida'),
        ('cita_confirmada', '📅 Cita confirmada'),
        ('cita_cancelada', '❌ Cita cancelada'),
        ('mensaje_nuevo', '💬 Mensaje nuevo'),
        ('recurso_compartido', '📎 Recurso compartido contigo'),
        ('caso_derivado', '🗂️ Estudiante derivado a caso'),
        ('sistema', '🔔 Sistema'),
    ]
    PRIORIDAD = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]

    profesor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notificaciones_profesor'
    )
    tipo = models.CharField(max_length=30, choices=TIPOS, default='sistema')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD, default='media')
    url_accion = models.CharField(max_length=200, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Notificación Profesor'
        verbose_name_plural = 'Notificaciones Profesores'

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} — {self.profesor.username}"


class RecursoProfesor(models.Model):
    """Recursos / materiales que la psicóloga comparte con profesores:
    guías de manejo de aula, protocolos de crisis, estrategias inclusivas."""

    CATEGORIAS = [
        ('manejo_aula', '🏫 Manejo de aula y convivencia'),
        ('deteccion_temprana', '🔍 Detección temprana de señales'),
        ('estres_burnout', '🧘 Manejo del estrés y burnout docente'),
        ('inclusion', '♿ Educación inclusiva'),
        ('comunicacion', '🗣️ Comunicación asertiva'),
        ('crisis', '🚨 Protocolos de crisis'),
        ('aprendizaje', '📚 Dificultades de aprendizaje'),
        ('general', '🌿 General'),
    ]
    TIPOS = [
        ('guia', '📄 Guía / Documento'),
        ('estrategia', '🛠️ Estrategia práctica'),
        ('protocolo', '📋 Protocolo'),
        ('video', '🎥 Video / Webinar'),
        ('infografia', '🖼️ Infografía'),
    ]

    titulo = models.CharField(max_length=300)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default='general')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='guia')
    contenido = models.TextField(blank=True)
    url_externo = models.URLField(blank=True)
    archivo = models.FileField(upload_to='recursos_profesores/', blank=True, null=True)
    # Visibilidad: para todos los profesores o específico
    para_todos = models.BooleanField(default=True)
    profesores_especificos = models.ManyToManyField(
        User, blank=True, related_name='recursos_asignados'
    )
    autor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='recursos_creados_prof'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Recurso Profesor'
        verbose_name_plural = 'Recursos Profesores'

    def __str__(self):
        return f"{self.titulo} [{self.get_categoria_display()}]"


class AutoevaluacionProfesor(models.Model):
    """Check-in de bienestar del profesor (semanal).
    Permite a la psicóloga detectar docentes en riesgo de burnout."""

    BIENESTAR = [
        ('excelente', '😄 Excelente'),
        ('bien', '🙂 Bien'),
        ('regular', '😐 Regular'),
        ('agotado', '😔 Agotado/a'),
        ('en_crisis', '😢 En crisis'),
    ]
    CARGA = [
        ('manejable', 'Manejable'),
        ('alta', 'Alta'),
        ('muy_alta', 'Muy alta — me desborda'),
    ]

    profesor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='autoevaluaciones_profesor'
    )
    bienestar = models.CharField(max_length=20, choices=BIENESTAR)
    carga_laboral = models.CharField(max_length=20, choices=CARGA, default='manejable')
    nota_privada = models.TextField(
        blank=True,
        help_text='Nota opcional visible solo para la psicóloga'
    )
    solicita_atencion = models.BooleanField(
        default=False,
        help_text='Si el docente marca esta casilla, la psicóloga recibe una alerta'
    )
    semana = models.DateField(
        default=timezone.now,
        help_text='Fecha de inicio de la semana reportada'
    )

    class Meta:
        ordering = ['-semana']
        unique_together = ['profesor', 'semana']
        verbose_name = 'Autoevaluación Profesor'
        verbose_name_plural = 'Autoevaluaciones Profesores'

    def __str__(self):
        return f"{self.profesor.username} — {self.get_bienestar_display()} — semana {self.semana}"


class LogActividadProfesor(models.Model):
    """Auditoría de acciones del profesor en el módulo."""

    ACCIONES = [
        ('login', 'Inicio de sesión'),
        ('alerta_enviada', 'Alerta enviada'),
        ('cita_solicitada', 'Cita solicitada'),
        ('mensaje_enviado', 'Mensaje enviado'),
        ('recurso_visto', 'Recurso consultado'),
        ('autoevaluacion', 'Autoevaluación completada'),
    ]

    profesor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='logs_actividad_profesor'
    )
    accion = models.CharField(max_length=30, choices=ACCIONES)
    descripcion = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log Actividad Profesor'

    def __str__(self):
        return f"{self.profesor.username} — {self.get_accion_display()} — {self.fecha.strftime('%d/%m/%Y %H:%M')}"

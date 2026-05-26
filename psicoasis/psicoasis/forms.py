from django import forms
from django.contrib.auth.models import User
from .models import (
    Estudiante, Caso, Reunion, Informe, Docente,
    SeguimientoDocente, CitaPublica, ForoTema, ForoRespuesta, PersonalAseo
)


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['nombre', 'apellido', 'grado', 'edad', 'email',
                  'telefono_acudiente', 'nombre_acudiente', 'notas_generales']


class CasoForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = ['estudiante', 'motivo', 'descripcion', 'tipo_atencion', 'estado']


class ReunionForm(forms.ModelForm):
    class Meta:
        model = Reunion
        fields = ['estudiante', 'caso', 'fecha', 'hora', 'motivo', 'estado', 'tipo_atencion', 'notas', 'fecha_aplazada', 'hora_aplazada']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'fecha_aplazada': forms.DateInput(attrs={'type': 'date'}),
            'hora_aplazada': forms.TimeInput(attrs={'type': 'time'}),
        }


class InformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        fields = [
            'titulo', 'tipo', 'estudiante', 'fecha_sesion',
            'motivo_consulta', 'antecedentes', 'situacion_familiar',
            'descripcion_conducta', 'estado_emocional', 'relaciones_sociales', 'rendimiento_academico',
            'contenido', 'fortalezas', 'factores_riesgo', 'nivel_riesgo',
            'recomendaciones', 'plan_intervencion', 'acuerdos', 'proxima_sesion',
            'requiere_remision', 'entidad_remision', 'confidencial',
        ]
        widgets = {
            'fecha_sesion': forms.DateInput(attrs={'type': 'date'}),
        }


class DocenteForm(forms.ModelForm):
    class Meta:
        model = Docente
        fields = ['nombre', 'apellido', 'area', 'email', 'telefono', 'grados_a_cargo', 'notas_generales']


class SeguimientoDocenteForm(forms.ModelForm):
    class Meta:
        model = SeguimientoDocente
        fields = ['docente', 'motivo', 'descripcion', 'estado']


class CitaPublicaForm(forms.ModelForm):
    class Meta:
        model = CitaPublica
        fields = ['nombre', 'email', 'telefono', 'rol', 'motivo', 'fecha_preferida', 'hora_preferida']
        widgets = {
            'fecha_preferida': forms.DateInput(attrs={'type': 'date'}),
            'hora_preferida': forms.TimeInput(attrs={'type': 'time'}),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }


class ForoTemaForm(forms.ModelForm):
    class Meta:
        model = ForoTema
        fields = ['titulo', 'descripcion', 'categoria']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class ForoRespuestaForm(forms.ModelForm):
    class Meta:
        model = ForoRespuesta
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 3}),
        }


class RegistroForm(forms.ModelForm):
    ROL_CHOICES = [
        ('psicologo', '🧠 Psicólogo/a'),
        ('estudiante', '🎒 Estudiante'),
    ]
    rol = forms.ChoiceField(choices=ROL_CHOICES, widget=forms.RadioSelect, label='Tipo de cuenta')
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')
    # Campo opcional para vincular al registro de estudiante (solo para rol=estudiante)
    grado = forms.CharField(max_length=5, required=False, label='Grado')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def save(self, commit=True):
        from .models import Perfil
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Perfil.objects.get_or_create(
                usuario=user,
                defaults={'rol': self.cleaned_data.get('rol', 'psicologo')}
            )
        return user


class PersonalAseoForm(forms.ModelForm):
    class Meta:
        model = PersonalAseo
        fields = ['nombre', 'apellido', 'area_asignada', 'turno', 'telefono', 'email', 'fecha_ingreso', 'notas_generales']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'notas_generales': forms.Textarea(attrs={'rows': 3}),
        }


# ============================================================
# MÓDULO PADRES/TUTORES
# ============================================================
from django import forms
from django.contrib.auth.models import User
from .models import (
    VinculoPadreTutor, ConfigPrivacidadPadre, CitaPadre,
    MensajePadre, ForoTemaPadres, ForoRespuestaPadres,
    RecomendacionPadre, NotificacionPadre,
)


# ─── Registro de padre desde panel psicóloga ──────────────────────────────────

class RegistroPadreForm(forms.Form):
    """Formulario que usa la psicóloga para crear la cuenta de un padre/tutor."""
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
    )
    last_name = forms.CharField(
        label='Apellido',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
    )
    password = forms.CharField(
        label='Contraseña temporal',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6,
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3XX XXX XXXX'}),
    )
    rol = forms.ChoiceField(
        label='Tipo de acudiente',
        choices=[('padre', 'Padre/Madre'), ('tutor', 'Tutor/a Legal')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email


# ─── Vínculo padre ↔ hijo ─────────────────────────────────────────────────────

class VinculoPadreTutorForm(forms.ModelForm):
    class Meta:
        model = VinculoPadreTutor
        fields = [
            'padre', 'hijo', 'tipo_relacion', 'es_principal',
            'puede_ver_emociones', 'puede_ver_citas',
            'puede_agendar_citas', 'puede_enviar_mensajes',
        ]
        widgets = {
            'padre': forms.Select(attrs={'class': 'form-select'}),
            'hijo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_relacion': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo usuarios con rol padre o tutor
        from .models import Perfil
        padre_ids = Perfil.objects.filter(rol__in=['padre', 'tutor']).values_list('usuario_id', flat=True)
        self.fields['padre'].queryset = User.objects.filter(id__in=padre_ids)


# ─── Privacidad ───────────────────────────────────────────────────────────────

class ConfigPrivacidadPadreForm(forms.ModelForm):
    class Meta:
        model = ConfigPrivacidadPadre
        exclude = ['vinculo', 'configurado_por', 'fecha_actualizacion']
        widgets = {
            'nivel_detalle': forms.Select(attrs={'class': 'form-select'}),
        }


# ─── Citas del padre ──────────────────────────────────────────────────────────

class CitaPadreForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )

    class Meta:
        model = CitaPadre
        fields = ['tipo_cita', 'hijo', 'motivo', 'descripcion_motivo', 'fecha', 'hora']
        widgets = {
            'tipo_cita': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_cita'}),
            'hijo': forms.Select(attrs={'class': 'form-select', 'id': 'id_hijo'}),
            'motivo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente el motivo de la consulta…',
            }),
        }

    def __init__(self, *args, **kwargs):
        padre = kwargs.pop('padre', None)
        super().__init__(*args, **kwargs)
        if padre:
            from .models import VinculoPadreTutor, Estudiante
            hijos_ids = VinculoPadreTutor.objects.filter(
                padre=padre, activo=True, puede_agendar_citas=True
            ).values_list('hijo_id', flat=True)
            self.fields['hijo'].queryset = Estudiante.objects.filter(id__in=hijos_ids)
        self.fields['hijo'].required = False
        self.fields['hijo'].empty_label = '— Solo padre + psicóloga —'

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_cita')
        hijo = cleaned.get('hijo')
        if tipo == 'familiar' and not hijo:
            raise forms.ValidationError(
                'Para una cita familiar debes seleccionar a tu hijo/a.'
            )
        return cleaned


class CitaPadreNotasForm(forms.ModelForm):
    """Para que la psicóloga agregue notas y cambie el estado."""
    class Meta:
        model = CitaPadre
        fields = ['estado', 'notas_psicologo']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas_psicologo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# ─── Mensajería padre ↔ psicóloga ─────────────────────────────────────────────

class MensajePadreForm(forms.ModelForm):
    class Meta:
        model = MensajePadre
        fields = ['contenido', 'hijo_referencia', 'archivo_adjunto']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu mensaje…',
            }),
            'hijo_referencia': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        padre = kwargs.pop('padre', None)
        super().__init__(*args, **kwargs)
        if padre:
            from .models import VinculoPadreTutor, Estudiante
            hijos_ids = VinculoPadreTutor.objects.filter(
                padre=padre, activo=True
            ).values_list('hijo_id', flat=True)
            self.fields['hijo_referencia'].queryset = Estudiante.objects.filter(id__in=hijos_ids)
        self.fields['hijo_referencia'].required = False
        self.fields['hijo_referencia'].empty_label = '— Sin referencia a un hijo específico —'
        self.fields['archivo_adjunto'].required = False


# ─── Foro de padres ───────────────────────────────────────────────────────────

class ForoTemaPadresForm(forms.ModelForm):
    class Meta:
        model = ForoTemaPadres
        fields = ['titulo', 'descripcion', 'categoria', 'es_anonimo']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '¿Sobre qué quieres conversar?',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Desarrolla tu pregunta o tema…',
            }),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }


class ForoRespuestaPadresForm(forms.ModelForm):
    class Meta:
        model = ForoRespuestaPadres
        fields = ['contenido', 'es_anonimo']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu respuesta…',
            }),
        }


# ─── Recomendaciones (psicóloga → padre) ────────────────────────────────────

class RecomendacionPadreForm(forms.ModelForm):
    class Meta:
        model = RecomendacionPadre
        fields = ['padre', 'hijo', 'tipo', 'titulo', 'contenido', 'url_recurso', 'trigger_emocion']
        widgets = {
            'padre': forms.Select(attrs={'class': 'form-select'}),
            'hijo': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'url_recurso': forms.URLInput(attrs={'class': 'form-control'}),
            'trigger_emocion': forms.Select(
                attrs={'class': 'form-select'},
                choices=[
                    ('', '— Sin emoción específica —'),
                    ('muy_bien', '😄 Muy bien'),
                    ('bien', '🙂 Bien'),
                    ('regular', '😐 Regular'),
                    ('mal', '😔 Mal'),
                    ('muy_mal', '😢 Muy mal'),
                ],
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Perfil
        padre_ids = Perfil.objects.filter(rol__in=['padre', 'tutor']).values_list('usuario_id', flat=True)
        self.fields['padre'].queryset = User.objects.filter(id__in=padre_ids)
        self.fields['hijo'].required = False
        self.fields['hijo'].empty_label = '— Recomendación general —'
        self.fields['url_recurso'].required = False
        self.fields['trigger_emocion'].required = False


# ============================================================
# MÓDULO PROFESORES
# ============================================================
from django import forms
from django.contrib.auth.models import User
from .models import (
    AlertaEstudianteProfesor, CitaProfesor, MensajeProfesor,
    RecursoProfesor, AutoevaluacionProfesor, PerfilProfesor, Estudiante,
)


# ── Registro / alta de cuenta profesor ────────────────────────────────────────

class RegistroProfesorForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': '••••••••'}))
    first_name = forms.CharField(label='Nombre', max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellidos', max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo institucional',
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def clean(self):
        cd = super().clean()
        if cd.get('password1') != cd.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ── Alerta docente ─────────────────────────────────────────────────────────────

class AlertaEstudianteForm(forms.ModelForm):
    class Meta:
        model = AlertaEstudianteProfesor
        fields = [
            'estudiante', 'categoria', 'urgencia',
            'descripcion', 'conductas_observadas', 'es_confidencial',
        ]
        widgets = {
            'estudiante': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'urgencia': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe la situación observada con el mayor detalle posible…',
            }),
            'conductas_observadas': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Ej: "Desde el lunes no participa en clase, llora al salir…"',
            }),
            'es_confidencial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, grados_prof=None, **kwargs):
        super().__init__(*args, **kwargs)
        if grados_prof:
            self.fields['estudiante'].queryset = Estudiante.objects.filter(
                grado__in=grados_prof, activo=True
            ).order_by('grado', 'apellido')
        else:
            self.fields['estudiante'].queryset = Estudiante.objects.filter(
                activo=True
            ).order_by('grado', 'apellido')


# ── Cita profesor ──────────────────────────────────────────────────────────────

class CitaProfesorForm(forms.ModelForm):
    class Meta:
        model = CitaProfesor
        fields = [
            'tipo', 'motivo_detalle', 'estudiante_relacionado',
            'fecha_propuesta', 'hora_propuesta',
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'motivo_detalle': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Explica brevemente el motivo de la cita…',
            }),
            'estudiante_relacionado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_propuesta': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}),
            'hora_propuesta': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estudiante_relacionado'].required = False
        self.fields['estudiante_relacionado'].queryset = Estudiante.objects.filter(
            activo=True
        ).order_by('grado', 'apellido')
        self.fields['estudiante_relacionado'].empty_label = '— Ninguno (cita personal) —'


class CitaProfesorGestionForm(forms.ModelForm):
    """Usado por la psicóloga para confirmar / reagendar / cancelar."""
    class Meta:
        model = CitaProfesor
        fields = ['estado', 'fecha_confirmada', 'hora_confirmada', 'notas_psicologo']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_confirmada': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}),
            'hora_confirmada': forms.TimeInput(
                attrs={'class': 'form-control', 'type': 'time'}),
            'notas_psicologo': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
            }),
        }


# ── Mensajería ─────────────────────────────────────────────────────────────────

class MensajeProfesorForm(forms.ModelForm):
    class Meta:
        model = MensajeProfesor
        fields = ['contenido', 'archivo_adjunto']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Escribe tu mensaje…',
            }),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ── Recurso para profesores ────────────────────────────────────────────────────

class RecursoProfesorForm(forms.ModelForm):
    class Meta:
        model = RecursoProfesor
        fields = [
            'titulo', 'descripcion', 'categoria', 'tipo',
            'contenido', 'url_externo', 'archivo',
            'para_todos', 'profesores_especificos',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'url_externo': forms.URLInput(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'para_todos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profesores_especificos': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profesores_especificos'].queryset = User.objects.filter(
            perfil__rol='profesor'
        ).order_by('last_name')
        self.fields['profesores_especificos'].required = False


# ── Autoevaluación bienestar ───────────────────────────────────────────────────

class AutoevaluacionProfesorForm(forms.ModelForm):
    class Meta:
        model = AutoevaluacionProfesor
        fields = ['bienestar', 'carga_laboral', 'nota_privada', 'solicita_atencion']
        widgets = {
            'bienestar': forms.RadioSelect(attrs={'class': 'bienestar-radio'}),
            'carga_laboral': forms.RadioSelect(attrs={'class': 'carga-radio'}),
            'nota_privada': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': '(Opcional) Cuéntame cómo te has sentido esta semana…',
            }),
            'solicita_atencion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ── Respuesta a alerta (psicóloga) ─────────────────────────────────────────────

class RespuestaAlertaForm(forms.ModelForm):
    class Meta:
        model = AlertaEstudianteProfesor
        fields = ['estado', 'respuesta_psicologo']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'respuesta_psicologo': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Escribe tu respuesta al docente…',
            }),
        }

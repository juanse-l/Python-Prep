from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings as django_settings
from datetime import date, timedelta
import calendar
import json
from .models import (
    Estudiante, Caso, Reunion, Informe, RecursoWellness, Perfil,
    Notificacion, CitaPublica, Docente, SeguimientoDocente,
    ForoTema, ForoRespuesta, PersonalAseo,
    MensajeEstudiante, AutoevaluacionEstudiante,
    ConversacionIA, PublicacionForo
)
import os
import urllib.request as _urllib_req
from .forms import (
    EstudianteForm, CasoForm, ReunionForm, InformeForm, RegistroForm,
    DocenteForm, SeguimientoDocenteForm, CitaPublicaForm,
    ForoTemaForm, ForoRespuestaForm, PersonalAseoForm
)

def home_view(request):
    from datetime import date
    import json as _json
    form = CitaPublicaForm()
    exito = False
    if request.method == 'POST':
        form = CitaPublicaForm(request.POST)
        if form.is_valid():
            cita = form.save()
            Notificacion.objects.create(
                tipo='cita_publica',
                titulo=f'Nueva solicitud de cita — {cita.nombre}',
                mensaje=f'{cita.get_rol_display()} solicita una cita. Motivo: {cita.motivo[:100]}',
                nombre_solicitante=cita.nombre,
                email_solicitante=cita.email,
                telefono_solicitante=cita.telefono,
                rol_solicitante=cita.rol,
                motivo_consulta=cita.motivo,
                fecha_solicitada=cita.fecha_preferida,
                hora_solicitada=cita.hora_preferida,
            )
            # ── Enviar correo a la psicóloga ────────────────────────────────
            try:
                fecha_str = cita.fecha_preferida.strftime('%d/%m/%Y') if cita.fecha_preferida else 'Sin especificar'
                hora_str  = cita.hora_preferida.strftime('%I:%M %p') if cita.hora_preferida else 'Sin especificar'
                asunto = f'📅 Nueva solicitud de cita — {cita.nombre}'
                cuerpo = (
                    f'Hola, has recibido una nueva solicitud de cita en PsicoAsis.\n\n'
                    f'━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                    f'👤 Nombre:       {cita.nombre}\n'
                    f'🎭 Rol:          {cita.get_rol_display()}\n'
                    f'📧 Correo:       {cita.email or "No indicado"}\n'
                    f'📞 Teléfono:     {cita.telefono or "No indicado"}\n'
                    f'📅 Fecha pref.:  {fecha_str}\n'
                    f'🕐 Hora pref.:   {hora_str}\n'
                    f'━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'📝 MOTIVO DE CONSULTA:\n{cita.motivo}\n\n'
                    f'Ingresa al panel de PsicoAsis para gestionar esta solicitud.\n'
                )
                send_mail(
                    asunto,
                    cuerpo,
                    django_settings.DEFAULT_FROM_EMAIL,
                    [django_settings.PSICOLOGA_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass
            exito = True
            form = CitaPublicaForm()

    # ── Horas ocupadas por día: reuniones confirmadas/pendientes en los próximos 3 meses ──
    hoy = date.today()
    tres_meses = hoy + timedelta(days=90)
    reuniones_proximas = Reunion.objects.filter(
        fecha__gte=hoy,
        fecha__lte=tres_meses,
        estado__in=['pendiente', 'confirmada']
    ).values('fecha', 'hora')

    # Construir dict: { 'YYYY-MM-DD': ['08:00', '10:30', ...] }
    horas_por_dia = {}
    for r in reuniones_proximas:
        iso = r['fecha'].isoformat()
        hora_str = r['hora'].strftime('%H:%M')
        if iso not in horas_por_dia:
            horas_por_dia[iso] = []
        horas_por_dia[iso].append(hora_str)

    horas_ocupadas = _json.dumps(horas_por_dia)
    # Mantener compatibilidad: dias_ocupados = días que tienen al menos 1 cita
    dias_ocupados = _json.dumps(list(horas_por_dia.keys()))

    return render(request, 'psicoasis/home.html', {
        'form': form,
        'exito': exito,
        'hoy_iso': hoy.isoformat(),
        'dias_ocupados': dias_ocupados,
        'horas_ocupadas': horas_ocupadas,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            u = User.objects.get(email=email)
            username = u.username
        except User.DoesNotExist:
            username = email
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            rol = getattr(getattr(user, 'perfil', None), 'rol', 'psicologo')
            if rol == 'estudiante':
                return redirect('dashboard_estudiante')
            elif rol in ('padre', 'tutor'):
                return redirect('dashboard_padre')
            elif rol == 'profesor':
                return redirect('dashboard_profesor')
            return redirect('dashboard')
        error = 'Correo o contraseña incorrectos.'
    return render(request, 'psicoasis/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('home')

def registro_view(request):
    if request.user.is_authenticated:
        rol = getattr(getattr(request.user, 'perfil', None), 'rol', 'psicologo')
        if rol == 'estudiante':
            return redirect('dashboard_estudiante')
        elif rol in ('padre', 'tutor'):
            return redirect('dashboard_padre')
        elif rol == 'profesor':
            return redirect('dashboard_profesor')
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            rol = form.cleaned_data.get('rol', 'psicologo')
            perfil, _ = Perfil.objects.get_or_create(usuario=user)
            perfil.rol = rol
            perfil.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.first_name}! Tu cuenta fue creada.')
            if rol == 'estudiante':
                return redirect('dashboard_estudiante')
            return redirect('dashboard')
    else:
        form = RegistroForm()
    return render(request, 'psicoasis/registro.html', {'form': form})

@login_required
def dashboard_view(request):
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)
    notificaciones_no_leidas = Notificacion.objects.filter(leida=False).count()
    notificaciones_recientes = Notificacion.objects.filter(leida=False).order_by('-fecha')[:5]

    # --- Datos para gráficas ---
    # Casos por motivo
    casos_por_motivo = list(
        Caso.objects.values('motivo').annotate(total=Count('id')).order_by('-total')[:6]
    )
    motivos_labels = [c['motivo'].replace('_', ' ').title() for c in casos_por_motivo]
    motivos_data = [c['total'] for c in casos_por_motivo]

    # Atenciones (reuniones realizadas) por mes - últimos 6 meses
    meses_labels = []
    meses_data = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1) - timedelta(days=i*28)
        count = Reunion.objects.filter(fecha__year=d.year, fecha__month=d.month, estado='realizada').count()
        meses_labels.append(d.strftime('%b'))
        meses_data.append(count)

    # Distribución de estudiantes por grado (top 8)
    grados_data_qs = list(
        Estudiante.objects.filter(activo=True).values('grado').annotate(total=Count('id')).order_by('grado')[:8]
    )
    grados_labels = [g['grado'] for g in grados_data_qs]
    grados_data = [g['total'] for g in grados_data_qs]

    # Reuniones por estado
    estados_reunion = list(
        Reunion.objects.values('estado').annotate(total=Count('id'))
    )
    estados_labels = [e['estado'].title() for e in estados_reunion]
    estados_data = [e['total'] for e in estados_reunion]

    return render(request, 'psicoasis/dashboard.html', {
        'casos_activos': Caso.objects.filter(estado='activo').count(),
        'total_estudiantes': Estudiante.objects.filter(activo=True).count(),
        'total_informes': Informe.objects.count(),
        'reuniones_hoy': Reunion.objects.filter(fecha=hoy).count(),
        'proximas_reuniones': Reunion.objects.filter(
            fecha__gte=hoy, fecha__lte=fin_semana,
            estado__in=['pendiente', 'confirmada']
        ).select_related('estudiante').order_by('fecha', 'hora')[:8],
        'hoy': hoy,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'notificaciones_recientes': notificaciones_recientes,
        'total_docentes': Docente.objects.filter(activo=True).count(),
        # Gráficas
        'motivos_labels': json.dumps(motivos_labels),
        'motivos_data': json.dumps(motivos_data),
        'meses_labels': json.dumps(meses_labels),
        'meses_data': json.dumps(meses_data),
        'grados_labels': json.dumps(grados_labels),
        'grados_data': json.dumps(grados_data),
        'estados_labels': json.dumps(estados_labels),
        'estados_data': json.dumps(estados_data),
    })

@login_required
def notificaciones_view(request):
    notificaciones = Notificacion.objects.all().order_by('-fecha')
    Notificacion.objects.filter(leida=False).update(leida=True)
    return render(request, 'psicoasis/notificaciones.html', {'notificaciones': notificaciones})

@login_required
def notificacion_marcar_leida(request, pk):
    if request.method == 'POST':
        n = get_object_or_404(Notificacion, pk=pk)
        n.leida = True
        n.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

@login_required
def citas_publicas_view(request):
    citas = CitaPublica.objects.all().order_by('-fecha_solicitud')
    return render(request, 'psicoasis/citas_publicas.html', {'citas': citas})

@login_required
def cita_publica_atender(request, pk):
    cita = get_object_or_404(CitaPublica, pk=pk)
    if request.method == 'POST':
        cita.estado = request.POST.get('estado', 'atendida')
        cita.notas_internas = request.POST.get('notas_internas', '')
        cita.save()
        messages.success(request, f'Cita de {cita.nombre} actualizada.')
        return redirect('citas_publicas')
    return render(request, 'psicoasis/cita_publica_detalle.html', {'cita': cita})

@login_required
def estudiantes_list(request):
    q = request.GET.get('q', '').strip()
    grado = request.GET.get('grado', '')
    qs = Estudiante.objects.filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(grado__icontains=q))
    if grado:
        qs = qs.filter(grado=grado)
    return render(request, 'psicoasis/estudiantes_list.html', {
        'estudiantes': qs, 'query': q, 'grado_filtro': grado,
        'grados': Estudiante.GRADOS, 'total': qs.count(),
    })

@login_required
def estudiante_nuevo(request):
    if request.method == 'POST':
        form = EstudianteForm(request.POST)
        if form.is_valid():
            est = form.save()
            messages.success(request, f'Estudiante {est.nombre} {est.apellido} registrado.')
            return redirect('estudiante_detalle', pk=est.pk)
    else:
        form = EstudianteForm()
    return render(request, 'psicoasis/estudiante_form.html', {
        'form': form, 'titulo': 'Nuevo Estudiante', 'accion': 'Registrar estudiante',
    })

@login_required
def estudiante_detalle(request, pk):
    est = get_object_or_404(Estudiante, pk=pk)
    # Check-ins emocionales del estudiante (si tiene cuenta vinculada)
    checkins = []
    usuario_vinculado = getattr(est, 'usuario_vinculado', None)
    if usuario_vinculado:
        usuario_est = getattr(usuario_vinculado, 'usuario', None)
        if usuario_est:
            checkins = AutoevaluacionEstudiante.objects.filter(
                estudiante=usuario_est
            ).order_by('-fecha')[:14]
    return render(request, 'psicoasis/estudiante_detalle.html', {
        'estudiante': est,
        'casos': est.casos.all(),
        'reuniones': est.reuniones.order_by('-fecha', '-hora'),
        'informes': Informe.objects.filter(estudiante=est).order_by('-fecha_creacion'),
        'checkins': checkins,
        'usuario_vinculado': getattr(getattr(est, 'usuario_vinculado', None), 'usuario', None),
    })

@login_required
def estudiante_editar(request, pk):
    est = get_object_or_404(Estudiante, pk=pk)
    if request.method == 'POST':
        form = EstudianteForm(request.POST, instance=est)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('estudiante_detalle', pk=pk)
    else:
        form = EstudianteForm(instance=est)
    return render(request, 'psicoasis/estudiante_form.html', {
        'form': form, 'titulo': f'Editar — {est.nombre} {est.apellido}',
        'accion': 'Guardar cambios', 'estudiante': est,
    })

@login_required
def docentes_list(request):
    q = request.GET.get('q', '').strip()
    area = request.GET.get('area', '')
    qs = Docente.objects.filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
    if area:
        qs = qs.filter(area=area)
    return render(request, 'psicoasis/docentes_list.html', {
        'docentes': qs, 'query': q, 'area_filtro': area,
        'areas': Docente.AREAS, 'total': qs.count(),
    })

@login_required
def docente_nuevo(request):
    if request.method == 'POST':
        form = DocenteForm(request.POST)
        if form.is_valid():
            doc = form.save()
            messages.success(request, f'Docente {doc.nombre} {doc.apellido} registrado.')
            return redirect('docente_detalle', pk=doc.pk)
    else:
        form = DocenteForm()
    return render(request, 'psicoasis/docente_form.html', {
        'form': form, 'titulo': 'Nuevo Docente', 'accion': 'Registrar docente',
    })

@login_required
def docente_detalle(request, pk):
    doc = get_object_or_404(Docente, pk=pk)
    return render(request, 'psicoasis/docente_detalle.html', {
        'docente': doc,
        'seguimientos': doc.seguimientos.all(),
    })

@login_required
def docente_editar(request, pk):
    doc = get_object_or_404(Docente, pk=pk)
    if request.method == 'POST':
        form = DocenteForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados.')
            return redirect('docente_detalle', pk=pk)
    else:
        form = DocenteForm(instance=doc)
    return render(request, 'psicoasis/docente_form.html', {
        'form': form, 'titulo': f'Editar — {doc.nombre} {doc.apellido}',
        'accion': 'Guardar cambios', 'docente': doc,
    })

@login_required
def seguimiento_docente_nuevo(request):
    doc_id = request.GET.get('docente') or request.POST.get('docente')
    doc_pre = None
    if doc_id:
        try:
            doc_pre = Docente.objects.get(pk=int(doc_id))
        except (Docente.DoesNotExist, ValueError):
            pass
    if request.method == 'POST':
        form = SeguimientoDocenteForm(request.POST)
        if form.is_valid():
            seg = form.save(commit=False)
            seg.psicologo = request.user
            seg.save()
            messages.success(request, 'Seguimiento registrado.')
            return redirect('docente_detalle', pk=seg.docente.pk)
    else:
        initial = {'docente': doc_pre} if doc_pre else {}
        form = SeguimientoDocenteForm(initial=initial)
    return render(request, 'psicoasis/seguimiento_docente_form.html', {
        'form': form, 'doc_pre': doc_pre,
        'docentes': Docente.objects.filter(activo=True).order_by('apellido'),
    })

@login_required
def caso_nuevo(request):
    estudiante_id = request.GET.get('estudiante') or request.POST.get('estudiante')
    estudiante_pre = None
    if estudiante_id:
        try:
            estudiante_pre = Estudiante.objects.get(pk=int(estudiante_id))
        except (Estudiante.DoesNotExist, ValueError):
            pass
    if request.method == 'POST':
        form = CasoForm(request.POST)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.psicologo = request.user
            caso.save()
            messages.success(request, 'Caso registrado correctamente.')
            return redirect('estudiante_detalle', pk=caso.estudiante.pk)
    else:
        initial = {}
        if estudiante_pre:
            initial['estudiante'] = estudiante_pre
        form = CasoForm(initial=initial)
    return render(request, 'psicoasis/caso_form.html', {
        'form': form, 'estudiante_pre': estudiante_pre,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
    })

@login_required
def caso_editar(request, pk):
    caso = get_object_or_404(Caso, pk=pk)
    if request.method == 'POST':
        form = CasoForm(request.POST, instance=caso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Caso actualizado.')
            return redirect('estudiante_detalle', pk=caso.estudiante.pk)
    else:
        form = CasoForm(instance=caso)
    return render(request, 'psicoasis/caso_form.html', {
        'form': form, 'estudiante_pre': caso.estudiante,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
        'titulo': 'Editar caso', 'caso': caso,
    })

@login_required
def caso_eliminar(request, pk):
    caso = get_object_or_404(Caso, pk=pk)
    est_pk = caso.estudiante.pk
    if request.method == 'POST':
        caso.delete()
        messages.success(request, 'Caso eliminado.')
        return redirect('estudiante_detalle', pk=est_pk)
    return render(request, 'psicoasis/confirmar_eliminar.html', {
        'objeto': f'el caso de {caso.estudiante.get_full_name()} — {caso.get_motivo_display()}',
        'cancelar_url': f'/estudiantes/{est_pk}/',
    })

@login_required
def reuniones_list(request):
    estado = request.GET.get('estado', '')
    qs = Reunion.objects.select_related('estudiante').order_by('-fecha', '-hora')
    if estado:
        qs = qs.filter(estado=estado)
    return render(request, 'psicoasis/reuniones_list.html', {
        'reuniones': qs, 'estado_filtro': estado, 'total': qs.count(),
    })

@login_required
def reunion_nueva(request):
    est_id = request.GET.get('estudiante')
    fecha_pre = request.GET.get('fecha', '')
    if request.method == 'POST':
        form = ReunionForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.psicologo = request.user
            r.save()
            messages.success(request, f'Cita agendada para {r.estudiante.nombre} el {r.fecha}.')
            return redirect('calendario')
    else:
        initial = {}
        if est_id:
            initial['estudiante'] = est_id
        if fecha_pre:
            initial['fecha'] = fecha_pre
        form = ReunionForm(initial=initial)
    return render(request, 'psicoasis/reunion_form.html', {
        'form': form,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
        'titulo': 'Nueva Reunión / Cita',
        'fecha_pre': fecha_pre,
    })

@login_required
def reunion_editar(request, pk):
    reunion = get_object_or_404(Reunion, pk=pk)
    if request.method == 'POST':
        form = ReunionForm(request.POST, instance=reunion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reunión actualizada.')
            return redirect('reuniones_list')
    else:
        form = ReunionForm(instance=reunion)
    return render(request, 'psicoasis/reunion_form.html', {
        'form': form,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
        'titulo': 'Editar Reunión', 'reunion': reunion,
    })

@login_required
def reunion_cambiar_estado(request, pk):
    if request.method == 'POST':
        reunion = get_object_or_404(Reunion, pk=pk)
        nuevo = request.POST.get('estado', '')
        validos = [k for k, v in Reunion.ESTADOS]
        if nuevo in validos:
            reunion.estado = nuevo
            reunion.save()
            return JsonResponse({'ok': True, 'label': reunion.get_estado_display(), 'estado': nuevo})
    return JsonResponse({'ok': False}, status=400)

@login_required
def calendario_view(request):
    hoy = date.today()
    year = int(request.GET.get('year', hoy.year))
    month = int(request.GET.get('month', hoy.month))
    if month < 1: month = 1
    if month > 12: month = 12

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    cal = calendar.monthcalendar(year, month)
    reuniones_mes = Reunion.objects.filter(
        fecha__year=year, fecha__month=month
    ).select_related('estudiante').order_by('fecha', 'hora')

    reuniones_por_dia = {}
    for r in reuniones_mes:
        d = r.fecha.day
        if d not in reuniones_por_dia:
            reuniones_por_dia[d] = []
        reuniones_por_dia[d].append(r)

    todas = list(Reunion.objects.select_related('estudiante').order_by('fecha', 'hora'))
    proximas = [r for r in todas if r.fecha >= hoy and r.estado in ('pendiente', 'confirmada')][:8]

    nombres_meses = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
                     'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    return render(request, 'psicoasis/calendario.html', {
        'todas_reuniones': todas,
        'proximas_reuniones': proximas,
        'hoy': hoy,
        'year': year, 'month': month,
        'nombre_mes': nombres_meses[month],
        'cal': cal,
        'reuniones_por_dia': reuniones_por_dia,
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
        'reuniones_mes': reuniones_mes,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
    })

@login_required
def agenda_cita_view(request):
    if request.method == 'POST':
        form = ReunionForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.psicologo = request.user
            r.save()
            messages.success(request, f'Cita agendada para {r.estudiante.nombre} el {r.fecha}.')
            return redirect('calendario')
    else:
        form = ReunionForm()
    return render(request, 'psicoasis/agenda_cita.html', {
        'form': form,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
    })

@login_required
def informes_list(request):
    qs = Informe.objects.select_related('estudiante').order_by('-fecha_creacion')
    return render(request, 'psicoasis/informes_list.html', {'informes': qs})

@login_required
def informe_nuevo(request):
    est_id = request.GET.get('estudiante')
    if request.method == 'POST':
        form = InformeForm(request.POST)
        if form.is_valid():
            inf = form.save(commit=False)
            inf.psicologo = request.user
            inf.save()
            messages.success(request, 'Informe creado.')
            return redirect('informe_detalle', pk=inf.pk)
    else:
        initial = {'estudiante': est_id} if est_id else {}
        form = InformeForm(initial=initial)
    return render(request, 'psicoasis/informe_form.html', {
        'form': form,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
    })

@login_required
def informe_detalle(request, pk):
    return render(request, 'psicoasis/informe_detalle.html', {
        'informe': get_object_or_404(Informe, pk=pk),
    })

@login_required
def informe_editar(request, pk):
    informe = get_object_or_404(Informe, pk=pk)
    if request.method == 'POST':
        form = InformeForm(request.POST, instance=informe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informe actualizado.')
            return redirect('informe_detalle', pk=pk)
    else:
        form = InformeForm(instance=informe)
    return render(request, 'psicoasis/informe_form.html', {
        'form': form,
        'estudiantes': Estudiante.objects.filter(activo=True).order_by('apellido'),
        'informe': informe,
    })

@login_required
def informe_eliminar(request, pk):
    informe = get_object_or_404(Informe, pk=pk)
    if request.method == 'POST':
        informe.delete()
        messages.success(request, 'Informe eliminado.')
        return redirect('informes_list')
    return render(request, 'psicoasis/confirmar_eliminar.html', {
        'objeto': f'el informe "{informe.titulo}"',
        'cancelar_url': f'/informes/{pk}/',
    })

@login_required
def informes_estudiante_todos(request, pk):
    """Genera una página HTML imprimible con TODOS los informes del estudiante."""
    estudiante = get_object_or_404(Estudiante, pk=pk)
    informes = Informe.objects.filter(estudiante=estudiante).order_by('-fecha_creacion')
    return render(request, 'psicoasis/informes_todos_print.html', {
        'estudiante': estudiante,
        'informes': informes,
    })

@login_required
def bienestar_view(request):
    return render(request, 'psicoasis/bienestar.html', {
        'herramientas': RecursoWellness.objects.filter(categoria='herramienta_autocuidado', activo=True)[:3],
        'biblioteca': RecursoWellness.objects.filter(categoria='biblioteca_emocional', activo=True)[:3],
        'multimedia': RecursoWellness.objects.filter(categoria='recursos_multimedia', activo=True)[:3],
        'mini_planes': RecursoWellness.objects.filter(categoria='mini_planes', activo=True)[:3],
    })

@login_required
def herramientas_autocuidado(request):
    return render(request, 'psicoasis/herramientas_autocuidado.html', {
        'recursos': RecursoWellness.objects.filter(categoria='herramienta_autocuidado', activo=True),
    })

@login_required
def biblioteca_emocional(request):
    return render(request, 'psicoasis/biblioteca_emocional.html', {
        'recursos': RecursoWellness.objects.filter(categoria='biblioteca_emocional', activo=True),
    })

@login_required
def recursos_multimedia(request):
    return render(request, 'psicoasis/recursos_multimedia.html', {
        'recursos': RecursoWellness.objects.filter(categoria='recursos_multimedia', activo=True),
    })

@login_required
def mini_planes(request):
    return render(request, 'psicoasis/mini_planes.html', {
        'recursos': RecursoWellness.objects.filter(categoria='mini_planes', activo=True),
    })

@login_required
def vlog_salud_mental(request):
    return render(request, 'psicoasis/vlog.html', {
        'recursos': RecursoWellness.objects.filter(categoria='vlog', activo=True),
    })

@login_required
def foros_view(request):
    categoria = request.GET.get('cat', '')
    temas = ForoTema.objects.filter(activo=True)
    if categoria:
        temas = temas.filter(categoria=categoria)
    return render(request, 'psicoasis/foros.html', {
        'temas': temas,
        'categorias': ForoTema.CATEGORIAS,
        'categoria_filtro': categoria,
        'form': ForoTemaForm(),
    })

@login_required
def foro_nuevo_tema(request):
    if request.method == 'POST':
        form = ForoTemaForm(request.POST)
        if form.is_valid():
            tema = form.save(commit=False)
            tema.autor = request.user
            tema.save()
            messages.success(request, 'Tema creado exitosamente.')
            return redirect('foro_tema', pk=tema.pk)
    return redirect('foros')

@login_required
def foro_tema_view(request, pk):
    tema = get_object_or_404(ForoTema, pk=pk, activo=True)
    respuestas = tema.respuestas.all()
    form = ForoRespuestaForm()
    if request.method == 'POST':
        form = ForoRespuestaForm(request.POST)
        if form.is_valid():
            resp = form.save(commit=False)
            resp.tema = tema
            resp.autor = request.user
            resp.save()
            messages.success(request, 'Respuesta publicada.')
            return redirect('foro_tema', pk=pk)
    return render(request, 'psicoasis/foro_tema.html', {
        'tema': tema, 'respuestas': respuestas, 'form': form,
    })

@login_required
def buscar_view(request):
    q = request.GET.get('q', '').strip()
    estudiantes, reuniones, informes = [], [], []
    if q:
        estudiantes = Estudiante.objects.filter(
            Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(grado__icontains=q), activo=True
        )
        reuniones = Reunion.objects.filter(
            Q(estudiante__nombre__icontains=q) | Q(estudiante__apellido__icontains=q) | Q(motivo__icontains=q)
        ).select_related('estudiante')[:10]
        informes = Informe.objects.filter(
            Q(titulo__icontains=q) | Q(contenido__icontains=q)
        ).select_related('estudiante')[:5]
    return render(request, 'psicoasis/buscar.html', {
        'query': q, 'estudiantes': estudiantes, 'reuniones': reuniones, 'informes': informes,
    })

# ─── CONTEXT PROCESSOR ──────────────────────────────────────────────────

def notif_context(request):
    if request.user.is_authenticated:
        from .models import Notificacion
        return {'notif_no_leidas': Notificacion.objects.filter(leida=False).count()}
    return {'notif_no_leidas': 0}

# ── SERVICIO DE ASEO ──────────────────────────────────────────

def notif_context_profesor(request):
    """Context processor para notificaciones del profesor."""
    count = 0
    if request.user.is_authenticated:
        rol = getattr(getattr(request.user, 'perfil', None), 'rol', None)
        if rol == 'profesor':
            from .models import NotificacionProfesor
            count = NotificacionProfesor.objects.filter(
                profesor=request.user, leida=False
            ).count()
    return {'notif_count_prof': count}


@login_required
def aseo_list(request):
    q = request.GET.get('q', '').strip()
    area = request.GET.get('area', '')
    qs = PersonalAseo.objects.filter(activo=True)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q))
    if area:
        qs = qs.filter(area_asignada=area)
    return render(request, 'psicoasis/aseo_list.html', {
        'personal': qs, 'query': q, 'area_filtro': area,
        'areas': PersonalAseo.AREAS, 'total': qs.count(),
    })

@login_required
def aseo_nuevo(request):
    if request.method == 'POST':
        form = PersonalAseoForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f'{p.nombre} {p.apellido} registrado.')
            return redirect('aseo_detalle', pk=p.pk)
    else:
        form = PersonalAseoForm()
    return render(request, 'psicoasis/aseo_form.html', {
        'form': form, 'titulo': 'Nuevo Personal de Aseo', 'accion': 'Registrar',
    })

@login_required
def aseo_detalle(request, pk):
    p = get_object_or_404(PersonalAseo, pk=pk)
    return render(request, 'psicoasis/aseo_detalle.html', {'persona': p})

@login_required
def aseo_editar(request, pk):
    p = get_object_or_404(PersonalAseo, pk=pk)
    if request.method == 'POST':
        form = PersonalAseoForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('aseo_detalle', pk=pk)
    else:
        form = PersonalAseoForm(instance=p)
    return render(request, 'psicoasis/aseo_form.html', {
        'form': form, 'titulo': f'Editar — {p.nombre} {p.apellido}',
        'accion': 'Guardar cambios', 'persona': p,
    })

# ── ASISTENTE IA ──────────────────────────────────────────────
@login_required
def asistente_ia_view(request):
    return render(request, 'psicoasis/asistente_ia.html')

@login_required
def asistente_ia_chat(request):
    """Proxy seguro hacia la API de Claude — la clave queda en el servidor."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        body = json.loads(request.body)
        mensajes = body.get('messages', [])
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    import urllib.request
    import urllib.error
    import os

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'API key no configurada. Agrega ANTHROPIC_API_KEY al entorno.'}, status=500)

    payload = json.dumps({
        'model': 'claude-sonnet-4-6-20251001',
        'max_tokens': 1024,
        'system': (
            'Eres PsicoIA, un asistente especializado en psicología escolar integrado en PsicoAsis. '
            'Ayudas a psicólogos escolares con: redacción de informes, estrategias de intervención, '
            'análisis de casos (sin datos reales de pacientes), recursos bibliográficos, orientación '
            'sobre señales de alerta en estudiantes y técnicas psicoeducativas. '
            'Responde siempre en español, de forma clara, empática y profesional. '
            'NO proporcionas diagnósticos clínicos definitivos. '
            'Si el usuario menciona datos personales reales de estudiantes, recuérdale la confidencialidad.'
        ),
        'messages': mensajes,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        texto = data['content'][0]['text']
        return JsonResponse({'respuesta': texto})
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return JsonResponse({'error': f'Error API: {err}'}, status=502)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════
#  PANEL DEL ESTUDIANTE
# ══════════════════════════════════════════════════════════════

def requiere_estudiante(view_func):
    """Decorator: solo estudiantes pueden acceder."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        rol = getattr(getattr(request.user, 'perfil', None), 'rol', 'psicologo')
        if rol != 'estudiante':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@requiere_estudiante
def dashboard_estudiante(request):
    """Panel principal del estudiante."""
    user = request.user
    perfil = getattr(user, 'perfil', None)
    estudiante = getattr(perfil, 'estudiante_vinculado', None)

    # Check-in de hoy
    hoy = date.today()
    checkin_hoy = AutoevaluacionEstudiante.objects.filter(estudiante=user, fecha=hoy).first()

    # Próximas reuniones
    proximas_reuniones = []
    if estudiante:
        proximas_reuniones = Reunion.objects.filter(
            estudiante=estudiante, fecha__gte=hoy, estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora')[:3]

    # Mensajes no leídos de la psicóloga
    mensajes_nuevos = MensajeEstudiante.objects.filter(
        destinatario=user, estado='enviado'
    ).count()

    # Últimos 7 check-ins para el gráfico de humor
    ultimos_checkins = AutoevaluacionEstudiante.objects.filter(
        estudiante=user
    ).order_by('-fecha')[:7]

    # Recursos de bienestar recientes
    recursos = RecursoWellness.objects.filter(activo=True).order_by('-fecha_creacion')[:3]

    ctx = {
        'checkin_hoy': checkin_hoy,
        'proximas_reuniones': proximas_reuniones,
        'mensajes_nuevos': mensajes_nuevos,
        'ultimos_checkins': ultimos_checkins,
        'recursos': recursos,
        'estudiante': estudiante,
        'hoy': hoy,
    }
    return render(request, 'psicoasis/dashboard_estudiante.html', ctx)


@requiere_estudiante
def checkin_emocional(request):
    """Check-in emocional diario del estudiante."""
    hoy = date.today()
    checkin_existente = AutoevaluacionEstudiante.objects.filter(
        estudiante=request.user, fecha=hoy
    ).first()

    if request.method == 'POST':
        emocion = request.POST.get('emocion')
        nota = request.POST.get('nota_privada', '')
        if emocion:
            AutoevaluacionEstudiante.objects.update_or_create(
                estudiante=request.user, fecha=hoy,
                defaults={'emocion': emocion, 'nota_privada': nota}
            )
            messages.success(request, '¡Check-in registrado! Gracias por compartir cómo te sientes.')
            return redirect('dashboard_estudiante')

    historial = AutoevaluacionEstudiante.objects.filter(
        estudiante=request.user
    ).order_by('-fecha')[:14]

    ctx = {
        'checkin_hoy': checkin_existente,
        'historial': historial,
        'hoy': hoy,
        'emociones': AutoevaluacionEstudiante.EMOCIONES,
    }
    return render(request, 'psicoasis/checkin_emocional.html', ctx)


@requiere_estudiante
def mis_citas_estudiante(request):
    """Citas del estudiante."""
    perfil = getattr(request.user, 'perfil', None)
    estudiante = getattr(perfil, 'estudiante_vinculado', None)
    hoy = date.today()

    proximas = []
    pasadas = []
    if estudiante:
        proximas = Reunion.objects.filter(
            estudiante=estudiante, fecha__gte=hoy
        ).order_by('fecha', 'hora')
        pasadas = Reunion.objects.filter(
            estudiante=estudiante, fecha__lt=hoy
        ).order_by('-fecha', '-hora')[:10]

    ctx = {'proximas': proximas, 'pasadas': pasadas, 'estudiante': estudiante, 'hoy': hoy}
    return render(request, 'psicoasis/mis_citas_estudiante.html', ctx)


@requiere_estudiante
def mis_mensajes_estudiante(request):
    """Chat privado entre estudiante y psicóloga."""
    user = request.user
    # Buscar psicólogos (usuarios con rol psicologo)
    psicologos = User.objects.filter(perfil__rol='psicologo', is_active=True)

    # Por defecto chatear con el primer psicólogo disponible
    psicologo = psicologos.first()

    if request.method == 'POST':
        contenido = request.POST.get('contenido', '').strip()
        es_anonimo = request.POST.get('anonimo') == '1'
        if contenido and psicologo:
            MensajeEstudiante.objects.create(
                remitente=user,
                destinatario=psicologo,
                contenido=contenido,
                es_anonimo=es_anonimo
            )
            return redirect('mis_mensajes_estudiante')

    mensajes = []
    if psicologo:
        mensajes = MensajeEstudiante.objects.filter(
            Q(remitente=user, destinatario=psicologo) |
            Q(remitente=psicologo, destinatario=user)
        ).order_by('fecha')
        # Marcar como leídos los del psicólogo
        mensajes.filter(remitente=psicologo, estado='enviado').update(estado='leido')

    ctx = {'mensajes': mensajes, 'psicologo': psicologo}
    return render(request, 'psicoasis/mis_mensajes_estudiante.html', ctx)


@requiere_estudiante
def bienestar_estudiante(request):
    """Centro de bienestar para el estudiante."""
    recursos = RecursoWellness.objects.filter(activo=True).order_by('-fecha_creacion')
    foros = ForoTema.objects.filter(activo=True, categoria__in=['estudiantes', 'bienestar', 'general']).order_by('-fecha_creacion')[:5]
    ctx = {'recursos': recursos, 'foros': foros}
    return render(request, 'psicoasis/bienestar_estudiante.html', ctx)


@requiere_estudiante
def solicitar_cita_estudiante(request):
    """El estudiante solicita una cita desde su panel."""
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        fecha_preferida = request.POST.get('fecha_preferida') or None
        hora_preferida = request.POST.get('hora_preferida') or None
        if motivo:
            nombre = request.user.get_full_name() or request.user.username
            email = request.user.email
            cita = CitaPublica.objects.create(
                nombre=nombre,
                email=email,
                rol='estudiante',
                motivo=motivo,
                fecha_preferida=fecha_preferida,
                hora_preferida=hora_preferida,
            )
            Notificacion.objects.create(
                tipo='cita_publica',
                titulo=f'Cita solicitada por {nombre}',
                mensaje=f'El estudiante {nombre} solicita una cita. Motivo: {motivo[:100]}',
                nombre_solicitante=nombre,
                email_solicitante=email,
                rol_solicitante='estudiante',
                motivo_consulta=motivo,
                fecha_solicitada=fecha_preferida,
            )
            messages.success(request, '¡Tu solicitud fue enviada! La psicóloga te contactará pronto.')
            return redirect('mis_citas_estudiante')
        else:
            messages.error(request, 'Por favor escribe el motivo de la cita.')
    return render(request, 'psicoasis/solicitar_cita_estudiante.html', {})


# ── VISTA DE MENSAJES PARA LA PSICÓLOGA (bandeja de entrada) ──

@login_required
def bandeja_mensajes_psicologo(request):
    """Psicóloga ve y responde los mensajes de estudiantes."""
    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.rol == 'estudiante':
        return redirect('dashboard_estudiante')

    # Conversaciones únicas (un hilo por estudiante)
    conversaciones = []
    estudiantes_que_escribieron = User.objects.filter(
        mensajes_enviados__destinatario=request.user
    ).distinct()

    for est in estudiantes_que_escribieron:
        ultimo = MensajeEstudiante.objects.filter(
            Q(remitente=est, destinatario=request.user) |
            Q(remitente=request.user, destinatario=est)
        ).order_by('-fecha').first()
        no_leidos = MensajeEstudiante.objects.filter(
            remitente=est, destinatario=request.user, estado='enviado'
        ).count()
        conversaciones.append({'usuario': est, 'ultimo': ultimo, 'no_leidos': no_leidos})

    conversaciones.sort(key=lambda x: x['ultimo'].fecha if x['ultimo'] else date.min, reverse=True)

    # Conversación activa
    chat_user_id = request.GET.get('con')
    chat_user = None
    mensajes_chat = []
    if chat_user_id:
        chat_user = get_object_or_404(User, pk=chat_user_id)
        mensajes_chat = MensajeEstudiante.objects.filter(
            Q(remitente=chat_user, destinatario=request.user) |
            Q(remitente=request.user, destinatario=chat_user)
        ).order_by('fecha')
        mensajes_chat.filter(remitente=chat_user, estado='enviado').update(estado='leido')

        if request.method == 'POST':
            contenido = request.POST.get('contenido', '').strip()
            if contenido:
                MensajeEstudiante.objects.create(
                    remitente=request.user,
                    destinatario=chat_user,
                    contenido=contenido
                )
                return redirect(f"{request.path}?con={chat_user_id}")

    ctx = {
        'conversaciones': conversaciones,
        'chat_user': chat_user,
        'mensajes_chat': mensajes_chat,
    }
    return render(request, 'psicoasis/bandeja_mensajes_psicologo.html', ctx)


@login_required
def vincular_estudiante(request, user_id):
    """Psicóloga vincula un usuario estudiante con su registro de Estudiante."""
    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.rol == 'estudiante':
        return redirect('dashboard_estudiante')

    usuario_est = get_object_or_404(User, pk=user_id)
    perfil_est, _ = Perfil.objects.get_or_create(usuario=usuario_est)

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        if estudiante_id:
            try:
                est = Estudiante.objects.get(pk=estudiante_id)
                perfil_est.estudiante_vinculado = est
                perfil_est.rol = 'estudiante'
                perfil_est.save()
                messages.success(request, f'✅ {usuario_est.get_full_name()} vinculado/a con {est.get_full_name()} ({est.grado})')
            except Estudiante.DoesNotExist:
                messages.error(request, 'Estudiante no encontrado.')
        return redirect('cuentas_estudiantes')
    return redirect('cuentas_estudiantes')


@login_required
def cuentas_estudiantes(request):
    """Lista de cuentas de usuario con rol estudiante, para vincularlas al registro."""
    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.rol == 'estudiante':
        return redirect('dashboard_estudiante')

    usuarios_estudiante = User.objects.filter(perfil__rol='estudiante').select_related('perfil__estudiante_vinculado')
    estudiantes_sin_cuenta = Estudiante.objects.filter(usuario_vinculado__isnull=True, activo=True)
    todos_estudiantes = Estudiante.objects.filter(activo=True).order_by('grado', 'apellido')

    ctx = {
        'usuarios_estudiante': usuarios_estudiante,
        'estudiantes_sin_cuenta': estudiantes_sin_cuenta,
        'todos_estudiantes': todos_estudiantes,
    }
    return render(request, 'psicoasis/cuentas_estudiantes.html', ctx)


# ══════════════════════════════════════════════════════════════
#  IA PARA ESTUDIANTES + AGENDAMIENTO AUTOMÁTICO
# ══════════════════════════════════════════════════════════════

# Mapa de temas detectados → motivo de reunión + urgencia
TEMAS_MOTIVOS = {
    'ansiedad':       ('Ansiedad / estrés emocional', 'prioritario'),
    'estres':         ('Estrés y manejo emocional', 'prioritario'),
    'tristeza':       ('Tristeza o estado de ánimo bajo', 'prioritario'),
    'depresion':      ('Estado de ánimo bajo / depresión', 'urgente'),
    'autoestima':     ('Trabajo de autoestima', 'regular'),
    'bullying':       ('Situación de acoso escolar', 'urgente'),
    'acoso':          ('Situación de acoso escolar', 'urgente'),
    'familia':        ('Dificultades familiares', 'prioritario'),
    'notas':          ('Rendimiento académico', 'regular'),
    'academico':      ('Rendimiento académico', 'regular'),
    'amigos':         ('Relaciones interpersonales', 'regular'),
    'soledad':        ('Sentimientos de soledad', 'prioritario'),
    'enojo':          ('Manejo de ira / emociones difíciles', 'regular'),
    'miedo':          ('Manejo de miedos y fobias', 'regular'),
    'concentracion':  ('Dificultades de concentración', 'regular'),
    'sueño':          ('Problemas de sueño', 'regular'),
    'alimentacion':   ('Hábitos de salud', 'regular'),
    'autolesion':     ('Situación de riesgo — autolesión', 'urgente'),
    'suicidio':       ('Situación de riesgo — ideación suicida', 'urgente'),
}

def _detectar_tema(texto):
    """Detecta el tema principal de la pregunta del estudiante."""
    texto_lower = texto.lower()
    for keyword, (motivo, urgencia) in TEMAS_MOTIVOS.items():
        if keyword in texto_lower:
            return keyword, motivo, urgencia
    return 'general', 'Consulta psicológica general', 'regular'


def _calcular_fecha_cita(urgencia):
    """Calcula la próxima fecha disponible según urgencia."""
    from datetime import date, timedelta
    hoy = date.today()
    if urgencia == 'urgente':
        dias = 1
    elif urgencia == 'prioritario':
        dias = 3
    else:
        dias = 7
    # Saltar fines de semana
    fecha = hoy + timedelta(days=dias)
    while fecha.weekday() >= 5:
        fecha += timedelta(days=1)
    return fecha


def _hora_disponible(fecha):
    """Busca un horario disponible para la fecha dada (9am-12pm)."""
    from datetime import time
    horas_posibles = [time(9,0), time(9,30), time(10,0), time(10,30), time(11,0), time(11,30)]
    ocupadas = set(
        Reunion.objects.filter(fecha=fecha, estado__in=['pendiente','confirmada']).values_list('hora', flat=True)
    )
    for h in horas_posibles:
        if h not in ocupadas:
            return h
    return time(12, 0)


@requiere_estudiante
def chat_ia_estudiante(request):
    """Chat de la IA para el estudiante con agendamiento automático."""
    user = request.user
    historial = ConversacionIA.objects.filter(estudiante=user).order_by('fecha')

    if request.method == 'POST':
        data = {}
        try:
            import json as _json
            body = _json.loads(request.body)
            pregunta = body.get('pregunta', '').strip()
        except Exception:
            pregunta = request.POST.get('pregunta', '').strip()

        if not pregunta:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Escribe tu pregunta.'}, status=400)

        # Detectar tema
        keyword, motivo_cita, urgencia = _detectar_tema(pregunta)

        # Llamar a la API de Claude
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        perfil = getattr(user, 'perfil', None)
        estudiante = getattr(perfil, 'estudiante_vinculado', None)
        nombre_est = user.first_name or user.username
        grado_est = estudiante.grado if estudiante else 'desconocido'

        system_prompt = f"""Eres PsicoIA, un asistente de bienestar emocional integrado en PsicoAsis, una plataforma de psicología escolar.
Estás hablando con {nombre_est}, un estudiante de grado {grado_est}.

Tu rol:
- Escuchar con empatía y sin juzgar
- Dar respuestas cortas, cálidas y comprensibles para un adolescente
- Sugerir estrategias básicas de bienestar emocional
- Si detectas crisis (autolesión, suicidio, violencia) indica claramente que debe hablar con la psicóloga YA
- NO hacer diagnósticos ni reemplazar a la psicóloga
- Al final de cada respuesta, si el tema lo amerita, menciona que se agendará una cita con la psicóloga
- Usa emojis ocasionalmente para ser más cercano
- Máximo 4 párrafos cortos por respuesta"""

        respuesta_ia = ""
        try:
            import json as _json
            import urllib.request as _req
            import urllib.error

            payload = _json.dumps({
                "model": "claude-sonnet-4-6-20251001",
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": pregunta}]
            }).encode('utf-8')

            req = _req.Request(
                'https://api.anthropic.com/v1/messages',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                },
                method='POST'
            )
            with _req.urlopen(req, timeout=20) as resp:
                result = _json.loads(resp.read().decode('utf-8'))
                respuesta_ia = result['content'][0]['text']
        except Exception as e:
            respuesta_ia = f"Lo siento, tuve un problema técnico. Por favor habla directamente con la psicóloga. 💚"

        # Agendar cita automáticamente si el tema es relevante
        cita_agendada = None
        fecha_cita = None
        hora_cita = None

        if keyword != 'general' or any(w in pregunta.lower() for w in ['ayuda', 'problema', 'mal', 'triste', 'ansios']):
            fecha_cita = _calcular_fecha_cita(urgencia)
            hora_cita = _hora_disponible(fecha_cita)
            nombre_completo = user.get_full_name() or user.username
            email = user.email or ''

            cita_agendada = CitaPublica.objects.create(
                nombre=nombre_completo,
                email=email,
                rol='estudiante',
                motivo=f"[IA] {motivo_cita} — Pregunta: {pregunta[:100]}",
                fecha_preferida=fecha_cita,
                hora_preferida=hora_cita,
            )

            # Notificar a la psicóloga
            Notificacion.objects.create(
                tipo='cita_publica',
                titulo=f'🤖 Cita sugerida por IA — {nombre_completo}',
                mensaje=f'El estudiante {nombre_completo} consultó a PsicoIA sobre: "{pregunta[:120]}". '
                        f'Se agendó automáticamente para el {fecha_cita.strftime("%d/%m/%Y")} a las {hora_cita.strftime("%H:%M")}.',
                nombre_solicitante=nombre_completo,
                email_solicitante=email,
                rol_solicitante='estudiante',
                motivo_consulta=motivo_cita,
                fecha_solicitada=fecha_cita,
                hora_solicitada=hora_cita,
            )

        # Guardar en historial
        conv = ConversacionIA.objects.create(
            estudiante=user,
            pregunta=pregunta,
            respuesta=respuesta_ia,
            tema_detectado=keyword,
            cita_sugerida=cita_agendada,
        )

        import json as _json
        from django.http import JsonResponse
        return JsonResponse({
            'respuesta': respuesta_ia,
            'cita': {
                'agendada': cita_agendada is not None,
                'fecha': fecha_cita.strftime('%d/%m/%Y') if fecha_cita else None,
                'hora': hora_cita.strftime('%H:%M') if hora_cita else None,
                'motivo': motivo_cita if cita_agendada else None,
                'urgencia': urgencia if cita_agendada else None,
            }
        })

    return render(request, 'psicoasis/chat_ia_estudiante.html', {'historial': historial})


# ══════════════════════════════════════════════════════════════
#  FORO EMOCIONAL — PSICÓLOGA PUBLICA, ESTUDIANTES VEN
# ══════════════════════════════════════════════════════════════

@requiere_estudiante
def foro_emocional_estudiante(request):
    """Vista del foro emocional para estudiantes."""
    categoria = request.GET.get('cat', '')
    publicaciones = PublicacionForo.objects.filter(activo=True)
    if categoria:
        publicaciones = publicaciones.filter(categoria=categoria)
    ctx = {
        'publicaciones': publicaciones,
        'categorias': PublicacionForo.CATEGORIAS,
        'cat_activa': categoria,
    }
    return render(request, 'psicoasis/foro_emocional_estudiante.html', ctx)


@requiere_estudiante
def foro_publicacion_detalle(request, pk):
    """Detalle de una publicación del foro emocional."""
    pub = get_object_or_404(PublicacionForo, pk=pk, activo=True)
    return render(request, 'psicoasis/foro_publicacion_detalle.html', {'pub': pub})


@login_required
def foro_emocional_psicologo(request):
    """La psicóloga gestiona sus publicaciones del foro emocional."""
    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.rol == 'estudiante':
        return redirect('foro_emocional_estudiante')

    publicaciones = PublicacionForo.objects.filter(autor=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'crear':
            titulo = request.POST.get('titulo', '').strip()
            contenido = request.POST.get('contenido', '').strip()
            categoria = request.POST.get('categoria', 'general')
            tipo = request.POST.get('tipo', 'mensaje')
            fijado = request.POST.get('fijado') == '1'
            imagen_url = request.POST.get('imagen_url', '').strip()
            if titulo and contenido:
                PublicacionForo.objects.create(
                    titulo=titulo, contenido=contenido,
                    categoria=categoria, tipo=tipo,
                    fijado=fijado, imagen_url=imagen_url,
                    autor=request.user, activo=True,
                )
                messages.success(request, f'✅ Publicación "{titulo}" creada y visible para estudiantes.')
            return redirect('foro_emocional_psicologo')

        elif action == 'eliminar':
            pk = request.POST.get('pk')
            PublicacionForo.objects.filter(pk=pk, autor=request.user).update(activo=False)
            messages.success(request, 'Publicación eliminada.')
            return redirect('foro_emocional_psicologo')

        elif action == 'fijar':
            pk = request.POST.get('pk')
            pub = get_object_or_404(PublicacionForo, pk=pk, autor=request.user)
            pub.fijado = not pub.fijado
            pub.save()
            return redirect('foro_emocional_psicologo')

    ctx = {
        'publicaciones': publicaciones,
        'categorias': PublicacionForo.CATEGORIAS,
        'tipos': PublicacionForo.TIPOS,
    }
    return render(request, 'psicoasis/foro_emocional_psicologo.html', ctx)


# ============================================================
# MÓDULO PADRES/TUTORES — IMPORTS ADICIONALES
# ============================================================
from .models import (
    VinculoPadreTutor, ConfigPrivacidadPadre, NotificacionPadre,
    CitaPadre, MensajePadre, ForoTemaPadres, ForoRespuestaPadres,
    ReaccionForoPadres, RecomendacionPadre, LogActividadPadre,
)
from .forms import (
    VinculoPadreTutorForm, ConfigPrivacidadPadreForm, CitaPadreForm,
    CitaPadreNotasForm, MensajePadreForm, ForoTemaPadresForm,
    ForoRespuestaPadresForm, RecomendacionPadreForm, RegistroPadreForm,
)
from .services_padres import (
    get_hijos_de_padre, get_vinculos_de_padre, verificar_acceso_padre,
    obtener_resumen_emocional_hijo, get_contadores_dashboard_padre,
    crear_notificacion_padre, registrar_log_padre,
    generar_recomendaciones_automaticas,
)


# ============================================================
# MÓDULO PADRES/TUTORES — VISTAS
# ============================================================
# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _es_padre(user):
    """True si el usuario tiene rol padre o tutor."""
    rol = getattr(getattr(user, 'perfil', None), 'rol', None)
    return rol in ('padre', 'tutor')

def _es_psicologo(user):
    rol = getattr(getattr(user, 'perfil', None), 'rol', None)
    return rol == 'psicologo'

def _get_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0] if x else request.META.get('REMOTE_ADDR')


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD DEL PADRE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dashboard_padre(request):
    """Panel principal del padre/tutor."""
    if not _es_padre(request.user):
        messages.error(request, 'Acceso restringido.')
        return redirect('home')

    from .models import (
        VinculoPadreTutor, NotificacionPadre, CitaPadre,
        MensajePadre, RecomendacionPadre,
    )
    from .services_padres import (
        get_vinculos_de_padre, obtener_resumen_emocional_hijo,
        get_contadores_dashboard_padre, registrar_log_padre,
    )

    registrar_log_padre(request.user, 'ver_dashboard', request=request)

    vinculos = get_vinculos_de_padre(request.user)
    hoy = timezone.now().date()

    # Resumen por hijo
    resumenes = []
    for vinculo in vinculos:
        resumen = obtener_resumen_emocional_hijo(vinculo.hijo, request.user)
        resumenes.append({
            'vinculo': vinculo,
            'hijo': vinculo.hijo,
            'resumen': resumen,
        })

    # Próximas citas
    proximas_citas = CitaPadre.objects.filter(
        padre=request.user,
        estado__in=['pendiente', 'confirmada'],
        fecha__gte=hoy,
    ).order_by('fecha', 'hora')[:5]

    # Notificaciones no leídas (las más recientes)
    notificaciones = NotificacionPadre.objects.filter(
        padre=request.user, leida=False
    ).order_by('-prioridad', '-fecha')[:8]

    # Mensajes no leídos
    mensajes_no_leidos = MensajePadre.objects.filter(
        destinatario=request.user, estado='enviado'
    ).count()

    # Recomendaciones nuevas
    recomendaciones = RecomendacionPadre.objects.filter(
        padre=request.user, activo=True, leida=False
    ).order_by('-fecha_creacion')[:4]

    contadores = get_contadores_dashboard_padre(request.user)

    ctx = {
        'vinculos': vinculos,
        'resumenes': resumenes,
        'proximas_citas': proximas_citas,
        'notificaciones': notificaciones,
        'mensajes_no_leidos': mensajes_no_leidos,
        'recomendaciones': recomendaciones,
        'contadores': contadores,
        'hoy': hoy,
    }
    return render(request, 'psicoasis/padres/dashboard_padre.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  MONITOREO EMOCIONAL DEL HIJO
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def seguimiento_emocional_hijo(request, hijo_id):
    """Vista del padre para ver el seguimiento emocional de su hijo."""
    if not _es_padre(request.user):
        messages.error(request, 'Acceso restringido.')
        return redirect('home')

    from .models import (
        Estudiante, VinculoPadreTutor, AutoevaluacionEstudiante,
        NotificacionPadre, Perfil,
    )
    from .services_padres import verificar_acceso_padre, registrar_log_padre

    if not verificar_acceso_padre(request.user, hijo_id, 'puede_ver_emociones'):
        messages.error(request, 'No tienes permiso para ver la información de este estudiante.')
        return redirect('dashboard_padre')

    hijo = get_object_or_404(Estudiante, id=hijo_id)
    vinculo = get_object_or_404(VinculoPadreTutor, padre=request.user, hijo=hijo, activo=True)
    privacidad = getattr(vinculo, 'privacidad', None)
    nivel = privacidad.nivel_detalle if privacidad else 'intermedio'

    registrar_log_padre(request.user, 'ver_emociones_hijo',
                         f'Vio emociones de {hijo.get_full_name()}', request)

    # Obtener usuario del hijo
    try:
        usuario_hijo = Perfil.objects.get(estudiante_vinculado=hijo).usuario
    except Perfil.DoesNotExist:
        usuario_hijo = None

    evaluaciones = []
    ultimas_evaluaciones = []
    if usuario_hijo:
        from datetime import timedelta
        from django.utils import timezone
        hoy = timezone.now().date()
        hace_30 = hoy - timedelta(days=30)
        evaluaciones = AutoevaluacionEstudiante.objects.filter(
            estudiante=usuario_hijo, fecha__gte=hace_30
        ).order_by('fecha')
        ultimas_evaluaciones = evaluaciones.order_by('-fecha')[:7]

    # Alertas del hijo para este padre
    alertas = NotificacionPadre.objects.filter(
        padre=request.user, hijo=hijo,
        tipo__in=['emocion_critica', 'riesgo_alto', 'cambio_brusco']
    ).order_by('-fecha')[:5]

    # Datos para gráfico
    EMOCIONES_ORDEN = {'muy_bien': 5, 'bien': 4, 'regular': 3, 'mal': 2, 'muy_mal': 1}
    grafico_labels = [str(e.fecha) for e in evaluaciones]
    grafico_valores = [EMOCIONES_ORDEN.get(e.emocion, 3) for e in evaluaciones]

    ctx = {
        'hijo': hijo,
        'vinculo': vinculo,
        'privacidad': privacidad,
        'nivel': nivel,
        'evaluaciones': evaluaciones,
        'ultimas_evaluaciones': ultimas_evaluaciones,
        'alertas': alertas,
        'grafico_labels': grafico_labels,
        'grafico_valores': grafico_valores,
        'tiene_usuario': usuario_hijo is not None,
    }
    return render(request, 'psicoasis/padres/seguimiento_emocional_padre.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  NOTIFICACIONES DEL PADRE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def notificaciones_padre(request):
    if not _es_padre(request.user):
        return redirect('home')

    from .models import NotificacionPadre
    notificaciones = NotificacionPadre.objects.filter(padre=request.user).order_by('-fecha')

    # Marcar todas como leídas al visitar
    NotificacionPadre.objects.filter(padre=request.user, leida=False).update(leida=True)

    return render(request, 'psicoasis/padres/notificaciones_padre.html', {
        'notificaciones': notificaciones
    })


@login_required
def notificacion_padre_leida(request, pk):
    """AJAX — marcar una notificación como leída."""
    from .models import NotificacionPadre
    n = get_object_or_404(NotificacionPadre, pk=pk, padre=request.user)
    n.leida = True
    n.save()
    return JsonResponse({'ok': True})


# ═══════════════════════════════════════════════════════════════════════════════
#  CITAS DEL PADRE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def citas_padre(request):
    """Lista de citas del padre + formulario para crear nueva."""
    if not _es_padre(request.user):
        return redirect('home')

    from .models import CitaPadre
    from .forms import CitaPadreForm
    from .services_padres import registrar_log_padre

    from django.utils import timezone
    hoy = timezone.now().date()

    if request.method == 'POST':
        form = CitaPadreForm(request.POST, padre=request.user)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.padre = request.user
            cita.save()
            registrar_log_padre(request.user, 'crear_cita',
                                 f'Cita para {cita.fecha}', request)
            messages.success(request, '✅ Solicitud de cita enviada. La psicóloga la confirmará pronto.')
            return redirect('citas_padre')
    else:
        form = CitaPadreForm(padre=request.user)

    proximas = CitaPadre.objects.filter(
        padre=request.user, fecha__gte=hoy
    ).order_by('fecha', 'hora')
    historial = CitaPadre.objects.filter(
        padre=request.user, fecha__lt=hoy
    ).order_by('-fecha')[:20]

    ctx = {
        'form': form,
        'proximas_citas': proximas,
        'historial_citas': historial,
        'hoy': hoy,
    }
    return render(request, 'psicoasis/padres/citas_padre.html', ctx)


@login_required
def cancelar_cita_padre(request, pk):
    """El padre cancela su propia cita (solo si está pendiente)."""
    if not _es_padre(request.user):
        return redirect('home')

    from .models import CitaPadre
    from .services_padres import registrar_log_padre

    cita = get_object_or_404(CitaPadre, pk=pk, padre=request.user)
    if cita.estado == 'pendiente':
        cita.estado = 'cancelada'
        cita.save()
        registrar_log_padre(request.user, 'cancelar_cita',
                             f'Canceló cita {cita.id}', request)
        messages.success(request, 'Cita cancelada.')
    else:
        messages.warning(request, 'Solo puedes cancelar citas pendientes.')
    return redirect('citas_padre')


# ─── Gestión de citas de padres para la psicóloga ────────────────────────────

@login_required
def citas_padres_psicologo(request):
    """La psicóloga ve y gestiona todas las citas de padres."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import CitaPadre
    from django.utils import timezone
    hoy = timezone.now().date()
    pendientes = CitaPadre.objects.filter(
        estado='pendiente'
    ).select_related('padre', 'hijo').order_by('fecha', 'hora')
    confirmadas = CitaPadre.objects.filter(
        estado='confirmada', fecha__gte=hoy
    ).select_related('padre', 'hijo').order_by('fecha', 'hora')
    historial = CitaPadre.objects.filter(
        estado__in=['realizada', 'cancelada']
    ).select_related('padre', 'hijo').order_by('-fecha')[:30]

    return render(request, 'psicoasis/padres/citas_padres_psicologo_tpl.html', {
        'pendientes': pendientes,
        'confirmadas': confirmadas,
        'historial': historial,
    })


@login_required
def gestionar_cita_padre(request, pk):
    """La psicóloga confirma/cancela/agrega notas a una cita de padre."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import CitaPadre
    from .forms import CitaPadreNotasForm

    cita = get_object_or_404(CitaPadre, pk=pk)
    if request.method == 'POST':
        form = CitaPadreNotasForm(request.POST, instance=cita)
        if form.is_valid():
            cita_guardada = form.save(commit=False)
            cita_guardada.psicologo = request.user
            cita_guardada.save()
            messages.success(request, 'Cita actualizada.')
            return redirect('citas_padres_psicologo')
    else:
        form = CitaPadreNotasForm(instance=cita)

    return render(request, 'psicoasis/padres/citas_padres_psicologo_tpl.html', {
        'cita': cita, 'form': form
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  MENSAJERÍA PADRE ↔ PSICÓLOGA
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def mensajes_padre(request):
    """Vista de mensajes para el padre."""
    if not _es_padre(request.user):
        return redirect('home')

    from .models import MensajePadre
    from .forms import MensajePadreForm
    from .services_padres import registrar_log_padre

    # Obtener la psicóloga (primer usuario con rol psicologo)
    try:
        from .models import Perfil
        psicologa = Perfil.objects.filter(rol='psicologo').first().usuario
    except Exception:
        psicologa = None

    if request.method == 'POST' and psicologa:
        form = MensajePadreForm(request.POST, request.FILES, padre=request.user)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.remitente = request.user
            msg.destinatario = psicologa
            msg.save()
            registrar_log_padre(request.user, 'enviar_mensaje', request=request)
            messages.success(request, '✅ Mensaje enviado.')
            return redirect('mensajes_padre')
    else:
        form = MensajePadreForm(padre=request.user)

    # Conversación con la psicóloga
    conversacion = []
    if psicologa:
        conversacion = MensajePadre.objects.filter(
            Q(remitente=request.user, destinatario=psicologa) |
            Q(remitente=psicologa, destinatario=request.user)
        ).order_by('fecha')
        # Marcar como leídos los del psicólogo
        MensajePadre.objects.filter(
            remitente=psicologa, destinatario=request.user, estado='enviado'
        ).update(estado='leido')

    ctx = {
        'form': form,
        'conversacion': conversacion,
        'psicologa': psicologa,
    }
    return render(request, 'psicoasis/padres/mensajes_padre.html', ctx)


@login_required
def bandeja_mensajes_padres_psicologo(request):
    """La psicóloga ve todos los mensajes con padres."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import MensajePadre, Perfil

    padre_ids = Perfil.objects.filter(rol__in=['padre', 'tutor']).values_list('usuario_id', flat=True)
    padres_con_mensajes = User.objects.filter(
        Q(mensajes_padre_enviados__destinatario=request.user) |
        Q(mensajes_padre_recibidos__remitente=request.user),
        id__in=padre_ids,
    ).distinct()

    padre_sel_id = request.GET.get('padre_id')
    conversacion = []
    padre_sel = None

    if padre_sel_id:
        padre_sel = get_object_or_404(User, pk=padre_sel_id)
        conversacion = MensajePadre.objects.filter(
            Q(remitente=request.user, destinatario=padre_sel) |
            Q(remitente=padre_sel, destinatario=request.user)
        ).order_by('fecha')
        MensajePadre.objects.filter(
            remitente=padre_sel, destinatario=request.user, estado='enviado'
        ).update(estado='leido')

    if request.method == 'POST' and padre_sel:
        from .forms import MensajePadreForm
        contenido = request.POST.get('contenido', '').strip()
        if contenido:
            MensajePadre.objects.create(
                remitente=request.user,
                destinatario=padre_sel,
                contenido=contenido,
            )
            return redirect(f'{request.path}?padre_id={padre_sel.id}')

    ctx = {
        'padres': padres_con_mensajes,
        'padre_sel': padre_sel,
        'conversacion': conversacion,
    }
    return render(request, 'psicoasis/padres/bandeja_mensajes_padres_tpl.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  FORO EXCLUSIVO DE PADRES
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def foro_padres(request):
    """Lista de temas del foro de padres."""
    if not (_es_padre(request.user) or _es_psicologo(request.user)):
        messages.error(request, 'El foro de padres es exclusivo para padres, tutores y psicóloga.')
        return redirect('home')

    from .models import ForoTemaPadres
    from .forms import ForoTemaPadresForm
    from .services_padres import registrar_log_padre

    categorias = ForoTemaPadres.CATEGORIA_CHOICES
    cat_sel = request.GET.get('categoria', '')

    temas = ForoTemaPadres.objects.filter(activo=True)
    if cat_sel:
        temas = temas.filter(categoria=cat_sel)

    if request.method == 'POST' and _es_padre(request.user):
        form = ForoTemaPadresForm(request.POST)
        if form.is_valid():
            tema = form.save(commit=False)
            tema.autor = request.user
            tema.save()
            registrar_log_padre(request.user, 'foro_crear_tema',
                                 f'Creó tema: {tema.titulo}', request)
            messages.success(request, '✅ Tema publicado correctamente.')
            return redirect('foro_padres')
    else:
        form = ForoTemaPadresForm()

    ctx = {
        'temas': temas,
        'form': form,
        'categorias': categorias,
        'cat_sel': cat_sel,
        'es_padre': _es_padre(request.user),
        'es_psicologo': _es_psicologo(request.user),
    }
    return render(request, 'psicoasis/padres/foro_padres.html', ctx)


@login_required
def foro_padres_tema(request, pk):
    """Detalle de un tema del foro de padres + respuestas."""
    if not (_es_padre(request.user) or _es_psicologo(request.user)):
        return redirect('home')

    from .models import ForoTemaPadres, ForoRespuestaPadres, ReaccionForoPadres
    from .forms import ForoRespuestaPadresForm
    from .services_padres import registrar_log_padre

    tema = get_object_or_404(ForoTemaPadres, pk=pk, activo=True)
    respuestas = tema.respuestas.filter(moderado=False).order_by('fecha')

    if request.method == 'POST' and _es_padre(request.user):
        # Reacción al tema
        if 'reaccionar' in request.POST:
            tipo = request.POST.get('tipo_reaccion', 'me_ayudo')
            ReaccionForoPadres.objects.get_or_create(
                usuario=request.user, tema=tema,
                defaults={'tipo': tipo}
            )
            return redirect('foro_padres_tema', pk=pk)

        form = ForoRespuestaPadresForm(request.POST)
        if form.is_valid():
            resp = form.save(commit=False)
            resp.tema = tema
            resp.autor = request.user
            resp.save()
            registrar_log_padre(request.user, 'foro_comentar',
                                 f'Respondió tema {tema.id}', request)
            return redirect('foro_padres_tema', pk=pk)
    else:
        form = ForoRespuestaPadresForm()

    # Reacciones del tema
    reacciones_tema = {r[0]: ReaccionForoPadres.objects.filter(tema=tema, tipo=r[0]).count()
                       for r in ReaccionForoPadres.TIPO_CHOICES}

    ctx = {
        'tema': tema,
        'respuestas': respuestas,
        'form': form,
        'reacciones': reacciones_tema,
        'es_padre': _es_padre(request.user),
        'es_psicologo': _es_psicologo(request.user),
    }
    return render(request, 'psicoasis/padres/foro_padres.html', ctx)


@login_required
def foro_padres_moderar(request, pk):
    """La psicóloga modera (destaca, fija, elimina) un tema del foro."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import ForoTemaPadres
    tema = get_object_or_404(ForoTemaPadres, pk=pk)
    accion = request.POST.get('accion')
    if accion == 'destacar':
        tema.destacado = not tema.destacado
        tema.save()
        messages.success(request, f"Tema {'destacado' if tema.destacado else 'sin destacar'}.")
    elif accion == 'fijar':
        tema.fijado = not tema.fijado
        tema.save()
        messages.success(request, f"Tema {'fijado' if tema.fijado else 'desfijado'}.")
    elif accion == 'eliminar':
        tema.activo = False
        tema.save()
        messages.success(request, 'Tema eliminado del foro.')
    return redirect('foro_padres')


# ═══════════════════════════════════════════════════════════════════════════════
#  RECOMENDACIONES
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def recomendaciones_padre(request):
    """Vista de recomendaciones personalizadas para el padre."""
    if not _es_padre(request.user):
        return redirect('home')

    from .models import RecomendacionPadre
    recomendaciones = RecomendacionPadre.objects.filter(
        padre=request.user, activo=True
    ).order_by('-fecha_creacion')

    # Marcar como leídas al acceder
    RecomendacionPadre.objects.filter(
        padre=request.user, leida=False
    ).update(leida=True)

    return render(request, 'psicoasis/padres/recomendaciones_padre.html', {
        'recomendaciones': recomendaciones
    })


@login_required
def enviar_recomendacion(request):
    """La psicóloga envía una recomendación a un padre."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .forms import RecomendacionPadreForm
    if request.method == 'POST':
        form = RecomendacionPadreForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.generada_por = 'psicologa'
            rec.save()
            messages.success(request, '✅ Recomendación enviada al padre.')
            return redirect('dashboard')
    else:
        form = RecomendacionPadreForm()

    return render(request, 'psicoasis/enviar_recomendacion.html', {'form': form})


# ═══════════════════════════════════════════════════════════════════════════════
#  GESTIÓN DE PADRES (PSICÓLOGA)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def padres_list(request):
    """La psicóloga ve todos los padres/tutores registrados."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from django.db.models import Count
    from .models import VinculoPadreTutor, Perfil

    padre_ids = Perfil.objects.filter(rol__in=['padre', 'tutor']).values_list('usuario_id', flat=True)
    padres = User.objects.filter(id__in=padre_ids).order_by('last_name', 'first_name')

    vinculos_count = {
        v['padre']: v['total']
        for v in VinculoPadreTutor.objects.filter(activo=True).values('padre').annotate(
            total=Count('id')
        )
    }

    return render(request, 'psicoasis/padres/padres_list.html', {
        'padres': padres,
        'vinculos_count': vinculos_count,
    })


@login_required
def padre_nuevo(request):
    """La psicóloga crea una cuenta de padre/tutor."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .forms import RegistroPadreForm
    from .models import Perfil

    if request.method == 'POST':
        form = RegistroPadreForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(
                username=d['email'],
                email=d['email'],
                password=d['password'],
                first_name=d['first_name'],
                last_name=d['last_name'],
            )
            perfil, _ = Perfil.objects.get_or_create(usuario=user)
            perfil.rol = d['rol']
            perfil.telefono = d.get('telefono', '')
            perfil.save()
            messages.success(request, f'✅ Cuenta creada para {user.get_full_name()}.')
            return redirect('padre_vincular', user_id=user.id)
    else:
        form = RegistroPadreForm()

    return render(request, 'psicoasis/padres/padre_nuevo.html', {'form': form})


@login_required
def padre_vincular(request, user_id):
    """La psicóloga vincula un padre con sus hijos."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import VinculoPadreTutor
    from .forms import VinculoPadreTutorForm

    padre = get_object_or_404(User, pk=user_id)
    vinculos = VinculoPadreTutor.objects.filter(padre=padre)

    if request.method == 'POST':
        form = VinculoPadreTutorForm(request.POST)
        # Quitar el campo padre DESPUÉS del __init__ para evitar KeyError
        form.fields.pop('padre', None)
        if form.is_valid():
            vinculo = form.save(commit=False)
            vinculo.padre = padre
            vinculo.vinculado_por = request.user
            vinculo.save()
            from .models import ConfigPrivacidadPadre
            ConfigPrivacidadPadre.objects.get_or_create(
                vinculo=vinculo,
                defaults={'configurado_por': request.user},
            )
            messages.success(request, f'✅ Vínculo creado con {vinculo.hijo.get_full_name()}.')
            return redirect('padre_vincular', user_id=user_id)
    else:
        form = VinculoPadreTutorForm()
        form.fields.pop('padre', None)

    return render(request, 'psicoasis/padres/padre_vincular.html', {
        'padre': padre, 'form': form, 'vinculos': vinculos,
    })


@login_required
def padre_privacidad(request, vinculo_id):
    """La psicóloga configura la privacidad de un vínculo padre-hijo."""
    if not _es_psicologo(request.user):
        return redirect('dashboard')

    from .models import VinculoPadreTutor, ConfigPrivacidadPadre
    from .forms import ConfigPrivacidadPadreForm

    vinculo = get_object_or_404(VinculoPadreTutor, pk=vinculo_id)
    config, _ = ConfigPrivacidadPadre.objects.get_or_create(
        vinculo=vinculo, defaults={'configurado_por': request.user}
    )

    if request.method == 'POST':
        form = ConfigPrivacidadPadreForm(request.POST, instance=config)
        if form.is_valid():
            conf = form.save(commit=False)
            conf.configurado_por = request.user
            conf.save()
            messages.success(request, '✅ Configuración de privacidad guardada.')
            return redirect('padres_list')
    else:
        form = ConfigPrivacidadPadreForm(instance=config)

    return render(request, 'psicoasis/padres/padre_privacidad.html', {
        'vinculo': vinculo, 'form': form,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORTES PARA EL PADRE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def reporte_emocional_padre(request, hijo_id):
    """Vista de reporte emocional completo del hijo para el padre."""
    if not _es_padre(request.user):
        return redirect('home')

    from .models import (
        Estudiante, AutoevaluacionEstudiante, CitaPadre,
        NotificacionPadre, Perfil,
    )
    from .services_padres import verificar_acceso_padre, registrar_log_padre
    from datetime import timedelta

    if not verificar_acceso_padre(request.user, hijo_id, 'puede_ver_emociones'):
        messages.error(request, 'No tienes acceso a este reporte.')
        return redirect('dashboard_padre')

    hijo = get_object_or_404(Estudiante, id=hijo_id)
    registrar_log_padre(request.user, 'ver_reporte',
                         f'Vio reporte de {hijo.get_full_name()}', request)

    from django.utils import timezone
    hoy = timezone.now().date()
    hace_30 = hoy - timedelta(days=30)
    hace_7 = hoy - timedelta(days=7)

    try:
        usuario_hijo = Perfil.objects.get(estudiante_vinculado=hijo).usuario
        eval_30 = AutoevaluacionEstudiante.objects.filter(
            estudiante=usuario_hijo, fecha__gte=hace_30
        ).order_by('fecha')
        eval_7 = eval_30.filter(fecha__gte=hace_7)
    except Perfil.DoesNotExist:
        eval_30, eval_7 = [], []

    # Estadísticas
    EMOCIONES_ORDEN = {'muy_bien': 5, 'bien': 4, 'regular': 3, 'mal': 2, 'muy_mal': 1}
    from django.db.models import Count as DCount
    distribucion = {}
    if eval_30:
        from collections import Counter
        distribucion = Counter(e.emocion for e in eval_30)

    # Citas del padre con este hijo (o solo padre-psicóloga)
    citas_historial = CitaPadre.objects.filter(
        padre=request.user
    ).filter(Q(hijo=hijo) | Q(tipo_cita='padre_psicologo')).order_by('-fecha')[:10]

    # Alertas históricas
    alertas = NotificacionPadre.objects.filter(
        padre=request.user, hijo=hijo
    ).order_by('-fecha')[:10]

    ctx = {
        'hijo': hijo,
        'eval_30': eval_30,
        'eval_7': eval_7,
        'distribucion': dict(distribucion),
        'citas_historial': citas_historial,
        'alertas': alertas,
        'grafico_labels': [str(e.fecha) for e in eval_30],
        'grafico_valores': [EMOCIONES_ORDEN.get(e.emocion, 3) for e in eval_30],
    }
    return render(request, 'psicoasis/padres/seguimiento_emocional_padre.html', ctx)



# ============================================================
# MÓDULO PROFESORES — IMPORTS ADICIONALES
# ============================================================
from .models import (
    PerfilProfesor, AlertaEstudianteProfesor, CitaProfesor,
    MensajeProfesor, NotificacionProfesor, RecursoProfesor,
    AutoevaluacionProfesor,
)
from .forms import (
    AlertaEstudianteForm, CitaProfesorForm, CitaProfesorGestionForm,
    MensajeProfesorForm, RecursoProfesorForm, AutoevaluacionProfesorForm,
    RespuestaAlertaForm, RegistroProfesorForm,
)
from .services_profesores import (
    es_profesor, get_perfil_profesor,
    get_contadores_dashboard_profesor, registrar_log_profesor,
    obtener_historial_bienestar, get_alertas_activas_profesor,
    crear_notificacion_profesor,
)


# ============================================================
# MÓDULO PROFESORES — VISTAS
# ============================================================
def _requiere_profesor(view_func):
    """Decorator: redirige si el usuario no tiene rol 'profesor'."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not es_profesor(request.user):
            messages.error(request, 'Acceso restringido a profesores.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _requiere_psicologo(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        rol = getattr(getattr(request.user, 'perfil', None), 'rol', None)
        if rol != 'psicologo':
            messages.error(request, 'Solo la psicóloga puede acceder aquí.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _grados_del_profesor(user):
    """Lista de grados del PerfilProfesor vinculado, o [] si no tiene."""
    perfil = get_perfil_profesor(user)
    return perfil.get_grados() if perfil else []


# ═══════════════════════════════════════════════════════════════════════════════
#  PANEL DEL PROFESOR
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def dashboard_profesor(request):
    user = request.user
    perfil = get_perfil_profesor(user)
    grados = _grados_del_profesor(user)
    contadores = get_contadores_dashboard_profesor(user)

    # Últimas alertas enviadas
    alertas_recientes = AlertaEstudianteProfesor.objects.filter(
        profesor=user
    ).order_by('-fecha_creacion')[:5]

    # Próxima cita
    from django.utils import timezone
    proxima_cita = CitaProfesor.objects.filter(
        profesor=user, estado='confirmada',
        fecha_confirmada__gte=timezone.now().date()
    ).order_by('fecha_confirmada', 'hora_confirmada').first()

    # Última autoevaluación
    ultima_autoevaluacion = AutoevaluacionProfesor.objects.filter(
        profesor=user
    ).first()

    # Recursos disponibles
    recursos = RecursoProfesor.objects.filter(
        activo=True
    ).filter(
        Q(para_todos=True) | Q(profesores_especificos=user)
    ).order_by('-fecha_creacion')[:4]

    # Estudiantes de sus grados con alertas activas
    alertas_activas = get_alertas_activas_profesor(user)

    # Notificaciones recientes no leídas
    notificaciones = NotificacionProfesor.objects.filter(
        profesor=user, leida=False
    ).order_by('-fecha')[:5]

    ctx = {
        'perfil': perfil,
        'grados': grados,
        'contadores': contadores,
        'alertas_recientes': alertas_recientes,
        'alertas_activas': alertas_activas,
        'proxima_cita': proxima_cita,
        'ultima_autoevaluacion': ultima_autoevaluacion,
        'recursos': recursos,
        'notificaciones': notificaciones,
    }
    return render(request, 'psicoasis/profesores/dashboard_profesor.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  ALERTAS DE ESTUDIANTES
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def mis_alertas(request):
    """Listado de alertas enviadas por el profesor y formulario para nueva alerta."""
    user = request.user
    grados = _grados_del_profesor(user)

    alertas = AlertaEstudianteProfesor.objects.filter(
        profesor=user
    ).order_by('-fecha_creacion')

    form = AlertaEstudianteForm(grados_prof=grados)

    if request.method == 'POST':
        form = AlertaEstudianteForm(request.POST, grados_prof=grados)
        if form.is_valid():
            alerta = form.save(commit=False)
            alerta.profesor = user
            alerta.save()
            registrar_log_profesor(user, 'alerta_enviada',
                                   f'Alerta sobre {alerta.estudiante}', request)
            messages.success(request, '✅ Alerta enviada a la psicóloga correctamente.')
            return redirect('mis_alertas_profesor')

    ctx = {
        'alertas': alertas,
        'form': form,
        'grados': grados,
    }
    return render(request, 'psicoasis/profesores/mis_alertas.html', ctx)


@_requiere_profesor
def alerta_detalle(request, pk):
    """Detalle de una alerta específica con la respuesta de la psicóloga."""
    alerta = get_object_or_404(AlertaEstudianteProfesor, pk=pk, profesor=request.user)
    return render(request, 'psicoasis/profesores/alerta_detalle.html', {'alerta': alerta})


# ═══════════════════════════════════════════════════════════════════════════════
#  CITAS
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def citas_profesor(request):
    """Citas del profesor: listado + formulario de solicitud."""
    user = request.user

    proximas = CitaProfesor.objects.filter(
        profesor=user, estado__in=('pendiente', 'confirmada')
    ).order_by('fecha_confirmada', 'hora_confirmada')
    historial = CitaProfesor.objects.filter(
        profesor=user, estado__in=('realizada', 'cancelada', 'reagendada')
    ).order_by('-fecha_creacion')

    form = CitaProfesorForm()
    if request.method == 'POST':
        form = CitaProfesorForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.profesor = user
            cita.save()
            registrar_log_profesor(user, 'cita_solicitada',
                                   f'Cita tipo {cita.tipo}', request)
            messages.success(request, '📅 Solicitud de cita enviada. La psicóloga la confirmará pronto.')
            return redirect('citas_profesor')

    ctx = {
        'proximas': proximas,
        'historial': historial,
        'form': form,
    }
    return render(request, 'psicoasis/profesores/citas_profesor.html', ctx)


@_requiere_profesor
def cancelar_cita_profesor(request, pk):
    cita = get_object_or_404(CitaProfesor, pk=pk, profesor=request.user)
    if cita.estado in ('pendiente', 'confirmada'):
        cita.estado = 'cancelada'
        cita.save()
        messages.info(request, 'Cita cancelada.')
    return redirect('citas_profesor')


# ═══════════════════════════════════════════════════════════════════════════════
#  MENSAJERÍA
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def mensajes_profesor(request):
    """Chat del profesor con la psicóloga."""
    user = request.user
    psicologo = User.objects.filter(perfil__rol='psicologo').first()

    if not psicologo:
        messages.error(request, 'No se encontró la psicóloga en el sistema.')
        return redirect('dashboard_profesor')

    # Marcar como leídos los mensajes recibidos
    MensajeProfesor.objects.filter(destinatario=user, leido=False).update(leido=True)

    conversacion = MensajeProfesor.objects.filter(
        Q(remitente=user, destinatario=psicologo) |
        Q(remitente=psicologo, destinatario=user)
    ).order_by('fecha')

    form = MensajeProfesorForm()
    if request.method == 'POST':
        form = MensajeProfesorForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.remitente = user
            msg.destinatario = psicologo
            msg.save()
            registrar_log_profesor(user, 'mensaje_enviado', '', request)
            return redirect('mensajes_profesor')

    ctx = {
        'conversacion': conversacion,
        'psicologo': psicologo,
        'form': form,
    }
    return render(request, 'psicoasis/profesores/mensajes_profesor.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  NOTIFICACIONES
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def notificaciones_profesor(request):
    notifs = NotificacionProfesor.objects.filter(profesor=request.user).order_by('-fecha')
    NotificacionProfesor.objects.filter(profesor=request.user, leida=False).update(leida=True)
    return render(request, 'psicoasis/profesores/notificaciones_profesor.html',
                  {'notificaciones': notifs})


# ═══════════════════════════════════════════════════════════════════════════════
#  RECURSOS
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def recursos_profesor(request):
    """Recursos compartidos por la psicóloga al profesor."""
    user = request.user
    recursos = RecursoProfesor.objects.filter(
        activo=True
    ).filter(
        Q(para_todos=True) | Q(profesores_especificos=user)
    ).order_by('-fecha_creacion')

    categorias = RecursoProfesor.CATEGORIAS
    cat_filter = request.GET.get('cat', '')
    if cat_filter:
        recursos = recursos.filter(categoria=cat_filter)

    registrar_log_profesor(user, 'recurso_visto', '', request)
    ctx = {
        'recursos': recursos,
        'categorias': categorias,
        'cat_filter': cat_filter,
    }
    return render(request, 'psicoasis/profesores/recursos_profesor.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTOEVALUACIÓN DE BIENESTAR
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_profesor
def bienestar_profesor(request):
    """Check-in semanal de bienestar del docente."""
    user = request.user
    historial = obtener_historial_bienestar(user, semanas=10)

    # Verificar si ya hizo check-in esta semana
    from datetime import timedelta
    from django.utils import timezone
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # lunes
    ya_hizo = AutoevaluacionProfesor.objects.filter(
        profesor=user, semana__gte=inicio_semana
    ).exists()

    form = AutoevaluacionProfesorForm()
    if request.method == 'POST' and not ya_hizo:
        form = AutoevaluacionProfesorForm(request.POST)
        if form.is_valid():
            ae = form.save(commit=False)
            ae.profesor = user
            ae.semana = inicio_semana
            ae.save()
            registrar_log_profesor(user, 'autoevaluacion', '', request)
            messages.success(request, '✅ Tu check-in de bienestar fue registrado.')
            return redirect('bienestar_profesor')

    # Datos para gráfica
    data_grafica = [
        {
            'semana': str(ae.semana),
            'bienestar': ae.bienestar,
            'valor': {'excelente': 5, 'bien': 4, 'regular': 3,
                      'agotado': 2, 'en_crisis': 1}.get(ae.bienestar, 3),
        }
        for ae in reversed(list(historial))
    ]

    ctx = {
        'historial': historial,
        'ya_hizo_checkin': ya_hizo,
        'form': form,
        'data_grafica': data_grafica,
    }
    return render(request, 'psicoasis/profesores/bienestar_profesor.html', ctx)


# ═══════════════════════════════════════════════════════════════════════════════
#  GESTIÓN POR LA PSICÓLOGA
# ═══════════════════════════════════════════════════════════════════════════════

@_requiere_psicologo
def profesores_list(request):
    """Panel de la psicóloga: lista de todos los profesores con cuenta."""
    profesores = User.objects.filter(
        perfil__rol='profesor'
    ).select_related('perfil', 'perfil_profesor').order_by('last_name')

    # Alertas pendientes por profesor
    alertas_pendientes = {}
    for p in profesores:
        alertas_pendientes[p.id] = AlertaEstudianteProfesor.objects.filter(
            profesor=p, estado='pendiente'
        ).count()

    ctx = {
        'profesores': profesores,
        'alertas_pendientes': alertas_pendientes,
    }
    return render(request, 'psicoasis/profesores/profesores_list.html', ctx)


@_requiere_psicologo
def profesor_nuevo(request):
    """Crear cuenta de profesor y su Perfil."""
    form = RegistroProfesorForm()
    if request.method == 'POST':
        form = RegistroProfesorForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear Perfil con rol profesor
            Perfil.objects.create(usuario=user, rol='profesor', cargo='Docente')
            # Crear PerfilProfesor vacío
            PerfilProfesor.objects.create(usuario=user)
            messages.success(request, f'✅ Cuenta creada para {user.get_full_name()}.')
            return redirect('profesor_vincular', user_id=user.id)
    return render(request, 'psicoasis/profesores/profesor_nuevo.html', {'form': form})


@_requiere_psicologo
def profesor_vincular(request, user_id):
    """Vincular la cuenta de profesor a un registro Docente existente."""
    prof_user = get_object_or_404(User, pk=user_id)
    perfil_prof = get_object_or_404(PerfilProfesor, usuario=prof_user)

    # Docentes sin usuario vinculado
    docentes_disponibles = Docente.objects.filter(
        usuario_vinculado__isnull=True, activo=True
    ).order_by('apellido')

    if request.method == 'POST':
        docente_id = request.POST.get('docente_id')
        if docente_id:
            docente = get_object_or_404(Docente, pk=docente_id)
            perfil_prof.docente = docente
            perfil_prof.save()
            messages.success(request, f'✅ Vinculado a {docente.get_full_name()}.')
        return redirect('profesores_list')

    ctx = {
        'prof_user': prof_user,
        'docentes_disponibles': docentes_disponibles,
    }
    return render(request, 'psicoasis/profesores/profesor_vincular.html', ctx)


@_requiere_psicologo
def alertas_docentes_psicologo(request):
    """Bandeja de alertas enviadas por todos los profesores."""
    estado_filter = request.GET.get('estado', '')
    urgencia_filter = request.GET.get('urgencia', '')

    alertas = AlertaEstudianteProfesor.objects.all().order_by('-fecha_creacion')
    if estado_filter:
        alertas = alertas.filter(estado=estado_filter)
    if urgencia_filter:
        alertas = alertas.filter(urgencia=urgencia_filter)

    ctx = {
        'alertas': alertas,
        'estado_filter': estado_filter,
        'urgencia_filter': urgencia_filter,
        'estados': AlertaEstudianteProfesor.ESTADOS,
        'urgencias': AlertaEstudianteProfesor.NIVEL_URGENCIA,
    }
    return render(request, 'psicoasis/profesores/alertas_psicologo.html', ctx)


@_requiere_psicologo
def responder_alerta(request, pk):
    """La psicóloga responde / gestiona una alerta docente."""
    alerta = get_object_or_404(AlertaEstudianteProfesor, pk=pk)
    form = RespuestaAlertaForm(instance=alerta)

    if request.method == 'POST':
        form = RespuestaAlertaForm(request.POST, instance=alerta)
        if form.is_valid():
            a = form.save(commit=False)
            from django.utils import timezone
            a.fecha_respuesta = timezone.now()
            a.save()
            # Notificar al profesor
            from .services_profesores import crear_notificacion_profesor
            crear_notificacion_profesor(
                alerta.profesor,
                'alerta_respondida',
                '✅ Tu alerta fue atendida',
                f'La psicóloga respondió tu alerta sobre {alerta.estudiante.get_full_name()}.',
                prioridad='media',
            )
            messages.success(request, 'Respuesta enviada al docente.')
            return redirect('alertas_docentes_psicologo')

    ctx = {'alerta': alerta, 'form': form}
    return render(request, 'psicoasis/profesores/responder_alerta.html', ctx)


@_requiere_psicologo
def citas_profesores_psicologo(request):
    """Gestión de citas de profesores desde el panel psicóloga."""
    citas = CitaProfesor.objects.all().order_by('-fecha_creacion')
    return render(request, 'psicoasis/profesores/citas_prof_psicologo.html',
                  {'citas': citas})


@_requiere_psicologo
def gestionar_cita_profesor(request, pk):
    """Confirmar / reagendar / cancelar una cita de profesor."""
    cita = get_object_or_404(CitaProfesor, pk=pk)
    form = CitaProfesorGestionForm(instance=cita)

    if request.method == 'POST':
        form = CitaProfesorGestionForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cita actualizada.')
            return redirect('citas_profesores_psicologo')

    ctx = {'cita': cita, 'form': form}
    return render(request, 'psicoasis/profesores/gestionar_cita_prof.html', ctx)


@_requiere_psicologo
def bandeja_mensajes_prof_psicologo(request):
    """Bandeja de conversaciones con profesores."""
    # Profesores que tienen mensajes
    profesores_con_msg = User.objects.filter(
        perfil__rol='profesor',
        mensajes_prof_enviados__isnull=False
    ).distinct()

    psicologo = request.user
    conversaciones = []
    for prof in User.objects.filter(perfil__rol='profesor'):
        ultimo = MensajeProfesor.objects.filter(
            Q(remitente=prof, destinatario=psicologo) |
            Q(remitente=psicologo, destinatario=prof)
        ).order_by('-fecha').first()
        no_leidos = MensajeProfesor.objects.filter(
            remitente=prof, destinatario=psicologo, leido=False
        ).count()
        if ultimo:
            conversaciones.append({
                'profesor': prof,
                'ultimo': ultimo,
                'no_leidos': no_leidos,
            })

    conversaciones.sort(key=lambda x: x['ultimo'].fecha, reverse=True)

    # Conversación activa
    prof_id = request.GET.get('prof')
    conv_activa = None
    form = MensajeProfesorForm()
    if prof_id:
        prof_activo = get_object_or_404(User, pk=prof_id, perfil__rol='profesor')
        MensajeProfesor.objects.filter(
            remitente=prof_activo, destinatario=psicologo, leido=False
        ).update(leido=True)
        conv_activa = MensajeProfesor.objects.filter(
            Q(remitente=prof_activo, destinatario=psicologo) |
            Q(remitente=psicologo, destinatario=prof_activo)
        ).order_by('fecha')

        if request.method == 'POST':
            form = MensajeProfesorForm(request.POST, request.FILES)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.remitente = psicologo
                msg.destinatario = prof_activo
                msg.save()
                # Notificar al profesor
                from .services_profesores import crear_notificacion_profesor
                crear_notificacion_profesor(
                    prof_activo, 'mensaje_nuevo',
                    '💬 Nuevo mensaje de la psicóloga',
                    'Tienes un mensaje nuevo en tu panel.', prioridad='media',
                )
                return redirect(f"{request.path}?prof={prof_id}")

    ctx = {
        'conversaciones': conversaciones,
        'conv_activa': conv_activa,
        'form': form,
        'prof_id': prof_id,
    }
    return render(request, 'psicoasis/profesores/bandeja_prof_psicologo.html', ctx)


@_requiere_psicologo
def crear_recurso_profesor(request):
    """La psicóloga crea un recurso para profesores."""
    form = RecursoProfesorForm()
    if request.method == 'POST':
        form = RecursoProfesorForm(request.POST, request.FILES)
        if form.is_valid():
            recurso = form.save(commit=False)
            recurso.autor = request.user
            recurso.save()
            form.save_m2m()
            # Notificar a los profesores destinatarios
            from .services_profesores import crear_notificacion_profesor
            if recurso.para_todos:
                destinatarios = User.objects.filter(perfil__rol='profesor')
            else:
                destinatarios = recurso.profesores_especificos.all()
            for prof in destinatarios:
                crear_notificacion_profesor(
                    prof, 'recurso_compartido',
                    f'📎 Nuevo recurso: {recurso.titulo}',
                    recurso.descripcion[:200],
                )
            messages.success(request, f'✅ Recurso "{recurso.titulo}" publicado.')
            return redirect('profesores_list')
    return render(request, 'psicoasis/profesores/crear_recurso.html', {'form': form})


@_requiere_psicologo
def bienestar_docentes_psicologo(request):
    """Vista de bienestar general de todos los docentes."""
    from datetime import timedelta
    from django.utils import timezone
    hoy = timezone.now().date()
    semanas_atras = int(request.GET.get('semanas', 8))

    desde = hoy - timedelta(weeks=semanas_atras)
    autoevaluaciones = AutoevaluacionProfesor.objects.filter(
        semana__gte=desde
    ).select_related('profesor').order_by('-semana')

    # Agrupar por profesor
    profesores_bienestar = {}
    for ae in autoevaluaciones:
        pid = ae.profesor.id
        if pid not in profesores_bienestar:
            profesores_bienestar[pid] = {
                'profesor': ae.profesor,
                'ultimo': ae,
                'registros': [],
            }
        profesores_bienestar[pid]['registros'].append(ae)

    # Alertas críticas sin resolver
    alertas_criticas = AutoevaluacionProfesor.objects.filter(
        Q(bienestar__in=('agotado', 'en_crisis')) | Q(solicita_atencion=True),
        semana__gte=hoy - timedelta(weeks=2)
    ).select_related('profesor')

    ctx = {
        'profesores_bienestar': profesores_bienestar.values(),
        'alertas_criticas': alertas_criticas,
        'semanas_atras': semanas_atras,
    }
    return render(request, 'psicoasis/profesores/bienestar_docentes.html', ctx)
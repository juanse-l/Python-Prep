#!/bin/bash
# ============================================================
#  🌿 PsicoAsis — Script de Inicio
#  Psicología Escolar
# ============================================================

echo ""
echo "🌿 Configurando PsicoAsis..."
echo ""

cd "$(dirname "$0")"

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "Variables de entorno cargadas desde .env"
else
    echo "Advertencia: no se encontro .env — copia .env.example a .env y completa los valores"
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt -q

# Migraciones
echo "🗄️  Configurando base de datos..."
python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

# Crear superusuario Laura si no existe
echo "👤 Configurando usuario Laura..."
python manage.py shell << 'PYTHON'
from django.contrib.auth.models import User
from psicoasis.models import Perfil

# Crear usuario Laura
if not User.objects.filter(username='laura').exists():
    user = User.objects.create_superuser(
        username='laura',
        email='laura@psicoasis.edu.co',
        password='psicoasis2025',
        first_name='Laura',
        last_name='Psicóloga'
    )
    Perfil.objects.get_or_create(usuario=user)
    print("✅ Usuario 'laura' creado")
    print("   Email: laura@psicoasis.edu.co")
    print("   Contraseña: psicoasis2025")
else:
    print("ℹ️  Usuario 'laura' ya existe")

# Crear datos de muestra
from psicoasis.models import Estudiante, Caso, Reunion, RecursoWellness
from datetime import date, timedelta

if Estudiante.objects.count() == 0:
    estudiantes_data = [
        ('Valentina', 'García', '8A', 14, 'María García', '310 123 4567'),
        ('Sebastián', 'Martínez', '9B', 15, 'Carlos Martínez', '311 234 5678'),
        ('Isabella', 'López', '7A', 13, 'Ana López', '312 345 6789'),
        ('Samuel', 'Rodríguez', '10A', 16, 'Pedro Rodríguez', '313 456 7890'),
        ('Sofía', 'Hernández', '6B', 12, 'Laura Hernández', '314 567 8901'),
        ('Mateo', 'González', '11A', 17, 'Jorge González', '315 678 9012'),
    ]
    
    for nombre, apellido, grado, edad, acudiente, tel in estudiantes_data:
        Estudiante.objects.create(
            nombre=nombre, apellido=apellido, grado=grado, edad=edad,
            nombre_acudiente=acudiente, telefono_acudiente=tel
        )
    print(f"✅ {len(estudiantes_data)} estudiantes de muestra creados")

    # Casos de muestra
    user = User.objects.get(username='laura')
    e1 = Estudiante.objects.first()
    e2 = Estudiante.objects.all()[1]
    
    Caso.objects.create(estudiante=e1, psicologo=user, motivo='ansiedad_academica', descripcion='Estudiante presenta ansiedad antes de los exámenes. Se trabajará con técnicas de relajación y manejo del estrés.', tipo_atencion='prioritario')
    Caso.objects.create(estudiante=e2, psicologo=user, motivo='baja_autoestima', descripcion='El estudiante muestra baja autoestima y dificultades para relacionarse con sus pares.', tipo_atencion='regular')
    
    # Reuniones de muestra
    hoy = date.today()
    Reunion.objects.create(estudiante=e1, psicologo=user, fecha=hoy, hora='09:00', motivo='Primera sesión de evaluación', estado='confirmada')
    Reunion.objects.create(estudiante=e2, psicologo=user, fecha=hoy+timedelta(days=2), hora='10:30', motivo='Seguimiento autoestima', estado='pendiente')
    Reunion.objects.create(estudiante=Estudiante.objects.all()[2], psicologo=user, fecha=hoy+timedelta(days=4), hora='14:00', motivo='Orientación familiar', estado='confirmada')
    print("✅ Datos de muestra creados")

# Recursos de bienestar
if RecursoWellness.objects.count() == 0:
    recursos = [
        ('Respiración 4-7-8', 'Técnica de respiración para reducir la ansiedad en momentos de estrés escolar.', 'herramienta_autocuidado', 'texto'),
        ('Diario de emociones', 'Guía para que los estudiantes registren y comprendan sus emociones diariamente.', 'herramienta_autocuidado', 'texto'),
        ('¿Qué es la inteligencia emocional?', 'Recurso educativo sobre las cinco dimensiones de la inteligencia emocional.', 'biblioteca_emocional', 'texto'),
        ('Manejo de la ansiedad escolar', 'Guía completa para docentes y estudiantes sobre cómo manejar la ansiedad académica.', 'biblioteca_emocional', 'texto'),
        ('Mini plan de autocuidado semanal', 'Plan de 7 días con actividades sencillas de autocuidado para adolescentes.', 'mini_planes', 'texto'),
    ]
    for titulo, desc, cat, tipo in recursos:
        RecursoWellness.objects.create(titulo=titulo, descripcion=desc, categoria=cat, tipo_media=tipo)
    print("✅ Recursos de bienestar creados")

print("")
print("🎉 ¡Todo listo!")
PYTHON

echo ""
echo "============================================================"
echo "  🌿 PsicoAsis está listo"
echo "============================================================"
echo ""
echo "  🌐 Sitio público:    http://127.0.0.1:8000/"
echo "  🔒 Dashboard Laura:  http://127.0.0.1:8000/dashboard/"
echo ""
echo "  👤 Credenciales de Laura:"
echo "     Email:      laura@psicoasis.edu.co"
echo "     Usuario:    laura"
echo "     Contraseña: psicoasis2025"
echo ""
echo "  En el sitio público, busca el botón 'Laura, ingresa aquí ✦'"
echo "  en la esquina superior derecha de la pantalla."
echo ""
echo "  Iniciando servidor..."
echo ""

python manage.py runserver

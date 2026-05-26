# PsicoAsis 🌿 — Sistema de Psicología Escolar

Plataforma integral de gestión psicológica escolar desarrollada con Django. Permite gestionar estudiantes, casos, citas, informes, bienestar emocional y comunicación con familias y docentes.

## 📋 Características

- **Panel Psicóloga**: Gestión completa de estudiantes, casos, reuniones e informes
- **Panel Estudiante**: Check-in emocional, citas, mensajes y chat con IA
- **Panel Padres/Tutores**: Seguimiento emocional del hijo, citas y mensajes
- **Panel Docentes**: Alertas, bienestar y comunicación con la psicóloga
- **PsicoIA**: Asistente de inteligencia artificial (Claude) integrado
- **Foros emocionales**: Espacios de bienestar y comunidad
- **Calendario**: Gestión visual de citas y reuniones

## 🗂️ Estructura del proyecto

```
psicoasis/
├── config/           # Configuración Django (settings, urls, wsgi)
├── psicoasis/        # Aplicación principal
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   │   └── psicoasis/
│   │       ├── padres/     # Templates del panel de padres
│   │       └── profesores/ # Templates del panel de docentes
│   ├── templatetags/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── services_padres.py
│   └── services_profesores.py
├── manage.py
├── requirements.txt
├── .env.example
└── iniciar.sh
```

## 🚀 Instalación y ejecución

### 1. Clonar y configurar entorno

```bash
git clone <repo-url>
cd psicoasis
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores reales
```

### 3. Base de datos y servidor

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O usa el script de inicio:

```bash
chmod +x iniciar.sh
./iniciar.sh
```

### 4. Crear superusuario psicóloga

```bash
python manage.py createsuperuser
```
Luego asigna el rol `psicologo` desde el panel de admin o directamente en la base de datos.

## ⚙️ Variables de entorno necesarias

| Variable | Descripción |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Clave secreta Django (requerida en producción) |
| `ANTHROPIC_API_KEY` | API key de Claude (para PsicoIA) |
| `PSICOASIS_EMAIL` | Correo Gmail que envía notificaciones |
| `PSICOASIS_EMAIL_PASSWORD` | Contraseña de aplicación Gmail |
| `PSICOLOGA_EMAIL` | Correo que recibe las solicitudes de cita |
| `GOOGLE_CALENDAR_ID` | ID calendario Google (opcional) |

## 🔑 Roles de usuario

| Rol | Acceso |
|-----|--------|
| `psicologo` | Panel completo de gestión |
| `estudiante` | Panel personal del estudiante |
| `padre` / `tutor` | Panel de padres/tutores |
| `profesor` | Panel de docentes |

## 📦 Dependencias principales

- Django >= 4.2
- Pillow (imágenes)
- python-dotenv (variables de entorno)
- Chart.js (gráficas, CDN)
- Font Awesome 6 (iconos, CDN)

---

Desarrollado con 💚 para el bienestar emocional escolar.

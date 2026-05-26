from django.apps import AppConfig


class PsicoasisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'psicoasis'

    def ready(self):
        import psicoasis.signals_padres    # noqa
        import psicoasis.signals_profesores  # noqa

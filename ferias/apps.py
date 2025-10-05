from django.apps import AppConfig


class FeriasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ferias"

    def ready(self):
        import ferias.signals
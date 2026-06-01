from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
    verbose_name = "Blog"

    def ready(self):
        # ready() jest wywoływane gdy Django kończy ładowanie
        # Importujemy sygnały tutaj żeby Django je zarejestrował
        # Gdybyś tego nie zrobił, sygnały by nie działały
        import blog.signals  # noqa: F401
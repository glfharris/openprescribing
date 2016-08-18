from django.apps import AppConfig

class FrontendConfig(AppConfig):
    name = 'frontend'

    def ready(self):
        import admin
        import frontend.signals.handlers

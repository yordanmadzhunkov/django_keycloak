from django.apps import AppConfig

class VeiPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vei_platform'
    
    def ready(self):
        import vei_platform.signals

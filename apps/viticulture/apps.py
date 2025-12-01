from django.apps import AppConfig


class ViticultureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.viticulture'
    verbose_name = 'Cœur Viticole'
    
    def ready(self):
        """Initialisation de l'app viticulture"""
        # Import des signaux pour validation métier
        try:
            from . import signals
        except ImportError:
            pass

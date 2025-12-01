from django.apps import AppConfig


class MetadataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.metadata'
    verbose_name = 'Métadonnées & Gouvernance'
    
    def ready(self):
        """Initialisation de l'app metadata"""
        # Import des signaux pour l'indexation automatique
        try:
            from . import signals
        except ImportError:
            pass

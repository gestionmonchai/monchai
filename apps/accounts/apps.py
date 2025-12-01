from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Comptes et Authentification'
    
    def ready(self):
        """Importer les signaux lors du démarrage de l'app"""
        import apps.accounts.signals

"""
Test de non-régression pour les URLs du module ventes
"""
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()


class Command(BaseCommand):
    help = 'Test toutes les URLs du module ventes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n*** TEST DE NON-REGRESSION - URLS VENTES ***\n'))
        
        # Liste de toutes les URLs à tester
        urls_to_test = [
            # URLs standards
            ('ventes:dashboard', None, 'Dashboard Ventes'),
            ('ventes:devis_list', None, 'Liste Devis'),
            ('ventes:devis_new', None, 'Nouveau Devis'),
            ('ventes:cmd_list', None, 'Liste Commandes'),
            ('ventes:cmd_new', None, 'Nouvelle Commande'),
            ('ventes:factures_list', None, 'Liste Factures'),
            ('ventes:facture_new', None, 'Nouvelle Facture'),
            ('ventes:primeur_list', None, 'Liste Ventes Primeur'),
            ('ventes:primeur_new', None, 'Nouvelle Vente Primeur'),
            ('ventes:vrac_list', None, 'Liste Ventes Vrac'),
            ('ventes:vrac_new', None, 'Nouvelle Vente Vrac'),
            ('ventes:clients_list', None, 'Liste Clients'),
            ('ventes:client_new', None, 'Nouveau Client'),
        ]
        
        self.stdout.write(self.style.WARNING('--- Test de resolution des URLs ---\n'))
        
        errors = []
        successes = []
        
        for url_name, kwargs, description in urls_to_test:
            try:
                if kwargs:
                    url = reverse(url_name, kwargs=kwargs)
                else:
                    url = reverse(url_name)
                successes.append(f'[OK] {description}: {url}')
            except Exception as e:
                errors.append(f'[ERREUR] {description} ({url_name}): {str(e)}')
        
        # Afficher les résultats
        for success in successes:
            self.stdout.write(self.style.SUCCESS(f'  {success}'))
        
        if errors:
            self.stdout.write(self.style.ERROR('\n*** ERREURS DETECTEES ***\n'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  {error}'))
            return
        
        # Test d'accès HTTP (si authentifié)
        self.stdout.write(self.style.WARNING('\n--- Test d\'acces HTTP ---\n'))
        
        # Vérifier qu'un utilisateur existe
        user = User.objects.filter(is_active=True).first()
        if not user:
            self.stdout.write(self.style.WARNING('  [WARN] Aucun utilisateur trouve, tests HTTP ignores'))
            self.stdout.write(self.style.SUCCESS('\n*** Tests de resolution d\'URLs: REUSSIS ***\n'))
            return
        
        # Créer un client de test
        client = Client()
        client.force_login(user)
        
        http_errors = []
        http_successes = []
        
        for url_name, kwargs, description in urls_to_test:
            try:
                if kwargs:
                    url = reverse(url_name, kwargs=kwargs)
                else:
                    url = reverse(url_name)
                
                response = client.get(url, follow=True)
                
                if response.status_code == 200:
                    http_successes.append(f'[OK] {description}: HTTP 200')
                elif response.status_code == 302:
                    http_successes.append(f'[OK] {description}: HTTP 302 (redirect)')
                else:
                    http_errors.append(f'[WARN] {description}: HTTP {response.status_code}')
                    
            except Exception as e:
                http_errors.append(f'[ERREUR] {description}: {str(e)}')
        
        # Afficher les résultats HTTP
        for success in http_successes:
            self.stdout.write(self.style.SUCCESS(f'  {success}'))
        
        if http_errors:
            self.stdout.write(self.style.WARNING('\n*** AVERTISSEMENTS HTTP ***\n'))
            for error in http_errors:
                self.stdout.write(self.style.WARNING(f'  {error}'))
        
        # Statistiques finales
        self.stdout.write(self.style.SUCCESS(f'\n*** RESULTATS ***'))
        self.stdout.write(f'  URLs résolues: {len(successes)}/{len(urls_to_test)}')
        self.stdout.write(f'  Accès HTTP OK: {len(http_successes)}/{len(urls_to_test)}')
        
        if not errors and not http_errors:
            self.stdout.write(self.style.SUCCESS('\n*** TOUS LES TESTS REUSSIS ! ***\n'))
        elif not errors:
            self.stdout.write(self.style.WARNING('\n*** URLs OK mais certains acces HTTP echouent (verifier permissions) ***\n'))
        else:
            self.stdout.write(self.style.ERROR('\n*** ECHEC DES TESTS ***\n'))

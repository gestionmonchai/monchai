"""
Commande pour créer des données de démonstration clients - Roadmap 37
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Organization
from apps.clients.models import Customer, CustomerTag, CustomerTagLink


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour les clients'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-name',
            type=str,
            default='Domaine de Démonstration',
            help='Nom de l\'organisation (défaut: Domaine de Démonstration)'
        )

    def handle(self, *args, **options):
        org_name = options['org_name']
        
        try:
            with transaction.atomic():
                # Récupération ou création de l'organisation
                organization, created = Organization.objects.get_or_create(
                    name=org_name,
                    defaults={
                        'address': '123 Route des Vignes',
                        'postal_code': '21200',
                        'city': 'Beaune',
                        'country': 'France'
                    }
                )
                
                if created:
                    self.stdout.write(f"✓ Organisation '{org_name}' créée")
                else:
                    self.stdout.write(f"✓ Organisation '{org_name}' trouvée")
                
                # Création des tags clients
                tags_data = [
                    {'name': 'VIP', 'color': '#dc3545'},
                    {'name': 'Fidèle', 'color': '#28a745'},
                    {'name': 'Nouveau', 'color': '#007bff'},
                    {'name': 'Export', 'color': '#6f42c1'},
                    {'name': 'Local', 'color': '#fd7e14'},
                ]
                
                created_tags = []
                for tag_data in tags_data:
                    tag, created = CustomerTag.objects.get_or_create(
                        organization=organization,
                        name=tag_data['name'],
                        defaults={'color': tag_data['color']}
                    )
                    created_tags.append(tag)
                    if created:
                        self.stdout.write(f"  ✓ Tag '{tag.name}' créé")
                
                # Création des clients de démonstration
                clients_data = [
                    {
                        'name': 'Cave du Rhône SARL',
                        'segment': 'wine_shop',
                        'email': 'contact@cave-rhone.fr',
                        'phone': '+33474123456',
                        'vat_number': 'FR12345678901',
                        'country_code': 'FR',
                        'is_active': True,
                        'tags': ['VIP', 'Local']
                    },
                    {
                        'name': 'Restaurant Le Gourmet',
                        'segment': 'business',
                        'email': 'commandes@legourmet.fr',
                        'phone': '+33145678901',
                        'vat_number': 'FR98765432109',
                        'country_code': 'FR',
                        'is_active': True,
                        'tags': ['Fidèle']
                    },
                    {
                        'name': 'Jean Dupont',
                        'segment': 'individual',
                        'email': 'jean.dupont@email.fr',
                        'phone': '+33612345678',
                        'country_code': 'FR',
                        'is_active': True,
                        'tags': ['Nouveau']
                    },
                    {
                        'name': 'Wine Import USA LLC',
                        'segment': 'export',
                        'email': 'orders@wineimportusa.com',
                        'phone': '+12125551234',
                        'vat_number': 'US123456789',
                        'country_code': 'US',
                        'is_active': True,
                        'tags': ['Export', 'VIP']
                    },
                    {
                        'name': 'Marie Martin',
                        'segment': 'individual',
                        'email': 'marie.martin@gmail.com',
                        'phone': '+33687654321',
                        'country_code': 'FR',
                        'is_active': True,
                        'tags': ['Fidèle', 'Local']
                    },
                    {
                        'name': 'Weinhandel Schmidt GmbH',
                        'segment': 'business',
                        'email': 'info@weinhandel-schmidt.de',
                        'phone': '+4930123456789',
                        'vat_number': 'DE123456789',
                        'country_code': 'DE',
                        'is_active': True,
                        'tags': ['Export']
                    },
                    {
                        'name': 'Pierre Moreau',
                        'segment': 'individual',
                        'email': 'p.moreau@hotmail.fr',
                        'country_code': 'FR',
                        'is_active': False,  # Client inactif pour test
                        'tags': []
                    },
                    {
                        'name': 'Swiss Wine Distribution SA',
                        'segment': 'business',
                        'email': 'contact@swisswine.ch',
                        'phone': '+41223456789',
                        'vat_number': 'CHE123456789TVA',
                        'country_code': 'CH',
                        'is_active': True,
                        'tags': ['Export', 'VIP']
                    }
                ]
                
                created_customers = []
                for client_data in clients_data:
                    # Extraction des tags
                    tag_names = client_data.pop('tags', [])
                    
                    # Création du client
                    customer, created = Customer.objects.get_or_create(
                        organization=organization,
                        name=client_data['name'],
                        defaults=client_data
                    )
                    
                    if created:
                        created_customers.append(customer)
                        self.stdout.write(f"  ✓ Client '{customer.name}' créé")
                        
                        # Assignation des tags
                        for tag_name in tag_names:
                            try:
                                tag = CustomerTag.objects.get(organization=organization, name=tag_name)
                                CustomerTagLink.objects.get_or_create(
                                    organization=organization,
                                    customer=customer,
                                    tag=tag
                                )
                            except CustomerTag.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f"    ⚠ Tag '{tag_name}' non trouvé pour {customer.name}")
                                )
                    else:
                        self.stdout.write(f"  - Client '{customer.name}' existe déjà")
                
                # Statistiques finales
                total_customers = Customer.objects.filter(organization=organization).count()
                active_customers = Customer.objects.filter(organization=organization, is_active=True).count()
                total_tags = CustomerTag.objects.filter(organization=organization).count()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n🎉 Données de démonstration créées avec succès !\n"
                        f"   Organisation: {organization.name}\n"
                        f"   Clients total: {total_customers} ({active_customers} actifs)\n"
                        f"   Tags: {total_tags}\n"
                        f"   Nouveaux clients: {len(created_customers)}\n"
                    )
                )
                
                # Instructions d'utilisation
                self.stdout.write(
                    self.style.WARNING(
                        f"\n📋 Pour tester l'interface :\n"
                        f"   1. Démarrez le serveur : python manage.py runserver\n"
                        f"   2. Accédez à : http://localhost:8000/clients/\n"
                        f"   3. Testez la recherche, les filtres et la création\n"
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de la création des données : {str(e)}")
            )
            raise

#!/usr/bin/env python
"""
Script pour créer des données de test pour les clients - Roadmap 36
"""

import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, User
from apps.clients.models import Customer, CustomerTag, CustomerTagLink

def create_test_clients():
    """Crée des clients de test pour validation"""
    
    # Récupérer une organisation de test
    org = Organization.objects.filter(name="Domaine de Démonstration").first()
    if not org:
        org = Organization.objects.first()
    
    if not org:
        print("Aucune organisation trouvee")
        return
    
    # Récupérer un utilisateur
    user = User.objects.filter(memberships__organization=org).first()
    if not user:
        print("Aucun utilisateur trouve pour l'organisation")
        return
    
    print(f"Organisation: {org.name}")
    print(f"Utilisateur: {user.email}")
    
    # Créer des tags
    tags_data = [
        {'name': 'VIP', 'color': '#dc3545', 'description': 'Clients VIP'},
        {'name': 'Fidèle', 'color': '#28a745', 'description': 'Clients fidèles'},
        {'name': 'Nouveau', 'color': '#007bff', 'description': 'Nouveaux clients'},
        {'name': 'Export', 'color': '#fd7e14', 'description': 'Clients export'},
        {'name': 'Local', 'color': '#6f42c1', 'description': 'Clients locaux'},
    ]
    
    created_tags = []
    for tag_data in tags_data:
        tag, created = CustomerTag.objects.get_or_create(
            organization=org,
            name=tag_data['name'],
            defaults={
                'color': tag_data['color'],
                'description': tag_data['description']
            }
        )
        created_tags.append(tag)
        if created:
            print(f"Tag cree: {tag.name}")
        else:
            print(f"Tag existant: {tag.name}")
    
    # Créer des clients de test
    clients_data = [
        {
            'name': 'Cave du Rhône',
            'segment': 'wine_shop',
            'email': 'contact@caverhone.fr',
            'phone': '04 90 12 34 56',
            'vat_number': 'FR12345678901',
            'country_code': 'FR',
            'tags': ['VIP', 'Fidèle']
        },
        {
            'name': 'Restaurant Le Gourmet',
            'segment': 'business',
            'email': 'chef@legourmet.fr',
            'phone': '01 42 56 78 90',
            'vat_number': 'FR98765432109',
            'country_code': 'FR',
            'tags': ['Fidèle', 'Local']
        },
        {
            'name': 'Pierre Martin',
            'segment': 'individual',
            'email': 'pierre.martin@email.fr',
            'phone': '06 12 34 56 78',
            'country_code': 'FR',
            'tags': ['Nouveau']
        },
        {
            'name': 'Wine Import USA',
            'segment': 'export',
            'email': 'orders@wineimportusa.com',
            'phone': '+1 555 123 4567',
            'vat_number': 'US123456789',
            'country_code': 'US',
            'tags': ['Export', 'VIP']
        },
        {
            'name': 'Domaine Voisin',
            'segment': 'business',
            'email': 'contact@domainevoisin.fr',
            'phone': '05 56 78 90 12',
            'vat_number': 'FR55667788990',
            'country_code': 'FR',
            'tags': ['Local']
        },
        {
            'name': 'Marie Dubois',
            'segment': 'individual',
            'email': 'marie.dubois@gmail.com',
            'phone': '06 98 76 54 32',
            'country_code': 'FR',
            'tags': ['Fidèle']
        },
        {
            'name': 'Swiss Wine Shop',
            'segment': 'wine_shop',
            'email': 'info@swisswineshop.ch',
            'phone': '+41 22 123 4567',
            'vat_number': 'CHE123456789',
            'country_code': 'CH',
            'tags': ['Export']
        },
        {
            'name': 'Jean-Claude Mercier',
            'segment': 'individual',
            'email': 'jc.mercier@hotmail.fr',
            'phone': '07 11 22 33 44',
            'country_code': 'FR',
            'tags': ['VIP', 'Fidèle']
        }
    ]
    
    created_customers = []
    for client_data in clients_data:
        # Créer le client
        customer, created = Customer.objects.get_or_create(
            organization=org,
            name=client_data['name'],
            defaults={
                'segment': client_data['segment'],
                'email': client_data.get('email'),
                'phone': client_data.get('phone'),
                'vat_number': client_data.get('vat_number'),
                'country_code': client_data.get('country_code'),
                'is_active': True
            }
        )
        
        if created:
            print(f"Client cree: {customer.name} ({customer.get_segment_display()})")
            
            # Ajouter les tags
            for tag_name in client_data.get('tags', []):
                tag = next((t for t in created_tags if t.name == tag_name), None)
                if tag:
                    CustomerTagLink.objects.get_or_create(
                        organization=org,
                        customer=customer,
                        tag=tag
                    )
        else:
            print(f"Client existant: {customer.name}")
        
        created_customers.append(customer)
    
    print(f"\nTotal clients: {len(created_customers)}")
    print(f"Total tags: {len(created_tags)}")
    
    # Statistiques par segment
    from collections import Counter
    segments = Counter(c.segment for c in created_customers)
    print(f"\nRepartition par segment:")
    for segment, count in segments.items():
        segment_display = dict(Customer.SEGMENT_CHOICES).get(segment, segment)
        print(f"  - {segment_display}: {count}")

def main():
    print("Configuration des clients de test - Roadmap 36")
    print("=" * 50)
    
    try:
        create_test_clients()
        
        print("\nConfiguration terminee avec succes!")
        print("\nProchaines etapes:")
        print("  1. Acceder a /clients/ pour voir l'interface")
        print("  2. Tester la recherche et les filtres")
        print("  3. Tester l'API /clients/api/")
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

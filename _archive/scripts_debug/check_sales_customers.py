"""
Script pour vérifier et créer des clients de test pour le module Sales
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.sales.models import Customer as SalesCustomer
from apps.accounts.models import Organization

def check_and_create_customers():
    """Vérifie et crée des clients de test si nécessaire"""
    
    # Récupérer la première organisation
    org = Organization.objects.first()
    if not org:
        print("[ERREUR] Aucune organisation trouvee. Creez d'abord une organisation.")
        return
    
    print(f"[OK] Organisation trouvee: {org.name}")
    
    # Vérifier les clients existants
    existing_customers = SalesCustomer.objects.filter(organization=org)
    count = existing_customers.count()
    
    print(f"\n[INFO] Clients existants: {count}")
    
    if count > 0:
        print("\n[LISTE] Clients:")
        for customer in existing_customers[:10]:
            print(f"  - {customer.legal_name} ({customer.get_type_display()})")
    else:
        print("\n[ATTENTION] Aucun client trouve. Creation de clients de test...")
        
        # Créer des clients de test
        test_customers = [
            {
                'legal_name': 'Domaine du Soleil',
                'type': 'pro',
                'billing_address': '123 Route des Vignes',
                'billing_postal_code': '33000',
                'billing_city': 'Bordeaux',
                'billing_country': 'FR',
                'payment_terms': '30j',
                'currency': 'EUR',
            },
            {
                'legal_name': 'Cave Martin',
                'type': 'part',
                'billing_address': '45 Rue de la Cave',
                'billing_postal_code': '69000',
                'billing_city': 'Lyon',
                'billing_country': 'FR',
                'payment_terms': '30j',
                'currency': 'EUR',
            },
            {
                'legal_name': 'Restaurant Le Gourmet',
                'type': 'pro',
                'billing_address': '78 Avenue des Champs',
                'billing_postal_code': '75008',
                'billing_city': 'Paris',
                'billing_country': 'FR',
                'payment_terms': '45j',
                'currency': 'EUR',
            },
            {
                'legal_name': 'Dupont Jean',
                'type': 'part',
                'billing_address': '12 Rue de la Paix',
                'billing_postal_code': '21000',
                'billing_city': 'Dijon',
                'billing_country': 'FR',
                'payment_terms': '30j',
                'currency': 'EUR',
            },
            {
                'legal_name': 'Société Vinicole du Sud',
                'type': 'pro',
                'billing_address': '56 Boulevard du Vin',
                'billing_postal_code': '84000',
                'billing_city': 'Avignon',
                'billing_country': 'FR',
                'payment_terms': '60j',
                'currency': 'EUR',
            },
        ]
        
        created = 0
        for customer_data in test_customers:
            customer = SalesCustomer(
                organization=org,
                is_active=True,
                shipping_address='',
                shipping_postal_code='',
                shipping_city='',
                shipping_country='',
                **customer_data
            )
            try:
                customer.full_clean()
                customer.save()
                print(f"  [OK] Cree: {customer.legal_name}")
                created += 1
            except Exception as e:
                print(f"  [ERREUR] Erreur pour {customer_data['legal_name']}: {e}")
        
        print(f"\n[OK] {created} clients crees avec succes!")
    
    print("\n" + "="*60)
    print("Test de l'API de suggestions:")
    print("="*60)
    
    # Test de recherche
    test_queries = ['Domaine', 'Cave', 'Restaurant', 'Dupont']
    for query in test_queries:
        results = SalesCustomer.objects.filter(
            organization=org,
            legal_name__icontains=query
        )
        print(f"\n[RECHERCHE] '{query}': {results.count()} resultat(s)")
        for r in results:
            print(f"  - {r.legal_name}")

if __name__ == '__main__':
    check_and_create_customers()

"""
Script de test pour vérifier que toutes les URLs du dashboard sont valides
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.urls import reverse, NoReverseMatch

# URLs utilisées dans dashboard_widgets.py
urls_to_test = [
    'clients:customers_list',
    'ventes:cmd_list',
    'ventes:factures_list',
    'catalogue:products_cuvees',
    'stock:dashboard',
    'production:vendanges_list',
    'onboarding:checklist',
]

print("Test des URLs du dashboard...\n")

errors = []
for url_name in urls_to_test:
    try:
        resolved_url = reverse(url_name)
        print(f"[OK] {url_name:30} -> {resolved_url}")
    except NoReverseMatch as e:
        print(f"[ERROR] {url_name:30} -> {e}")
        errors.append((url_name, str(e)))

print(f"\n{'='*60}")
if errors:
    print(f"ERREURS: {len(errors)} URL(s) invalide(s)")
    for url_name, error in errors:
        print(f"   - {url_name}: {error}")
else:
    print("SUCCESS: Toutes les URLs sont valides !")
print(f"{'='*60}")

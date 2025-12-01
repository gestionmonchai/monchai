#!/usr/bin/env python
"""
Test de qualité visuelle et d'encodage
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import re

User = get_user_model()

def test_visual_quality():
    """Tester la qualité visuelle et l'encodage"""
    print("=== TEST QUALITE VISUELLE ===")
    
    client = Client()
    
    # Login avec utilisateur existant
    user = User.objects.first()
    if user:
        client.force_login(user)
        print(f"Login avec {user.email}")
    else:
        print("Aucun utilisateur disponible")
        return False
    
    # Pages à tester visuellement
    pages_to_test = [
        {
            'url': '/catalogue/produits/',
            'name': 'Dashboard produits',
            'expected_elements': ['Cuvées', 'Lots', 'SKU']
        },
        {
            'url': '/catalogue/produits/cuvees/',
            'name': 'Liste cuvées',
            'expected_elements': ['Nom', 'Appellation', 'Millésime']
        },
        {
            'url': '/catalogue/produits/lots/',
            'name': 'Liste lots',
            'expected_elements': ['Code', 'Cuvée', 'Volume']
        },
        {
            'url': '/catalogue/produits/skus/',
            'name': 'Liste SKUs',
            'expected_elements': ['Étiquette', 'Stock', 'Code-barres']
        }
    ]
    
    issues = []
    
    for page in pages_to_test:
        print(f"\n--- Test {page['name']} ---")
        
        try:
            response = client.get(page['url'])
            content = response.content.decode('utf-8', errors='replace')
            
            # 1. Test problèmes d'encodage
            encoding_issues = []
            if 'Ã©' in content:
                encoding_issues.append("Caractères mal encodés détectés (Ã©)")
            if 'Ã¨' in content:
                encoding_issues.append("Caractères mal encodés détectés (Ã¨)")
            if 'Ã ' in content:
                encoding_issues.append("Caractères mal encodés détectés (Ã )")
            
            if encoding_issues:
                print(f"  PROBLEME ENCODAGE: {', '.join(encoding_issues)}")
                issues.extend([f"{page['name']}: {issue}" for issue in encoding_issues])
            else:
                print("  OK Encodage correct")
            
            # 2. Test présence éléments attendus
            missing_elements = []
            for element in page['expected_elements']:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"  PROBLEME CONTENU: Éléments manquants: {missing_elements}")
                issues.append(f"{page['name']}: Éléments manquants {missing_elements}")
            else:
                print("  OK Contenu présent")
            
            # 3. Test problèmes CSS potentiels
            css_issues = []
            
            # Chercher styles inline problématiques
            if 'color: blue' in content and 'background: blue' in content:
                css_issues.append("Texte bleu sur fond bleu détecté")
            
            # Chercher classes CSS suspectes
            if 'class="text-primary bg-primary"' in content:
                css_issues.append("Classes CSS conflictuelles détectées")
            
            if css_issues:
                print(f"  PROBLEME CSS: {', '.join(css_issues)}")
                issues.extend([f"{page['name']}: {issue}" for issue in css_issues])
            else:
                print("  OK Pas de conflit CSS évident")
            
            # 4. Extraire et analyser les badges/couleurs
            badge_matches = re.findall(r'class="[^"]*badge[^"]*"[^>]*>([^<]+)', content)
            if badge_matches:
                print(f"  INFO Badges trouvés: {badge_matches[:3]}...")
            
        except Exception as e:
            error = f"Erreur test {page['name']}: {e}"
            print(f"  ERREUR {error}")
            issues.append(error)
    
    # Résultats
    if issues:
        print(f"\nRésultats: {len(issues)} problèmes visuels détectés")
        print("\nPROBLEMES détectés:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\nRésultats: Aucun problème visuel détecté")
        print("Interface visuellement correcte!")
        return True

def test_template_encoding():
    """Tester l'encodage des templates"""
    print("\n=== TEST ENCODAGE TEMPLATES ===")
    
    template_files = [
        'templates/catalogue/products_unified.html',
        'templates/catalogue/products_cuvees.html',
        'templates/catalogue/products_lots.html',
        'templates/catalogue/products_skus.html',
        'templates/catalogue/products_referentiels.html'
    ]
    
    encoding_issues = []
    
    for template_file in template_files:
        if os.path.exists(template_file):
            try:
                # Test lecture UTF-8
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chercher caractères mal encodés
                if 'Ã©' in content or 'Ã¨' in content or 'Ã ' in content:
                    encoding_issues.append(f"{template_file}: Caractères mal encodés")
                    print(f"  PROBLEME {template_file}: Encodage incorrect")
                else:
                    print(f"  OK {template_file}: Encodage correct")
                    
            except UnicodeDecodeError:
                encoding_issues.append(f"{template_file}: Erreur décodage UTF-8")
                print(f"  ERREUR {template_file}: Impossible de décoder en UTF-8")
        else:
            print(f"  INFO {template_file}: Fichier non trouvé")
    
    return len(encoding_issues) == 0

if __name__ == '__main__':
    visual_ok = test_visual_quality()
    encoding_ok = test_template_encoding()
    
    success = visual_ok and encoding_ok
    sys.exit(0 if success else 1)

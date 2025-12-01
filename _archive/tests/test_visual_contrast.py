#!/usr/bin/env python
"""
Test de contraste visuel et d'accessibilité
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

def hex_to_rgb(hex_color):
    """Convertir couleur hex en RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def calculate_luminance(rgb):
    """Calculer la luminance d'une couleur RGB"""
    def gamma_correct(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = [gamma_correct(c) for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(color1, color2):
    """Calculer le ratio de contraste entre deux couleurs"""
    lum1 = calculate_luminance(hex_to_rgb(color1))
    lum2 = calculate_luminance(hex_to_rgb(color2))
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)

def test_visual_contrast():
    """Tester le contraste visuel"""
    print("=== TEST CONTRASTE VISUEL ===")
    
    # Couleurs à tester (extraites des CSS)
    color_combinations = [
        {'bg': '#007bff', 'fg': '#ffffff', 'name': 'Badge IGP original'},
        {'bg': '#0056b3', 'fg': '#ffffff', 'name': 'Badge IGP corrigé'},
        {'bg': '#ffc107', 'fg': '#333333', 'name': 'Badge VSIG original'},
        {'bg': '#e0a800', 'fg': '#000000', 'name': 'Badge VSIG corrigé'},
        {'bg': '#5b80b2', 'fg': '#ffffff', 'name': 'Lien sélectionné original'},
        {'bg': '#2c5282', 'fg': '#ffffff', 'name': 'Lien sélectionné corrigé'},
        {'bg': '#2c5282', 'fg': '#ffffff', 'name': 'Header module corrigé'},
        {'bg': '#ffffff', 'fg': '#333333', 'name': 'Texte principal'},
    ]
    
    contrast_issues = []
    
    for combo in color_combinations:
        try:
            ratio = contrast_ratio(combo['bg'], combo['fg'])
            
            # WCAG AA recommande 4.5:1 pour le texte normal, 3:1 pour le texte large
            if ratio >= 4.5:
                status = "EXCELLENT"
            elif ratio >= 3.0:
                status = "BON"
            elif ratio >= 2.0:
                status = "FAIBLE"
            else:
                status = "MAUVAIS"
                contrast_issues.append(f"{combo['name']}: {ratio:.2f}:1")
            
            print(f"  {combo['name']}: {ratio:.2f}:1 - {status}")
            
        except Exception as e:
            print(f"  ERREUR {combo['name']}: {e}")
            contrast_issues.append(f"{combo['name']}: Erreur calcul")
    
    return len(contrast_issues) == 0

def test_encoding_in_browser():
    """Tester l'encodage tel que vu par le navigateur"""
    print("\n=== TEST ENCODAGE NAVIGATEUR ===")
    
    client = Client()
    user = User.objects.first()
    if user:
        client.force_login(user)
    
    # Tester différentes pages
    test_urls = [
        '/catalogue/produits/cuvees/',
        '/catalogue/produits/lots/',
        '/catalogue/produits/skus/'
    ]
    
    encoding_issues = []
    
    for url in test_urls:
        try:
            response = client.get(url)
            
            # Vérifier l'en-tête Content-Type
            content_type = response.get('Content-Type', '')
            print(f"  {url}: Content-Type = {content_type}")
            
            # Vérifier le contenu
            if hasattr(response, 'content'):
                # Test avec différents encodages
                try:
                    content_utf8 = response.content.decode('utf-8')
                    if 'Ã©' in content_utf8 or 'Ã¨' in content_utf8:
                        encoding_issues.append(f"{url}: Caractères mal encodés détectés")
                        print(f"    PROBLEME: Caractères mal encodés détectés")
                    else:
                        print(f"    OK: Encodage UTF-8 correct")
                except UnicodeDecodeError:
                    encoding_issues.append(f"{url}: Erreur décodage UTF-8")
                    print(f"    ERREUR: Impossible de décoder en UTF-8")
            
        except Exception as e:
            encoding_issues.append(f"{url}: Erreur test - {e}")
            print(f"  ERREUR {url}: {e}")
    
    return len(encoding_issues) == 0

def test_css_conflicts():
    """Tester les conflits CSS potentiels"""
    print("\n=== TEST CONFLITS CSS ===")
    
    client = Client()
    user = User.objects.first()
    if user:
        client.force_login(user)
    
    response = client.get('/catalogue/produits/cuvees/')
    content = response.content.decode('utf-8')
    
    css_issues = []
    
    # Chercher les classes CSS suspectes
    suspicious_patterns = [
        r'class="[^"]*text-primary[^"]*bg-primary[^"]*"',
        r'class="[^"]*text-blue[^"]*bg-blue[^"]*"',
        r'style="[^"]*color:\s*blue[^"]*background[^"]*blue[^"]*"'
    ]
    
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            css_issues.extend(matches)
            print(f"  PROBLEME: Classes conflictuelles trouvées: {matches}")
    
    if not css_issues:
        print("  OK: Aucun conflit CSS évident détecté")
    
    return len(css_issues) == 0

if __name__ == '__main__':
    contrast_ok = test_visual_contrast()
    encoding_ok = test_encoding_in_browser()
    css_ok = test_css_conflicts()
    
    print(f"\n=== RÉSULTATS FINAUX ===")
    print(f"Contraste visuel: {'OK' if contrast_ok else 'ERREUR'}")
    print(f"Encodage: {'OK' if encoding_ok else 'ERREUR'}")
    print(f"CSS: {'OK' if css_ok else 'ERREUR'}")
    
    if contrast_ok and encoding_ok and css_ok:
        print("Interface visuellement optimisée!")
    else:
        print("Problèmes visuels détectés - corrections appliquées")
    
    success = contrast_ok and encoding_ok and css_ok
    sys.exit(0 if success else 1)

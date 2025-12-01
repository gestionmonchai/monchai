#!/usr/bin/env python
"""
Test de résolution bidirectionnelle des URLs
Vérifie que toutes les URLs peuvent être résolues et inversées
"""
import os
import sys
import django
import json
from urllib.parse import urlparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.urls import resolve, reverse, NoReverseMatch
from django.core.management import call_command
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

def test_url_resolution():
    """Test la résolution bidirectionnelle des URLs"""
    print("=== Test de résolution bidirectionnelle des URLs ===\n")
    
    # Récupérer la liste des URLs
    try:
        from io import StringIO
        out = StringIO()
        call_command('show_urls', format='json', stdout=out)
        urls_data = json.loads(out.getvalue())
    except Exception as e:
        print(f"[ERROR] Erreur recuperation URLs: {e}")
        return False
    
    print(f"[INFO] {len(urls_data)} URLs trouvees\n")
    
    errors = []
    success_count = 0
    
    # Test de résolution pour chaque URL
    for url_info in urls_data:
        url_pattern = url_info['url']
        url_name = url_info['name']
        module_name = url_info['module']
        
        # Skip les URLs avec paramètres complexes pour ce test basique
        if '<' in url_pattern and '>' in url_pattern:
            continue
            
        # Skip les URLs statiques
        if 'static' in url_pattern or 'media' in url_pattern:
            continue
            
        try:
            # Test resolve
            resolved = resolve(url_pattern)
            
            # Test reverse si name disponible
            if url_name:
                try:
                    reversed_url = reverse(url_name)
                    success_count += 1
                    print(f"[OK] {url_pattern} -> {url_name}")
                except NoReverseMatch as e:
                    errors.append({
                        'type': 'NoReverseMatch',
                        'url': url_pattern,
                        'name': url_name,
                        'error': str(e)
                    })
                    print(f"[ERROR] NoReverseMatch: {url_name}")
            else:
                success_count += 1
                print(f"[OK] {url_pattern} (pas de name)")
                
        except Exception as e:
            errors.append({
                'type': 'ResolveError',
                'url': url_pattern,
                'name': url_name,
                'module': module_name,
                'error': str(e)
            })
            print(f"[ERROR] ResolveError: {url_pattern} - {e}")
    
    # Résumé
    print(f"\n[RESUME] Resume:")
    print(f"[OK] Succes: {success_count}")
    print(f"[ERROR] Erreurs: {len(errors)}")
    
    if errors:
        print(f"\n[DETAIL] Detail des erreurs:")
        for error in errors[:10]:  # Limiter à 10 erreurs
            print(f"  - {error['type']}: {error['url']} ({error.get('name', 'no name')})")
            print(f"    {error['error']}")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_url_resolution()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""
Test de résolution bidirectionnelle des URLs
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch, Resolver404
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def extract_named_urls(resolver, prefix=''):
    """Extraire toutes les URLs nommées"""
    urls = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLPattern):
            name = getattr(pattern, 'name', None)
            if name:
                urls.append({
                    'name': name,
                    'pattern': prefix + str(pattern.pattern)
                })
        elif isinstance(pattern, URLResolver):
            namespace = getattr(pattern, 'namespace', '')
            new_prefix = prefix + str(pattern.pattern)
            nested_urls = extract_named_urls(pattern, new_prefix)
            for url in nested_urls:
                if namespace:
                    url['name'] = f'{namespace}:{url["name"]}'
            urls.extend(nested_urls)
    return urls

def test_url_resolution():
    """Tester la résolution bidirectionnelle des URLs"""
    print("=== TEST RÉSOLUTION BIDIRECTIONNELLE ===")
    
    resolver = get_resolver()
    named_urls = extract_named_urls(resolver)
    
    errors = []
    success_count = 0
    
    # URLs simples à tester (sans paramètres)
    simple_urls = [
        'catalogue:products_dashboard',
        'catalogue:products_cuvees', 
        'catalogue:products_lots',
        'catalogue:products_skus',
        'catalogue:products_referentiels',
        'auth:login',
        'auth:logout',
        'admin:index'
    ]
    
    print(f"Test de {len(simple_urls)} URLs importantes...")
    
    for url_name in simple_urls:
        try:
            # Test reverse (name -> path)
            path = reverse(url_name)
            print(f"  {url_name} -> {path}")
            
            # Test resolve (path -> callback)
            match = resolve(path)
            print(f"    resolve: {match.func.__module__}.{match.func.__name__}")
            
            success_count += 1
            
        except NoReverseMatch as e:
            errors.append(f"NoReverseMatch pour '{url_name}': {e}")
        except Resolver404 as e:
            errors.append(f"Resolver404 pour '{url_name}': {e}")
        except Exception as e:
            errors.append(f"Erreur pour '{url_name}': {e}")
    
    print(f"\nRésultats: {success_count}/{len(simple_urls)} URLs OK")
    
    if errors:
        print("\nERREURS détectées:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("Toutes les URLs importantes résolvent correctement!")
        return True

if __name__ == '__main__':
    success = test_url_resolution()
    sys.exit(0 if success else 1)

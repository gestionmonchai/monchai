#!/usr/bin/env python
"""
Script d'analyse des URLs pour la batterie de tests
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def extract_urls(resolver, prefix=''):
    urls = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLPattern):
            name = getattr(pattern, 'name', None)
            callback = getattr(pattern, 'callback', None)
            if callback:
                callback_name = f'{callback.__module__}.{callback.__name__}'
            else:
                callback_name = 'Unknown'
            
            urls.append({
                'pattern': prefix + str(pattern.pattern),
                'name': name,
                'callback': callback_name
            })
        elif isinstance(pattern, URLResolver):
            namespace = getattr(pattern, 'namespace', '')
            new_prefix = prefix + str(pattern.pattern)
            nested_urls = extract_urls(pattern, new_prefix)
            for url in nested_urls:
                if namespace and url['name']:
                    url['name'] = f'{namespace}:{url["name"]}'
            urls.extend(nested_urls)
    return urls

def main():
    print("=== ANALYSE DES URLs ===")
    
    resolver = get_resolver()
    all_urls = extract_urls(resolver)
    
    print(f'Total URLs trouvées: {len(all_urls)}')
    
    # URLs avec noms
    named_urls = [u for u in all_urls if u['name']]
    print(f'URLs nommées: {len(named_urls)}')
    
    # Vérifier doublons de noms
    names = [u['name'] for u in named_urls if u['name']]
    duplicates = [name for name in set(names) if names.count(name) > 1]
    if duplicates:
        print(f'ERREUR - DOUBLONS détectés: {duplicates}')
    else:
        print('OK - Aucun doublon de nom détecté')
    
    # URLs catalogue
    print('\n=== URLs CATALOGUE ===')
    catalogue_urls = [u for u in all_urls if 'catalogue' in u['pattern']]
    for url in catalogue_urls:
        print(f'  {url["pattern"]} -> {url["name"]} ({url["callback"]})')
    
    # URLs importantes à tester
    print('\n=== URLs IMPORTANTES À TESTER ===')
    important_patterns = ['/', '/catalogue/', '/api/', '/admin/', '/auth/']
    for pattern in important_patterns:
        matching = [u for u in all_urls if u['pattern'].startswith(pattern)]
        if matching:
            print(f'\n{pattern}:')
            for url in matching[:5]:  # Limiter à 5 par catégorie
                print(f'  {url["pattern"]} -> {url["name"]}')
    
    return len(duplicates) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

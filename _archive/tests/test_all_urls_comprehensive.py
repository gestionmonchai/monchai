#!/usr/bin/env python
"""
TEST EXHAUSTIF DE TOUTES LES URLs ET FONCTIONS
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
import re

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.accounts.models import Organization, Membership

def extract_all_urls(resolver, prefix=''):
    """Extrait toutes les URLs du système"""
    urls = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLPattern):
            name = getattr(pattern, 'name', None)
            callback = getattr(pattern, 'callback', None)
            if callback:
                callback_name = f'{callback.__module__}.{callback.__name__}'
            else:
                callback_name = 'Unknown'
            
            # Convertir le pattern en URL testable
            pattern_str = str(pattern.pattern)
            # Remplacer les paramètres par des valeurs de test
            test_url = convert_pattern_to_url(prefix + pattern_str)
            
            urls.append({
                'pattern': prefix + pattern_str,
                'test_url': test_url,
                'name': name,
                'callback': callback_name
            })
        elif isinstance(pattern, URLResolver):
            namespace = getattr(pattern, 'namespace', '')
            new_prefix = prefix + str(pattern.pattern)
            nested_urls = extract_all_urls(pattern, new_prefix)
            for url in nested_urls:
                if namespace and url['name']:
                    url['name'] = f'{namespace}:{url["name"]}'
            urls.extend(nested_urls)
    return urls

def convert_pattern_to_url(pattern):
    """Convertit un pattern Django en URL testable"""
    # Supprimer les caractères regex de début/fin
    url = pattern.replace('^', '').replace('$', '')
    
    # Remplacer les paramètres communs
    replacements = {
        r'<int:pk>': '1',
        r'<int:id>': '1',
        r'<uuid:pk>': '550e8400-e29b-41d4-a716-446655440000',
        r'<uuid:id>': '550e8400-e29b-41d4-a716-446655440000',
        r'<uuid:cuvee_id>': '550e8400-e29b-41d4-a716-446655440000',
        r'<str:token>': 'test-token-123',
        r'<path:object_id>': '1',
        r'<slug:slug>': 'test-slug',
        r'(?P<app_label>auth|accounts|referentiels|catalogue|viticulture|stock|sales|billing|imports|clients)': 'viticulture',
    }
    
    for pattern_regex, replacement in replacements.items():
        url = re.sub(pattern_regex, replacement, url)
    
    # Nettoyer les caractères regex restants
    url = re.sub(r'\(\?\P<[^>]+>[^)]*\)', '', url)
    url = re.sub(r'[()^$]', '', url)
    
    # S'assurer que l'URL commence par /
    if not url.startswith('/'):
        url = '/' + url
    
    return url

def test_url_with_client(client, url, url_info):
    """Teste une URL avec le client"""
    try:
        response = client.get(url, follow=False)
        status = response.status_code
        
        # Analyser le résultat
        if status == 200:
            return "OK"
        elif status == 302:
            location = response.get('Location', '')
            if '/auth/login' in location:
                return "Redir Login"
            else:
                return f"Redir {location[:50]}"
        elif status == 403:
            return "403 FORBIDDEN"
        elif status == 404:
            return "404 Not Found"
        elif status == 405:
            return "405 Method Not Allowed"
        elif status == 500:
            return "500 Server Error"
        else:
            return f"{status}"
            
    except Exception as e:
        return f"Exception: {str(e)[:50]}"

def main():
    print("=" * 80)
    print("TEST EXHAUSTIF DE TOUTES LES URLs ET FONCTIONS")
    print("=" * 80)
    
    # Extraire toutes les URLs
    resolver = get_resolver()
    all_urls = extract_all_urls(resolver)
    
    print(f"Total URLs decouvertes: {len(all_urls)}")
    
    # Créer un client de test
    client = Client()
    
    # Test spécifique de l'URL mentionnée
    print("\n" + "=" * 50)
    print("TEST URL SPECIFIQUE: /admin/viticulture/cuvee/add/")
    print("=" * 50)
    
    specific_url = "/admin/viticulture/cuvee/add/"
    print(f"Sans auth: {test_url_with_client(client, specific_url, {})}")
    
    # Authentification
    User = get_user_model()
    user = User.objects.first()
    if user:
        client.force_login(user)
        print(f"Avec auth ({user.email}): {test_url_with_client(client, specific_url, {})}")
    
    # Test par catégories
    categories = {
        'Admin': [],
        'Auth': [],
        'Catalogue': [],
        'Viticulture': [],
        'Stock': [],
        'Sales': [],
        'API': [],
        'Autres': []
    }
    
    # Classifier les URLs
    for url_info in all_urls:
        url = url_info['test_url']
        if '/admin/' in url:
            categories['Admin'].append(url_info)
        elif '/auth/' in url:
            categories['Auth'].append(url_info)
        elif '/catalogue/' in url:
            categories['Catalogue'].append(url_info)
        elif '/viticulture/' in url:
            categories['Viticulture'].append(url_info)
        elif '/stock/' in url:
            categories['Stock'].append(url_info)
        elif '/sales/' in url:
            categories['Sales'].append(url_info)
        elif '/api/' in url:
            categories['API'].append(url_info)
        else:
            categories['Autres'].append(url_info)
    
    # Tester chaque catégorie
    for category, urls in categories.items():
        if not urls:
            continue
            
        print(f"\n" + "=" * 50)
        print(f"CATEGORIE: {category} ({len(urls)} URLs)")
        print("=" * 50)
        
        # Limiter à 20 URLs par catégorie pour éviter la surcharge
        test_urls = urls[:20]
        if len(urls) > 20:
            print(f"Affichage limite aux 20 premieres URLs sur {len(urls)}")
        
        for url_info in test_urls:
            url = url_info['test_url']
            name = url_info['name'] or 'No name'
            
            # Test sans auth
            result_no_auth = test_url_with_client(Client(), url, url_info)
            
            # Test avec auth
            auth_client = Client()
            if user:
                auth_client.force_login(user)
                result_with_auth = test_url_with_client(auth_client, url, url_info)
            else:
                result_with_auth = "No user"
            
            print(f"{url:<50} | Sans: {result_no_auth:<15} | Avec: {result_with_auth:<15} | {name}")
    
    # Résumé des erreurs critiques
    print(f"\n" + "=" * 80)
    print("RESUME DES ERREURS CRITIQUES")
    print("=" * 80)
    
    critical_errors = []
    auth_client = Client()
    if user:
        auth_client.force_login(user)
    
    for url_info in all_urls:
        url = url_info['test_url']
        result = test_url_with_client(auth_client, url, url_info)
        
        if "403 FORBIDDEN" in result or "500 Server Error" in result:
            critical_errors.append((url, result, url_info['name']))
    
    if critical_errors:
        print(f"{len(critical_errors)} erreurs critiques detectees:")
        for url, error, name in critical_errors[:10]:  # Limiter à 10
            print(f"  {url} -> {error} ({name})")
    else:
        print("Aucune erreur critique detectee!")
    
    print(f"\nSTATISTIQUES FINALES:")
    print(f"  - URLs testees: {len(all_urls)}")
    print(f"  - Erreurs critiques: {len(critical_errors)}")
    print(f"  - Utilisateur test: {user.email if user else 'Aucun'}")

if __name__ == '__main__':
    main()

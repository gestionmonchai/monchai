#!/usr/bin/env python
"""
Smoke crawl test - vérifie que les pages principales sont accessibles
"""
import os
import sys
import django
from urllib.parse import urljoin, urlparse
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership
from tests.factories import UserFactory, OrganizationFactory, MembershipFactory

def extract_links(html_content, base_url):
    """Extrait les liens internes d'une page HTML"""
    links = set()
    # Pattern pour trouver les href
    href_pattern = r'href=["\']([^"\']+)["\']'
    matches = re.findall(href_pattern, html_content)
    
    for match in matches:
        # Skip les liens externes, ancres, mailto, etc.
        if match.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
            continue
        if match.startswith('javascript:'):
            continue
        if match.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
            continue
            
        # Construire l'URL complète
        if match.startswith('/'):
            full_url = match
        else:
            full_url = urljoin(base_url, match)
            
        # Nettoyer les paramètres de query pour éviter les doublons
        if '?' in full_url:
            full_url = full_url.split('?')[0]
            
        links.add(full_url)
    
    return links

def test_smoke_crawl():
    """Test smoke crawl des pages principales"""
    print("=== Smoke Crawl Test ===\n")
    
    # Utiliser un utilisateur existant ou en créer un simple
    try:
        User = get_user_model()
        # Essayer de récupérer un utilisateur existant
        try:
            user = User.objects.filter(is_active=True).first()
            if user and hasattr(user, 'memberships') and user.memberships.exists():
                membership = user.memberships.first()
                org = membership.organization
                print(f"[SETUP] Utilisateur existant utilise: {user.email}")
            else:
                raise User.DoesNotExist()
        except (User.DoesNotExist, AttributeError):
            # Créer un utilisateur simple
            user = User.objects.create_user(
                email='test_smoke_simple@example.com',
                password='testpass123'
            )
            org = Organization.objects.create(
                name='Test Smoke Simple Org',
                siret='98765432109876',
                is_initialized=True
            )
            membership = Membership.objects.create(
                user=user,
                organization=org,
                role='admin'
            )
            print(f"[SETUP] Utilisateur simple cree: {user.email}")
    except Exception as e:
        print(f"[ERROR] Erreur creation utilisateur: {e}")
        return False
    
    client = Client()
    
    # URLs de base à tester
    base_urls = [
        '/',
        '/dashboard/',
        '/auth/login/',
        '/catalogue/',
        '/ref/',
        '/clients/',
        '/stocks/',
    ]
    
    visited = set()
    to_visit = set(base_urls)
    errors = []
    success_count = 0
    redirect_chains = {}
    
    # Test sans authentification d'abord
    print("[INFO] Test sans authentification...")
    for url in base_urls[:3]:  # Seulement /, /dashboard/, /auth/login/
        try:
            response = client.get(url, follow=True)
            if response.status_code in [200, 302]:
                success_count += 1
                print(f"[OK] {url} -> {response.status_code}")
                
                # Tracker les redirections
                if hasattr(response, 'redirect_chain') and response.redirect_chain:
                    redirect_chains[url] = response.redirect_chain
                    if len(response.redirect_chain) > 5:
                        errors.append({
                            'type': 'TooManyRedirects',
                            'url': url,
                            'redirects': len(response.redirect_chain)
                        })
            else:
                errors.append({
                    'type': 'BadStatus',
                    'url': url,
                    'status': response.status_code
                })
                print(f"[ERROR] {url} -> {response.status_code}")
        except Exception as e:
            errors.append({
                'type': 'Exception',
                'url': url,
                'error': str(e)
            })
            print(f"[ERROR] {url} -> Exception: {e}")
    
    # Test avec authentification
    print(f"\n[INFO] Test avec authentification...")
    client.force_login(user)
    
    for url in base_urls:
        try:
            response = client.get(url, follow=True)
            if response.status_code == 200:
                success_count += 1
                print(f"[OK] {url} -> {response.status_code}")
                
                # Extraire les liens de la page
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8', errors='ignore')
                    links = extract_links(content, url)
                    
                    # Tester quelques liens internes (limité pour éviter explosion)
                    for link in list(links)[:5]:  # Max 5 liens par page
                        if link not in visited and link not in to_visit:
                            to_visit.add(link)
                            
            elif response.status_code in [301, 302]:
                success_count += 1
                print(f"[OK] {url} -> {response.status_code} (redirect)")
                
                # Tracker les redirections
                if hasattr(response, 'redirect_chain') and response.redirect_chain:
                    redirect_chains[url] = response.redirect_chain
                    if len(response.redirect_chain) > 5:
                        errors.append({
                            'type': 'TooManyRedirects',
                            'url': url,
                            'redirects': len(response.redirect_chain)
                        })
            else:
                errors.append({
                    'type': 'BadStatus',
                    'url': url,
                    'status': response.status_code
                })
                print(f"[ERROR] {url} -> {response.status_code}")
                
        except Exception as e:
            errors.append({
                'type': 'Exception',
                'url': url,
                'error': str(e)
            })
            print(f"[ERROR] {url} -> Exception: {e}")
        
        visited.add(url)
    
    # Tester quelques liens découverts (limité)
    discovered_links = list(to_visit - visited)[:10]  # Max 10 liens supplémentaires
    if discovered_links:
        print(f"\n[INFO] Test de {len(discovered_links)} liens decouverts...")
        for url in discovered_links:
            try:
                response = client.get(url, follow=True)
                if response.status_code in [200, 301, 302]:
                    success_count += 1
                    print(f"[OK] {url} -> {response.status_code}")
                else:
                    errors.append({
                        'type': 'BadStatus',
                        'url': url,
                        'status': response.status_code
                    })
                    print(f"[ERROR] {url} -> {response.status_code}")
            except Exception as e:
                errors.append({
                    'type': 'Exception',
                    'url': url,
                    'error': str(e)
                })
                print(f"[ERROR] {url} -> Exception: {e}")
    
    # Résumé
    print(f"\n[RESUME] Smoke Crawl Resume:")
    print(f"[OK] Pages testees: {len(visited) + len(discovered_links)}")
    print(f"[OK] Succes: {success_count}")
    print(f"[ERROR] Erreurs: {len(errors)}")
    
    if redirect_chains:
        print(f"\n[INFO] Chaines de redirection detectees:")
        for url, chain in redirect_chains.items():
            print(f"  {url} -> {len(chain)} redirections")
            if len(chain) > 3:
                print(f"    {' -> '.join([str(r[0]) for r in chain[:3]])}...")
    
    if errors:
        print(f"\n[DETAIL] Detail des erreurs:")
        for error in errors[:10]:
            print(f"  - {error['type']}: {error['url']}")
            if 'status' in error:
                print(f"    Status: {error['status']}")
            if 'error' in error:
                print(f"    Error: {error['error']}")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_smoke_crawl()
    sys.exit(0 if success else 1)

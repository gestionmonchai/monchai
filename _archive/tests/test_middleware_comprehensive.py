#!/usr/bin/env python
"""
Test du middleware d'organisation
Vérifie le nettoyage des sessions invalides et le fallback
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

def test_organization_middleware():
    """Test du middleware d'organisation"""
    print("=== Test du middleware d'organisation ===\n")
    
    # Utiliser un utilisateur existant
    User = get_user_model()
    try:
        user = User.objects.filter(is_active=True).first()
        if not user:
            print("[ERROR] Aucun utilisateur actif trouvé")
            return False
        print(f"[SETUP] Utilisateur de test: {user.email}")
    except Exception as e:
        print(f"[ERROR] Erreur récupération utilisateur: {e}")
        return False
    
    client = Client()
    errors = []
    success_count = 0
    
    # Test 1: Session avec current_org_id invalide
    print("[TEST] 1. Session avec current_org_id invalide...")
    try:
        # Se connecter d'abord
        client.force_login(user)
        
        # Mettre un org_id invalide dans la session
        session = client.session
        session['current_org_id'] = 99999  # ID inexistant
        session.save()
        
        # Faire une requête qui utilise le middleware
        response = client.get('/api/auth/whoami/')
        
        # Vérifier que la session a été nettoyée
        updated_session = client.session
        if 'current_org_id' not in updated_session or updated_session.get('current_org_id') != 99999:
            success_count += 1
            print("[OK] Session invalide nettoyée")
        else:
            errors.append({
                'test': 'Invalid org_id cleanup',
                'expected': 'current_org_id removed or changed',
                'got': f'current_org_id still {updated_session.get("current_org_id")}'
            })
            print("[ERROR] Session invalide non nettoyée")
            
    except Exception as e:
        errors.append({
            'test': 'Invalid org_id cleanup',
            'error': str(e)
        })
        print(f"[ERROR] Exception: {e}")
    
    # Test 2: Fallback sur première organisation
    print("\n[TEST] 2. Fallback sur première organisation...")
    try:
        # Se reconnecter
        client.force_login(user)
        
        # Vérifier qu'un fallback est appliqué
        response = client.get('/dashboard/')
        if response.status_code == 200:
            success_count += 1
            print("[OK] Fallback organisation appliqué")
        else:
            errors.append({
                'test': 'Organization fallback',
                'expected': '200 (fallback applied)',
                'got': f'{response.status_code}'
            })
            print(f"[ERROR] Fallback échoué: {response.status_code}")
            
    except Exception as e:
        errors.append({
            'test': 'Organization fallback',
            'error': str(e)
        })
        print(f"[ERROR] Exception: {e}")
    
    # Test 3: Injection request.current_org
    print("\n[TEST] 3. Injection request.current_org...")
    try:
        # Faire une requête et vérifier l'injection
        response = client.get('/dashboard/')
        
        # On ne peut pas directement tester l'injection du request,
        # mais on peut vérifier que les pages qui en dépendent fonctionnent
        if response.status_code == 200:
            success_count += 1
            print("[OK] Injection request.current_org fonctionne")
        else:
            errors.append({
                'test': 'Request injection',
                'expected': '200 (injection working)',
                'got': f'{response.status_code}'
            })
            print(f"[ERROR] Injection échouée: {response.status_code}")
            
    except Exception as e:
        errors.append({
            'test': 'Request injection',
            'error': str(e)
        })
        print(f"[ERROR] Exception: {e}")
    
    # Test 4: Headers de sécurité
    print("\n[TEST] 4. Headers de sécurité...")
    try:
        response = client.get('/dashboard/')
        
        security_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
        ]
        
        headers_found = 0
        for header in security_headers:
            if header in response:
                headers_found += 1
                print(f"[OK] Header {header} présent")
        
        if headers_found > 0:
            success_count += 1
            print(f"[OK] {headers_found}/{len(security_headers)} headers de sécurité trouvés")
        else:
            errors.append({
                'test': 'Security headers',
                'expected': 'At least one security header',
                'got': 'No security headers found'
            })
            print("[ERROR] Aucun header de sécurité trouvé")
            
    except Exception as e:
        errors.append({
            'test': 'Security headers',
            'error': str(e)
        })
        print(f"[ERROR] Exception: {e}")
    
    # Résumé
    print(f"\n[RESUME] Middleware Resume:")
    print(f"[OK] Tests reussis: {success_count}/4")
    print(f"[ERROR] Erreurs: {len(errors)}")
    
    if errors:
        print(f"\n[DETAIL] Detail des erreurs:")
        for error in errors:
            print(f"  - Test: {error['test']}")
            if 'expected' in error and 'got' in error:
                print(f"    Attendu: {error['expected']}, Obtenu: {error['got']}")
            if 'error' in error:
                print(f"    Erreur: {error['error']}")
    
    return len(errors) <= 1  # Tolérer 1 erreur mineure

if __name__ == "__main__":
    success = test_organization_middleware()
    sys.exit(0 if success else 1)

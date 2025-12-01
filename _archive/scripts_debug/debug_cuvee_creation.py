#!/usr/bin/env python
"""
DEBUG SPECIFIQUE CREATION CUVEE
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
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import Organization, Membership

def debug_cuvee_creation():
    """Debug spécifique de la création de cuvée"""
    
    print("=" * 80)
    print("DEBUG CREATION CUVEE - URL /admin/viticulture/cuvee/add/")
    print("=" * 80)
    
    User = get_user_model()
    user = User.objects.first()
    
    if not user:
        print("ERREUR: Aucun utilisateur")
        return
    
    print(f"Utilisateur: {user.email}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is active: {user.is_active}")
    
    # Vérifier les permissions spécifiques
    print(f"\n=== PERMISSIONS VITICULTURE ===")
    
    viticulture_perms = [
        'viticulture.add_cuvee',
        'viticulture.change_cuvee',
        'viticulture.delete_cuvee',
        'viticulture.view_cuvee',
    ]
    
    for perm in viticulture_perms:
        has_perm = user.has_perm(perm)
        print(f"{perm}: {has_perm}")
    
    # Vérifier les permissions admin générales
    print(f"\n=== PERMISSIONS ADMIN GENERALES ===")
    admin_perms = [
        'admin.view_logentry',
        'auth.view_user',
        'contenttypes.view_contenttype',
    ]
    
    for perm in admin_perms:
        has_perm = user.has_perm(perm)
        print(f"{perm}: {has_perm}")
    
    # Test direct avec client Django
    print(f"\n=== TEST CLIENT DJANGO ===")
    client = Client()
    client.force_login(user)
    
    url = "/admin/viticulture/cuvee/add/"
    print(f"Test URL: {url}")
    
    try:
        response = client.get(url, follow=True)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Page accessible")
            content = response.content.decode('utf-8')
            if 'Ajouter' in content and 'cuvée' in content.lower():
                print("OK: Formulaire d'ajout détecté")
            else:
                print("ATTENTION: Contenu inattendu")
                
        elif response.status_code == 403:
            print("ERREUR: 403 Forbidden")
            content = response.content.decode('utf-8')
            if 'permission' in content.lower():
                print("Cause: Problème de permissions")
            else:
                print("Cause: Autre problème d'autorisation")
                
        elif response.status_code == 302:
            print("REDIRECTION:")
            if hasattr(response, 'redirect_chain'):
                for redirect_url, status_code in response.redirect_chain:
                    print(f"  -> {redirect_url} (status {status_code})")
        
        # Afficher les headers de réponse
        print(f"\nHeaders de réponse:")
        for key, value in response.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
    
    # Vérifier la configuration admin Django
    print(f"\n=== CONFIGURATION ADMIN DJANGO ===")
    
    from django.contrib import admin
    from apps.viticulture.models import Cuvee
    
    # Vérifier si le modèle est enregistré
    if Cuvee in admin.site._registry:
        print("OK: Modèle Cuvee enregistré dans admin")
        admin_class = admin.site._registry[Cuvee]
        print(f"Admin class: {admin_class.__class__.__name__}")
        
        # Vérifier les permissions de l'admin class
        if hasattr(admin_class, 'has_add_permission'):
            try:
                from django.http import HttpRequest
                request = HttpRequest()
                request.user = user
                can_add = admin_class.has_add_permission(request)
                print(f"has_add_permission(): {can_add}")
            except Exception as e:
                print(f"Erreur has_add_permission(): {e}")
    else:
        print("ERREUR: Modèle Cuvee NON enregistré dans admin")
    
    # Vérifier les ContentTypes
    print(f"\n=== CONTENT TYPES ===")
    try:
        from django.contrib.contenttypes.models import ContentType
        cuvee_ct = ContentType.objects.get_for_model(Cuvee)
        print(f"ContentType Cuvee: {cuvee_ct}")
        
        # Vérifier les permissions associées
        perms = Permission.objects.filter(content_type=cuvee_ct)
        print(f"Permissions disponibles:")
        for perm in perms:
            print(f"  - {perm.codename}: {perm.name}")
            
    except Exception as e:
        print(f"Erreur ContentType: {e}")
    
    # Test avec superuser temporaire
    print(f"\n=== TEST SUPERUSER TEMPORAIRE ===")
    
    # Créer un superuser temporaire
    temp_user = User.objects.create_user(
        email='temp_superuser@test.com',
        password='temp123',
        is_staff=True,
        is_superuser=True
    )
    
    client_temp = Client()
    client_temp.force_login(temp_user)
    
    try:
        response_temp = client_temp.get(url, follow=True)
        print(f"Superuser test - Status: {response_temp.status_code}")
        
        if response_temp.status_code == 200:
            print("SUCCESS: Superuser peut accéder")
        else:
            print(f"ERREUR: Même le superuser ne peut pas accéder")
            
    except Exception as e:
        print(f"Erreur test superuser: {e}")
    finally:
        # Nettoyer
        temp_user.delete()

def main():
    debug_cuvee_creation()

if __name__ == '__main__':
    main()

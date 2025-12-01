#!/usr/bin/env python
"""
Test de compilation des templates
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.template import loader
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
import re

def find_template_references():
    """Trouver toutes les références de templates dans le code"""
    templates = set()
    
    # Patterns à chercher
    patterns = [
        r'render\([^,]+,\s*[\'"]([^\'\"]+)[\'"]',  # render(request, "template.html")
        r'TemplateResponse\([^,]+,\s*[\'"]([^\'\"]+)[\'"]',  # TemplateResponse(request, "template.html")
        r'render_to_string\([\'"]([^\'\"]+)[\'"]',  # render_to_string("template.html")
    ]
    
    # Chercher dans les vues
    views_dirs = [
        'apps/catalogue',
        'apps/accounts', 
        'apps/referentiels',
        'apps/viticulture',
        'apps/stock',
        'apps/sales'
    ]
    
    for views_dir in views_dirs:
        views_path = os.path.join(views_dir, 'views.py')
        views_unified_path = os.path.join(views_dir, 'views_unified.py')
        
        for file_path in [views_path, views_unified_path]:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        templates.update(matches)
                        
                except Exception as e:
                    print(f"Erreur lecture {file_path}: {e}")
    
    return templates

def test_templates_compile():
    """Tester la compilation des templates"""
    print("=== TEST COMPILATION TEMPLATES ===")
    
    # Templates connus à tester
    known_templates = [
        'catalogue/products_unified.html',
        'catalogue/products_cuvees.html', 
        'catalogue/products_lots.html',
        'catalogue/products_skus.html',
        'catalogue/products_referentiels.html',
        'accounts/dashboard_placeholder.html',
        'admin/base_site.html',
    ]
    
    # Trouver templates dans le code
    found_templates = find_template_references()
    
    # Combiner les deux listes
    all_templates = set(known_templates) | found_templates
    
    print(f"Templates à tester: {len(all_templates)}")
    
    errors = []
    success_count = 0
    
    for template_name in sorted(all_templates):
        try:
            # Tenter de charger le template
            template = loader.get_template(template_name)
            print(f"  OK {template_name}")
            success_count += 1
            
        except TemplateDoesNotExist as e:
            error_msg = f"TemplateDoesNotExist: {template_name}"
            print(f"  ERREUR {error_msg}")
            errors.append(error_msg)
            
        except TemplateSyntaxError as e:
            error_msg = f"TemplateSyntaxError dans {template_name}: {e}"
            print(f"  ERREUR {error_msg}")
            errors.append(error_msg)
            
        except Exception as e:
            error_msg = f"Erreur dans {template_name}: {e}"
            print(f"  ERREUR {error_msg}")
            errors.append(error_msg)
    
    print(f"\nRésultats: {success_count}/{len(all_templates)} templates OK")
    
    if errors:
        print("\nERREURS détectées:")
        for error in errors:
            print(f"  - {error}")
        
        print("\nCORRECTIFS PROPOSÉS:")
        for error in errors:
            if "TemplateDoesNotExist" in error:
                template_name = error.split(": ")[1]
                print(f"  - Créer le template: templates/{template_name}")
        
        return False
    else:
        print("Tous les templates compilent correctement!")
        return True

if __name__ == '__main__':
    success = test_templates_compile()
    sys.exit(0 if success else 1)

#!/usr/bin/env python
"""
Test de compilation des templates
Vérifie que tous les templates référencés par les vues existent et compilent
"""
import os
import sys
import django
import re
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.template import loader, TemplateDoesNotExist, TemplateSyntaxError
from django.conf import settings
import importlib.util

def find_template_references():
    """Trouve toutes les références de templates dans le code"""
    template_refs = set()
    
    # Patterns pour trouver les références de templates
    patterns = [
        r'render\([^,]+,\s*["\']([^"\']+)["\']',  # render(request, "template.html")
        r'TemplateResponse\([^,]+,\s*["\']([^"\']+)["\']',  # TemplateResponse(request, "template.html")
        r'render_to_string\(["\']([^"\']+)["\']',  # render_to_string("template.html")
        r'template_name\s*=\s*["\']([^"\']+)["\']',  # template_name = "template.html"
    ]
    
    # Chercher dans tous les fichiers Python des apps
    apps_dir = Path('apps')
    if apps_dir.exists():
        for py_file in apps_dir.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match and not match.startswith('${'):  # Skip template variables
                            template_refs.add(match)
            except Exception as e:
                print(f"[WARNING] Erreur lecture {py_file}: {e}")
    
    return template_refs

def test_template_compilation():
    """Test la compilation de tous les templates référencés"""
    print("=== Test de compilation des templates ===\n")
    
    # Trouver les références de templates
    template_refs = find_template_references()
    print(f"[INFO] {len(template_refs)} references de templates trouvees\n")
    
    errors = []
    success_count = 0
    
    # Tester chaque template
    for template_name in sorted(template_refs):
        try:
            # Essayer de charger le template
            template = loader.get_template(template_name)
            success_count += 1
            print(f"[OK] {template_name}")
            
        except TemplateDoesNotExist as e:
            errors.append({
                'type': 'TemplateDoesNotExist',
                'template': template_name,
                'error': str(e)
            })
            print(f"[ERROR] TemplateDoesNotExist: {template_name}")
            
        except TemplateSyntaxError as e:
            errors.append({
                'type': 'TemplateSyntaxError',
                'template': template_name,
                'error': str(e)
            })
            print(f"[ERROR] TemplateSyntaxError: {template_name} - {e}")
            
        except Exception as e:
            errors.append({
                'type': 'OtherError',
                'template': template_name,
                'error': str(e)
            })
            print(f"[ERROR] OtherError: {template_name} - {e}")
    
    # Vérifier aussi les templates existants dans le dossier templates
    print(f"\n[INFO] Verification des templates existants...")
    templates_dir = Path('templates')
    if templates_dir.exists():
        existing_templates = list(templates_dir.rglob('*.html'))
        print(f"[INFO] {len(existing_templates)} fichiers templates trouves")
        
        # Tester quelques templates existants
        for template_file in existing_templates[:20]:  # Limiter à 20
            relative_path = template_file.relative_to(templates_dir)
            template_name = str(relative_path).replace('\\', '/')
            
            if template_name not in template_refs:
                try:
                    template = loader.get_template(template_name)
                    print(f"[OK] {template_name} (non référencé mais valide)")
                except Exception as e:
                    print(f"[WARNING] {template_name} (non référencé, erreur: {e})")
    
    # Résumé
    print(f"\n[RESUME] Compilation Templates Resume:")
    print(f"[OK] Templates references: {len(template_refs)}")
    print(f"[OK] Succes: {success_count}")
    print(f"[ERROR] Erreurs: {len(errors)}")
    
    if errors:
        print(f"\n[DETAIL] Detail des erreurs:")
        for error in errors:
            print(f"  - {error['type']}: {error['template']}")
            print(f"    {error['error']}")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_template_compilation()
    sys.exit(0 if success else 1)

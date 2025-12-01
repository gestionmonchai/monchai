"""
Script d'audit complet des URLs dans les templates
Détecte les URLs hardcodées qui devraient utiliser {% url %}
"""
import os
import re
from pathlib import Path

# Patterns à détecter
PROBLEMATIC_PATTERNS = [
    (r'href="/admin/', 'URL admin hardcodée'),
    (r'href="/ventes/', 'URL ventes hardcodée (devrait utiliser {% url %})', ['ventes/primeur/', 'ventes/vrac/']),  # Exceptions pour nouvelles pages
    (r'href="/production/', 'URL production hardcodée'),
    (r'href="/stocks/', 'URL stocks hardcodée'),
    (r'href="/catalogue/', 'URL catalogue hardcodée'),
    (r'href="/clients/', 'URL clients hardcodée'),
    (r'href="/referentiels/', 'URL referentiels hardcodée'),
]

# Mappings des URLs admin vers les vraies URLs
URL_MAPPINGS = {
    '/admin/billing/invoice/': "{% url 'ventes:factures_list' %}",
    '/admin/production/vendangereception/': "{% url 'production:vendanges_list' %}",
    '/admin/sales/order/': "{% url 'ventes:cmd_list' %}",
    '/admin/sales/quote/': "{% url 'ventes:devis_list' %}",
    '/admin/clients/customer/': "{% url 'ventes:clients_list' %}",
}

def scan_template_file(file_path):
    """Scanne un fichier template pour détecter les problèmes d'URLs"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for pattern, description, *exceptions in PROBLEMATIC_PATTERNS:
                # Vérifier exceptions
                skip = False
                if exceptions and exceptions[0]:
                    for exception in exceptions[0]:
                        if exception in line:
                            skip = True
                            break
                
                if skip:
                    continue
                
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Extraire l'URL complète
                    url_match = re.search(r'href="([^"]+)"', line[match.start():])
                    if url_match:
                        url = url_match.group(1)
                        
                        # Chercher une suggestion de remplacement
                        suggestion = URL_MAPPINGS.get(url, "Vérifier le mapping URL")
                        
                        issues.append({
                            'line': line_num,
                            'url': url,
                            'description': description,
                            'suggestion': suggestion,
                            'context': line.strip()
                        })
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")
    
    return issues

def scan_directory(directory):
    """Scanne récursivement tous les templates"""
    all_issues = {}
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                issues = scan_template_file(file_path)
                
                if issues:
                    rel_path = os.path.relpath(file_path, directory)
                    all_issues[rel_path] = issues
    
    return all_issues

def print_report(issues):
    """Affiche le rapport d'audit"""
    if not issues:
        print("[OK] AUCUN PROBLEME DETECTE !\n")
        return
    
    print("=" * 80)
    print("*** RAPPORT D'AUDIT DES URLs")
    print("=" * 80)
    print()
    
    total_issues = sum(len(file_issues) for file_issues in issues.values())
    print(f"[WARN] {total_issues} probleme(s) detecte(s) dans {len(issues)} fichier(s)\n")
    
    for file_path, file_issues in sorted(issues.items()):
        print(f"[FILE] {file_path}")
        print("-" * 80)
        
        for issue in file_issues:
            print(f"  Ligne {issue['line']}: {issue['description']}")
            print(f"  URL actuelle  : {issue['url']}")
            print(f"  Suggestion    : {issue['suggestion']}")
            print(f"  Contexte      : {issue['context'][:100]}...")
            print()
        
        print()

def generate_fix_script(issues):
    """Génère un script Python pour corriger automatiquement"""
    if not issues:
        return
    
    print("=" * 80)
    print("*** SCRIPT DE CORRECTION AUTOMATIQUE")
    print("=" * 80)
    print()
    
    print("# Corrections à appliquer manuellement:")
    print()
    
    for file_path, file_issues in sorted(issues.items()):
        print(f"# Fichier: {file_path}")
        for issue in file_issues:
            if issue['suggestion'] in URL_MAPPINGS.values():
                print(f"# Ligne {issue['line']}: Remplacer '{issue['url']}' par {issue['suggestion']}")
        print()

if __name__ == '__main__':
    # Chemin vers le dossier templates
    templates_dir = Path(__file__).parent / 'templates'
    
    if not templates_dir.exists():
        print(f"[ERREUR] Dossier templates introuvable: {templates_dir}")
        exit(1)
    
    print("*** Scan des templates en cours...")
    print()
    
    issues = scan_directory(templates_dir)
    print_report(issues)
    
    if issues:
        generate_fix_script(issues)
        
        print("=" * 80)
        print("*** RESUME")
        print("=" * 80)
        print()
        print("Actions recommandees:")
        print("1. Verifier chaque URL detectee")
        print("2. Remplacer les URLs hardcodees par {% url 'namespace:name' %}")
        print("3. Tester toutes les pages apres correction")
        print()

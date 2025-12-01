#!/usr/bin/env python
"""
Script d'analyse de couverture de tests - Sprint 08
Objectif: Atteindre >70% de couverture selon roadmap 08
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')

def run_coverage_analysis():
    """Exécuter l'analyse de couverture et générer un rapport"""
    print("Analyse de la couverture de tests - Sprint 08")
    print("=" * 50)
    
    # Exécuter les tests avec couverture
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=apps",
        "--cov-report=term",
        "--cov-report=html:htmlcov",
        "--cov-report=json:coverage.json",
        "--maxfail=1",
        "-q"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode != 0:
            print("[ERREUR] Erreur lors de l'execution des tests:")
            print(result.stdout)
            print(result.stderr)
            return False
            
        print("[OK] Tests executes avec succes")
        print(result.stdout)
        
        # Analyser le fichier JSON de couverture
        coverage_file = project_root / "coverage.json"
        if coverage_file.exists():
            analyze_coverage_json(coverage_file)
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        return False

def analyze_coverage_json(coverage_file):
    """Analyser le fichier JSON de couverture"""
    try:
        with open(coverage_file, 'r') as f:
            data = json.load(f)
        
        total_coverage = data['totals']['percent_covered']
        print(f"\nCOUVERTURE GLOBALE: {total_coverage:.1f}%")
        
        target_coverage = 70.0
        if total_coverage >= target_coverage:
            print(f"[OK] Objectif atteint! (>={target_coverage}%)")
        else:
            print(f"[ATTENTION] Objectif non atteint (cible: {target_coverage}%)")
            print(f"   Manque: {target_coverage - total_coverage:.1f}%")
        
        # Analyser par fichier
        print("\nCOUVERTURE PAR FICHIER:")
        print("-" * 50)
        
        files_coverage = []
        for filename, file_data in data['files'].items():
            if 'apps/' in filename and not filename.endswith('test_'):
                coverage_pct = (file_data['summary']['covered_lines'] / 
                              file_data['summary']['num_statements'] * 100 
                              if file_data['summary']['num_statements'] > 0 else 0)
                files_coverage.append((filename, coverage_pct, file_data['summary']))
        
        # Trier par couverture croissante
        files_coverage.sort(key=lambda x: x[1])
        
        for filename, coverage_pct, summary in files_coverage:
            status = "[OK]" if coverage_pct >= 70 else "[KO]" if coverage_pct < 50 else "[WARN]"
            print(f"{status} {filename:<50} {coverage_pct:>6.1f}% "
                  f"({summary['covered_lines']}/{summary['num_statements']})")
        
        # Recommandations
        print("\nRECOMMANDATIONS:")
        print("-" * 50)
        
        low_coverage_files = [f for f in files_coverage if f[1] < 50]
        if low_coverage_files:
            print("Priorite haute - Fichiers avec couverture <50%:")
            for filename, coverage_pct, _ in low_coverage_files[:3]:
                print(f"   • {filename} ({coverage_pct:.1f}%)")
        
        medium_coverage_files = [f for f in files_coverage if 50 <= f[1] < 70]
        if medium_coverage_files:
            print("Priorite moyenne - Fichiers avec couverture 50-70%:")
            for filename, coverage_pct, _ in medium_coverage_files[:3]:
                print(f"   • {filename} ({coverage_pct:.1f}%)")
        
        print(f"\nRapport HTML genere: file://{project_root}/htmlcov/index.html")
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'analyse: {e}")

def main():
    """Point d'entrée principal"""
    success = run_coverage_analysis()
    
    if success:
        print("\n[OK] Analyse terminee avec succes!")
        print("Consultez le rapport HTML pour plus de details")
    else:
        print("\n[ERREUR] Analyse echouee")
        sys.exit(1)

if __name__ == "__main__":
    main()

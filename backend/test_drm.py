#!/usr/bin/env python
"""
Script de test pour la fonctionnalité DRM
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from monchai.apps.accounts.models import Domaine
from monchai.apps.drm.services import DRMExportService
from monchai.apps.drm.models import DRMExport

def test_drm_export():
    """Test de création d'un export DRM"""
    print("=== Test Export DRM ===")
    
    # Récupérer le premier domaine
    domaine = Domaine.objects.first()
    if not domaine:
        print("Aucun domaine trouve")
        return False
    
    print(f"Domaine trouve: {domaine.nom}")
    
    # Créer un export pour septembre 2025
    periode = "2025-09"
    region = "Loire"
    
    try:
        print(f"Generation export DRM pour {periode}...")
        
        # Générer l'export complet
        drm_export = DRMExportService.generer_export_complet(
            domaine=domaine,
            periode=periode,
            region=region
        )
        
        print(f"Export cree avec ID: {drm_export.id}")
        print(f"   - Statut: {drm_export.get_status_display()}")
        print(f"   - Stock debut: {drm_export.stock_debut_hl} HL")
        print(f"   - Entrees: {drm_export.entrees_hl} HL")
        print(f"   - Sorties: {drm_export.sorties_hl} HL")
        print(f"   - Stock fin: {drm_export.stock_fin_hl} HL")
        print(f"   - Fichier CSV: {drm_export.chemin_csv}")
        print(f"   - Fichier PDF: {drm_export.chemin_pdf}")
        
        # Vérifier les lignes produits
        lignes = drm_export.lignes_produits.all()
        print(f"   - Lignes produits: {lignes.count()}")
        
        for ligne in lignes:
            print(f"     * {ligne.appellation} {ligne.couleur}: {ligne.stock_fin_hl} HL")
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n=== Test API Endpoints ===")
    
    import requests
    
    base_url = "http://127.0.0.1:8000/api/drm"
    
    try:
        # Test GET exports
        response = requests.get(f"{base_url}/exports/")
        print(f"GET /exports/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            exports = data.get('results', data) if isinstance(data, dict) else data
            print(f"   - Nombre d'exports: {len(exports) if isinstance(exports, list) else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"Erreur API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Demarrage des tests DRM...")
    
    success = True
    success &= test_drm_export()
    success &= test_api_endpoints()
    
    if success:
        print("\nTous les tests sont passes avec succes!")
    else:
        print("\nCertains tests ont echoue")
        sys.exit(1)

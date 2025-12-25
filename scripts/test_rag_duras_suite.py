#!/usr/bin/env python
"""
Suite de tests automatisés pour RAG Côtes de Duras
Objectif: 100% de réponses correctes avant extension aux autres CDC
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import Client

# Scénarios de test critiques Duras
TEST_SCENARIOS = [
    {
        "id": "DURAS_CHARGE_BLANCS",
        "question": "Quelles sont les charges maximales par hectare pour les blancs en Côtes de Duras?",
        "expected_values": ["10000", "10 000", "9500", "9 500", "8500", "8 500"],
        "expected_keywords": ["kg", "hectare", "blancs secs", "densité"],
        "page_url": "/produits/",
    },
    {
        "id": "DURAS_DENSITE_ROUGE",
        "question": "Quelle densité de plantation minimale est exigée pour les nouvelles parcelles en Côtes de Duras rouge?",
        "expected_values": ["4000", "4 000", "3300", "3 300"],
        "expected_keywords": ["pieds", "hectare", "densité"],
        "page_url": "/stocks/",
    },
    {
        "id": "DURAS_RICHESSE_LIQUOREUX",
        "question": "Quelles richesses en sucre sont demandées pour un vin liquoreux Côtes de Duras?",
        "expected_values": ["185", "grammes", "g/l"],
        "expected_keywords": ["sucre", "moût", "blancs"],
        "page_url": "/drm/",
    },
    {
        "id": "DURAS_RECOLTE_ROSE",
        "question": "Quels sont les créneaux de récolte autorisés pour les raisins destinés aux rosés Côtes de Duras?",
        "expected_values": ["bonne maturité", "maturité"],
        "expected_keywords": ["récolte", "raisins"],
        "page_url": "/drm/",
    },
]

def run_test_suite():
    """Execute tous les tests et retourne le score"""
    client = Client()
    results = []
    
    print("=" * 80)
    print("SUITE DE TESTS RAG - CÔTES DE DURAS")
    print("=" * 80)
    print()
    
    for scenario in TEST_SCENARIOS:
        print(f"Test: {scenario['id']}")
        print(f"Question: {scenario['question']}")
        
        # Appel API
        payload = {
            'page_url': scenario['page_url'],
            'question': scenario['question'],
            'history': []
        }
        
        try:
            resp = client.post(
                '/api/help/query',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            if resp.status_code != 200:
                result = {
                    'id': scenario['id'],
                    'status': 'ERROR',
                    'error': f"HTTP {resp.status_code}",
                    'response': None
                }
                results.append(result)
                print(f"[ERROR] HTTP {resp.status_code}")
                print()
                continue
            
            data = resp.json()
            answer = data.get('text', '') or data.get('answer', '')
            answer_lower = answer.lower()
            
            # Vérification des valeurs attendues
            has_expected_value = any(val.lower() in answer_lower for val in scenario['expected_values'])
            
            # Vérification des mots-clés
            has_keywords = any(kw.lower() in answer_lower for kw in scenario['expected_keywords'])
            
            # Vérification citation source
            has_citation = '[DOCUMENT:' in answer or '[DURAS::' in answer
            
            # Pas d'hallucination
            no_hallucination = not any(bad in answer_lower for bad in ['sucre d\'érable', 'amargue', 'montreuil'])
            
            passed = has_expected_value and has_keywords and no_hallucination
            
            result = {
                'id': scenario['id'],
                'status': 'PASS' if passed else 'FAIL',
                'has_value': has_expected_value,
                'has_keywords': has_keywords,
                'has_citation': has_citation,
                'no_hallucination': no_hallucination,
                'response': answer[:300]
            }
            results.append(result)
            
            if passed:
                print("[PASS]")
            else:
                print("[FAIL]")
                print(f"   - Valeur attendue: {has_expected_value}")
                print(f"   - Mots-cles: {has_keywords}")
                print(f"   - Citation: {has_citation}")
                print(f"   - Pas hallucination: {no_hallucination}")
            
            print(f"Réponse: {answer[:200]}...")
            print()
            
        except Exception as e:
            result = {
                'id': scenario['id'],
                'status': 'ERROR',
                'error': str(e),
                'response': None
            }
            results.append(result)
            print(f"[EXCEPTION] {e}")
            print()
    
    # Calcul du score
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    score_pct = (passed / total * 100) if total > 0 else 0
    
    print("=" * 80)
    print(f"RÉSULTATS: {passed}/{total} tests réussis ({score_pct:.1f}%)")
    print("=" * 80)
    
    # Sauvegarde des résultats
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'tests', 'logs')
    os.makedirs(output_dir, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'rag_duras_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'score': score_pct,
            'passed': passed,
            'total': total,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Rapport sauvegardé: {output_file}")
    print()
    
    if score_pct < 100:
        print("[WARNING] OBJECTIF NON ATTEINT: Le taux de reussite doit etre de 100% avant extension.")
        return 1
    else:
        print("[SUCCESS] OBJECTIF ATTEINT: Tous les tests Duras passent a 100%!")
        return 0

if __name__ == '__main__':
    sys.exit(run_test_suite())

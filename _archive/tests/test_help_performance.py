#!/usr/bin/env python
"""
Script de test de performance du module d'aide.
Teste l'endpoint /api/help/query avec mesure de temps de réponse.
"""
import os
import sys
import django
import time
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from django.test import RequestFactory
from apps.ai.views import help_query


def test_help_performance():
    """Test de performance de l'aide avec mesure de temps."""
    factory = RequestFactory()
    
    # Questions de test
    test_cases = [
        {
            'question': 'Comment créer un client ?',
            'page_url': '/ventes/clients/',
        },
        {
            'question': 'Comment faire un devis ?',
            'page_url': '/ventes/',
        },
        {
            'question': 'Comment gérer le stock ?',
            'page_url': '/stocks/',
        },
    ]
    
    print("=" * 80)
    print("TEST DE PERFORMANCE DU MODULE D'AIDE")
    print("=" * 80)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['question']}")
        print(f"Page: {test_case['page_url']}")
        print("-" * 80)
        
        # Créer la requête
        request = factory.post(
            '/api/help/query',
            data=json.dumps(test_case),
            content_type='application/json'
        )
        
        # Mesurer le temps
        start = time.perf_counter()
        try:
            response = help_query(request)
            duration = time.perf_counter() - start
            
            # Parser la réponse
            data = json.loads(response.content.decode('utf-8'))
            
            result = {
                'question': test_case['question'],
                'status': response.status_code,
                'duration_ms': int(duration * 1000),
                'degraded': data.get('degraded', False),
                'answer_length': len(data.get('text', '') or data.get('answer', '')),
            }
            
            results.append(result)
            
            # Afficher le résultat
            print(f"[OK] Status: {result['status']}")
            print(f"[TIME] Temps: {result['duration_ms']} ms")
            print(f"[MODE] Mode degrade: {'Oui' if result['degraded'] else 'Non'}")
            print(f"[LEN] Longueur reponse: {result['answer_length']} caracteres")
            
            # Afficher un extrait de la réponse
            answer = data.get('text', '') or data.get('answer', '')
            if answer:
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"[ANSWER] Reponse: {preview}")
            
        except Exception as e:
            duration = time.perf_counter() - start
            result = {
                'question': test_case['question'],
                'status': 'ERROR',
                'duration_ms': int(duration * 1000),
                'error': str(e),
            }
            results.append(result)
            
            print(f"[ERROR] ERREUR: {e}")
            print(f"[TIME] Temps avant erreur: {result['duration_ms']} ms")
        
        print()
    
    # Résumé
    print("=" * 80)
    print("RÉSUMÉ DES PERFORMANCES")
    print("=" * 80)
    print()
    
    successful = [r for r in results if r.get('status') == 200]
    degraded = [r for r in successful if r.get('degraded')]
    errors = [r for r in results if r.get('status') not in [200, 'ERROR']]
    
    if successful:
        durations = [r['duration_ms'] for r in successful]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"[OK] Tests reussis: {len(successful)}/{len(results)}")
        print(f"[WARN] Mode degrade: {len(degraded)}/{len(successful)}")
        print(f"[ERROR] Erreurs: {len(errors)}")
        print()
        print(f"[TIME] Temps moyen: {int(avg_duration)} ms")
        print(f"[TIME] Temps min: {min_duration} ms")
        print(f"[TIME] Temps max: {max_duration} ms")
        print()
        
        # Diagnostic
        if avg_duration > 10000:
            print("[CRITICAL] CRITIQUE: Temps de reponse > 10s (tres lent)")
            print("   -> Ollama est probablement surcharge ou le modele est trop lourd")
        elif avg_duration > 5000:
            print("[WARN] ATTENTION: Temps de reponse > 5s (lent)")
            print("   -> Optimisations necessaires")
        elif avg_duration > 2000:
            print("[INFO] ACCEPTABLE: Temps de reponse > 2s (correct)")
            print("   -> Peut etre ameliore")
        else:
            print("[OK] BON: Temps de reponse < 2s (rapide)")
        
        if len(degraded) > 0:
            print()
            print("[WARN] Mode degrade active sur certaines requetes")
            print("   -> Ollama n'a pas pu repondre, fallback utilise")
    else:
        print("[ERROR] Aucun test reussi")
    
    print()
    print("=" * 80)
    
    return results


if __name__ == '__main__':
    test_help_performance()

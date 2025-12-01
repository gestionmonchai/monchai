#!/usr/bin/env python
"""Test direct d'Ollama pour diagnostiquer le problème."""
import requests
import time
import json

def test_ollama_direct():
    """Test Ollama directement sans Django."""
    url = "http://127.0.0.1:11434/api/generate"
    
    test_cases = [
        {
            'model': 'phi3:mini',
            'prompt': 'Comment créer un client ?',
            'stream': False,
        },
        {
            'model': 'monchai-help',
            'prompt': 'Comment créer un client ?',
            'stream': False,
        },
    ]
    
    print("=" * 80)
    print("TEST DIRECT OLLAMA")
    print("=" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: Modele {test['model']}")
        print("-" * 80)
        
        start = time.perf_counter()
        try:
            response = requests.post(url, json=test, timeout=30)
            duration = time.perf_counter() - start
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('response', '')
                
                print(f"[OK] Status: {response.status_code}")
                print(f"[TIME] Temps: {int(duration * 1000)} ms")
                print(f"[LEN] Longueur: {len(answer)} caracteres")
                print(f"[ANSWER] Reponse: {answer[:200]}...")
            else:
                print(f"[ERROR] Status: {response.status_code}")
                print(f"[ERROR] Reponse: {response.text[:500]}")
                
        except Exception as e:
            duration = time.perf_counter() - start
            print(f"[ERROR] Exception: {e}")
            print(f"[TIME] Temps avant erreur: {int(duration * 1000)} ms")
        
        print()

if __name__ == '__main__':
    test_ollama_direct()

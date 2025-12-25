#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE 5 — Tests smoke sur Côtes de Duras.

Usage:
    py -u tests_smoke.py
    py -u tests_smoke.py --verbose
    py -u tests_smoke.py --doc 2-cdc-aopcotes-de-duras-v20241203

Vérifie:
    - Doc routing correct
    - Pages candidates non vides
    - Validation réponse (unités, sources)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import du module ask
sys.path.insert(0, str(Path(__file__).parent))
from ask import (
    ask,
    resolve_doc_ids,
    load_appellation_index,
    load_tokens_index,
    score_pages,
    detect_question_type,
    RAG_DIR,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DURAS_DOC_ID = "2-cdc-aopcotes-de-duras-v20241203"

# Tests Côtes de Duras avec valeurs attendues
DURAS_TESTS = [
    {
        "id": "DENSITE_MINIMALE",
        "question": "Quelle est la densité de plantation minimale en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["4000", "4 000", "pieds"],
        "expected_units": ["pieds", "hectare"],
        "forbidden": ["%", "11.72", "bourgogne", "loire"],
        "question_type": "densite",
    },
    {
        "id": "DENSITE_BLANC_SEC",
        "question": "Quelle densité minimale pour les blancs secs en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["3300", "3 300"],
        "expected_units": ["pieds", "hectare"],
        "forbidden": ["%"],
        "question_type": "densite",
    },
    {
        "id": "CHARGE_BLANCS",
        "question": "Quelles sont les charges maximales par hectare pour les blancs en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["10000", "10 000", "9500", "9 500", "8500", "8 500"],
        "expected_units": ["kg", "kilogramme"],
        "forbidden": ["72", "hl", "hectolitre"],
        "question_type": "charge",
    },
    {
        "id": "CHARGE_ROUGES",
        "question": "Quelle est la charge maximale pour les vins rouges en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["10000", "10 000"],
        "expected_units": ["kg", "kilogramme"],
        "forbidden": ["72", "hl"],
        "question_type": "charge",
    },
    {
        "id": "RENDEMENT_BUTOIR",
        "question": "Quel est le rendement butoir en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["72", "66", "60"],
        "expected_units": ["hl", "hectolitre"],
        "forbidden": ["kg", "kilogramme"],
        "question_type": "rendement",
    },
    {
        "id": "RICHESSE_LIQUOREUX",
        "question": "Quelle richesse en sucre pour les liquoreux Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["185"],
        "expected_units": ["gramme", "g/l", "litre"],
        "forbidden": [],
        "question_type": "general",
    },
    {
        "id": "RICHESSE_BLANC_SEC",
        "question": "Quelle richesse en sucre pour les blancs secs Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["170"],
        "expected_units": ["gramme", "g/l", "litre"],
        "forbidden": [],
        "question_type": "general",
    },
    {
        "id": "INTER_RANG",
        "question": "Quel est l'écartement inter-rang maximal en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["2,50", "2.50", "2,5", "2.5", "3"],
        "expected_units": ["mètre", "metre", "m"],
        "forbidden": ["%"],
        "question_type": "densite",
    },
    {
        "id": "CEPAGES_ROUGES",
        "question": "Quels sont les cépages autorisés pour les rouges Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["merlot", "cabernet"],
        "expected_units": [],
        "forbidden": [],
        "question_type": "general",
    },
    {
        "id": "TAV_MINIMUM",
        "question": "Quel est le titre alcoométrique minimum en Côtes de Duras ?",
        "expected_doc": DURAS_DOC_ID,
        "expected_values": ["10", "11", "%"],
        "expected_units": ["%", "vol"],
        "forbidden": [],
        "question_type": "general",
    },
]


# ============================================================================
# TEST RUNNER
# ============================================================================

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def check_routing(question: str, expected_doc: str, rag_dir: Path) -> Tuple[bool, str]:
    """Vérifie que le routing retourne le bon doc."""
    app_index = load_appellation_index(rag_dir)
    doc_ids = resolve_doc_ids(question, app_index)
    
    if not doc_ids:
        return False, "Aucun doc trouvé"
    
    if expected_doc in doc_ids:
        return True, f"OK (position {doc_ids.index(expected_doc) + 1})"
    
    return False, f"Mauvais doc: {doc_ids[0]} (attendu: {expected_doc})"


def check_pages(question: str, doc_id: str, rag_dir: Path) -> Tuple[bool, str]:
    """Vérifie que des pages candidates sont trouvées."""
    tokens_index = load_tokens_index(rag_dir, doc_id)
    if not tokens_index:
        return False, "Index non trouvé"
    
    page_scores = score_pages(question, tokens_index)
    if not page_scores:
        return False, "Aucune page trouvée"
    
    top_pages = [p for p, s in page_scores[:3]]
    return True, f"Pages: {top_pages}"


def check_response(response: str, test: Dict) -> Tuple[bool, List[str]]:
    """Vérifie la réponse du LLM."""
    issues = []
    response_lower = response.lower()
    
    # Vérifier valeurs attendues
    has_value = any(v.lower() in response_lower for v in test['expected_values'])
    if not has_value:
        issues.append(f"Valeur manquante (attendu: {test['expected_values'][:3]})")
    
    # Vérifier unités
    if test['expected_units']:
        has_unit = any(u.lower() in response_lower for u in test['expected_units'])
        if not has_unit:
            issues.append(f"Unité manquante (attendu: {test['expected_units']})")
    
    # Vérifier interdits
    for forbidden in test['forbidden']:
        if forbidden.lower() in response_lower:
            issues.append(f"Valeur interdite trouvée: {forbidden}")
    
    # Vérifier sources
    if 'page' not in response_lower and 'source' not in response_lower:
        issues.append("Pas de citation de source")
    
    return len(issues) == 0, issues


def run_test(test: Dict, rag_dir: Path, verbose: bool = False, skip_llm: bool = False) -> Dict:
    """Exécute un test complet."""
    result = {
        'id': test['id'],
        'question': test['question'],
        'routing_ok': False,
        'pages_ok': False,
        'response_ok': False,
        'issues': [],
        'response': None,
    }
    
    # 1. Test routing
    routing_ok, routing_msg = check_routing(test['question'], test['expected_doc'], rag_dir)
    result['routing_ok'] = routing_ok
    if not routing_ok:
        result['issues'].append(f"Routing: {routing_msg}")
    elif verbose:
        log(f"  Routing: {routing_msg}", "DEBUG")
    
    # 2. Test pages
    pages_ok, pages_msg = check_pages(test['question'], test['expected_doc'], rag_dir)
    result['pages_ok'] = pages_ok
    if not pages_ok:
        result['issues'].append(f"Pages: {pages_msg}")
    elif verbose:
        log(f"  Pages: {pages_msg}", "DEBUG")
    
    # 3. Test réponse LLM (optionnel)
    if not skip_llm and routing_ok and pages_ok:
        try:
            ask_result = ask(
                question=test['question'],
                rag_dir=rag_dir,
                doc_id=test['expected_doc'],
                debug=verbose,
            )
            
            if ask_result['response']:
                result['response'] = ask_result['response']
                response_ok, response_issues = check_response(ask_result['response'], test)
                result['response_ok'] = response_ok
                result['issues'].extend(response_issues)
            else:
                result['issues'].append("Pas de réponse LLM")
        except Exception as e:
            result['issues'].append(f"Erreur LLM: {str(e)}")
    
    return result


def run_all_tests(
    rag_dir: Path,
    verbose: bool = False,
    skip_llm: bool = False,
    doc_filter: str = None
) -> Dict:
    """Exécute tous les tests."""
    results = []
    
    tests = DURAS_TESTS
    if doc_filter:
        tests = [t for t in tests if t['expected_doc'] == doc_filter]
    
    log(f"Exécution de {len(tests)} tests...")
    log("=" * 60)
    
    for i, test in enumerate(tests, 1):
        log(f"[{i}/{len(tests)}] {test['id']}")
        
        result = run_test(test, rag_dir, verbose, skip_llm)
        results.append(result)
        
        # Afficher statut
        status_parts = []
        status_parts.append("R" if result['routing_ok'] else "r")
        status_parts.append("P" if result['pages_ok'] else "p")
        status_parts.append("L" if result['response_ok'] else "l")
        status = "".join(status_parts)
        
        if result['issues']:
            log(f"  [{status}] FAIL: {result['issues'][0]}", "FAIL")
        else:
            log(f"  [{status}] PASS", "PASS")
    
    log("=" * 60)
    
    # Stats
    routing_ok = sum(1 for r in results if r['routing_ok'])
    pages_ok = sum(1 for r in results if r['pages_ok'])
    response_ok = sum(1 for r in results if r['response_ok'])
    all_ok = sum(1 for r in results if r['routing_ok'] and r['pages_ok'] and r['response_ok'])
    
    summary = {
        'total': len(results),
        'routing_ok': routing_ok,
        'pages_ok': pages_ok,
        'response_ok': response_ok,
        'all_ok': all_ok,
        'results': results,
    }
    
    log(f"RÉSULTATS:")
    log(f"  Routing:  {routing_ok}/{len(results)}")
    log(f"  Pages:    {pages_ok}/{len(results)}")
    log(f"  Réponse:  {response_ok}/{len(results)}")
    log(f"  TOTAL:    {all_ok}/{len(results)} ({100*all_ok/len(results):.0f}%)")
    
    return summary


# ============================================================================
# QUICK TESTS (sans LLM)
# ============================================================================

def run_quick_tests(rag_dir: Path, verbose: bool = False) -> Dict:
    """Tests rapides sans appel LLM (routing + pages seulement)."""
    log("Mode QUICK: tests routing et pages uniquement (pas de LLM)")
    return run_all_tests(rag_dir, verbose, skip_llm=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tests smoke sur Côtes de Duras"
    )
    parser.add_argument(
        '--dir', dest='rag_dir', default=None,
        help="Dossier rag_out"
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help="Mode verbeux"
    )
    parser.add_argument(
        '--quick', '-q', action='store_true',
        help="Tests rapides (sans LLM)"
    )
    parser.add_argument(
        '--doc', dest='doc_filter', default=None,
        help="Filtrer sur un doc_id"
    )
    parser.add_argument(
        '--save', dest='save_file', default=None,
        help="Sauvegarder les résultats en JSON"
    )
    args = parser.parse_args()
    
    rag_dir = Path(args.rag_dir).resolve() if args.rag_dir else RAG_DIR
    
    log(f"RAG dir: {rag_dir}")
    
    if not rag_dir.exists():
        log(f"ERREUR: dossier n'existe pas", "ERROR")
        sys.exit(1)
    
    # Exécuter les tests
    if args.quick:
        summary = run_quick_tests(rag_dir, args.verbose)
    else:
        summary = run_all_tests(
            rag_dir,
            verbose=args.verbose,
            skip_llm=False,
            doc_filter=args.doc_filter
        )
    
    # Sauvegarder si demandé
    if args.save_file:
        with open(args.save_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log(f"Résultats sauvegardés: {args.save_file}")
    
    # Code de sortie
    if summary['all_ok'] == summary['total']:
        log("SUCCESS: Tous les tests passent!", "SUCCESS")
        sys.exit(0)
    else:
        log(f"ÉCHEC: {summary['total'] - summary['all_ok']} tests en erreur", "FAIL")
        sys.exit(1)


if __name__ == '__main__':
    main()

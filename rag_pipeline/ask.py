#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE 4 — Script d'interrogation avec routing pages + fallback.

Usage:
    py -u ask.py "Quelle est la densité de plantation en Côtes de Duras ?"
    py -u ask.py "densité Duras" --doc 2-cdc-aopcotes-de-duras-v20241203
    py -u ask.py "charge maximale Duras" --debug

Pipeline:
    1. Doc routing: via --doc ou appellation_index.json
    2. Page routing: score des pages avec tokens significatifs
    3. Sélection top 3 pages candidates
    4. Construction CONTEXTE = texte pages
    5. Appel LLM local (Ollama)
    6. Auto-évaluation réponse + fallback
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

ENCODING = 'utf-8'
RAG_DIR = Path(__file__).parent / 'rag_out'

# LLM Configuration
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'mistral:7b')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434/api/generate')

# Prompts
SYSTEM_PROMPT = """Tu es un assistant réglementaire vitivinicole expert. Tu réponds UNIQUEMENT à partir des extraits (contexte) fournis.

RÈGLES ANTI-HALLUCINATION (INVIOLABLES):
1. Tu n'utilises QUE les extraits fournis. INTERDICTION d'ajouter du savoir externe.
2. Si l'information demandée n'est PAS dans les extraits: réponds exactement "Je ne sais pas à partir des extraits fournis." puis propose 5 mots-clés de recherche.
3. Tu termines TOUJOURS par: "Sources: page X, Y" (les numéros de pages utilisées).
4. INTERDICTION de mélanger plusieurs appellations ou documents.
5. Contrôle d'unités:
   - Densité de plantation => tu attends "pieds/ha" et/ou distances (m, mètres).
   - Charge parcelle => tu attends "kg/ha" ou "kilogrammes par hectare".
   - Rendement => tu attends "hl/ha" ou "hectolitres par hectare".
   - Si tu ne vois que des "%" pour densité => dis "Je ne sais pas..." (c'est probablement TAV).

FORMAT DE RÉPONSE:
**Réponse:** [ta réponse courte et précise]

**Détails:** [si besoin, développement]

**Sources:** page X, Y"""

USER_PROMPT_TEMPLATE = """QUESTION: {question}

CONTEXTE (extraits du document "{doc_id}"):
{context}

Réponds en respectant strictement les règles."""

# Tokens métier pour scoring pages
METIER_TOKENS = {
    'densite': ['densité', 'plantation', 'pieds', 'hectare', 'inter-rang', 'ecartement', 'metre'],
    'charge': ['charge', 'maximale', 'parcelle', 'kilogramme', 'kg'],
    'rendement': ['rendement', 'hectolitre', 'butoir', 'hl'],
    'richesse': ['richesse', 'sucre', 'gramme', 'litre', 'mout'],
    'recolte': ['recolte', 'vendange', 'maturite'],
    'cepage': ['cepage', 'encepagement', 'variete'],
}

# Tokens boilerplate (pénalité)
BOILERPLATE_TOKENS = {'inao', 'tsa', 'montreuil', 'cedex', 'adresse', 'secretariat'}

# Validation réponse
UNIT_CHECKS = {
    'densite': {'expected': ['pieds', 'hectare', 'metre', 'rang'], 'forbidden_alone': ['%']},
    'charge': {'expected': ['kg', 'kilogramme', 'hectare'], 'forbidden_alone': ['hl', 'hectolitre']},
    'rendement': {'expected': ['hl', 'hectolitre', 'hectare'], 'forbidden_alone': ['kg', 'kilogramme']},
}


# ============================================================================
# HELPERS
# ============================================================================

def log(msg: str, level: str = "INFO", debug: bool = False) -> None:
    if level == "DEBUG" and not debug:
        return
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", file=sys.stderr)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize('NFKD', text.lower())
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text


def tokenize(text: str) -> List[str]:
    raw = re.findall(r"[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9'-]*", text)
    return [normalize_text(t) for t in raw if len(t) > 2]


# ============================================================================
# ROUTING & SCORING
# ============================================================================

def load_appellation_index(rag_dir: Path) -> Dict:
    index_file = rag_dir / 'appellation_index.json'
    if not index_file.exists():
        return {}
    with open(index_file, 'r', encoding=ENCODING) as f:
        return json.load(f)


def resolve_doc_ids(question: str, app_index: Dict) -> List[str]:
    """Résout les doc_ids candidats pour une question."""
    question_norm = normalize_text(question)
    scores = Counter()
    
    for appellation, doc_ids in app_index.get('appellations', {}).items():
        app_norm = normalize_text(appellation)
        
        # Match exact
        if app_norm in question_norm:
            for doc_id in doc_ids:
                scores[doc_id] += 10
        
        # Match partiel
        app_words = set(app_norm.split())
        question_words = set(question_norm.split())
        common = app_words & question_words
        if common:
            for doc_id in doc_ids:
                scores[doc_id] += len(common) * 3
    
    return [doc_id for doc_id, _ in scores.most_common(3)]


def load_tokens_index(rag_dir: Path, doc_id: str) -> Dict:
    index_file = rag_dir / 'docs' / doc_id / 'tokens_index.json'
    if not index_file.exists():
        return {}
    with open(index_file, 'r', encoding=ENCODING) as f:
        return json.load(f)


def detect_question_type(question: str) -> str:
    """Détecte le type de question pour validation."""
    q_norm = normalize_text(question)
    
    if any(w in q_norm for w in ['densite', 'plantation', 'pieds', 'inter-rang', 'ecartement']):
        return 'densite'
    if any(w in q_norm for w in ['charge', 'parcelle', 'kg']):
        return 'charge'
    if any(w in q_norm for w in ['rendement', 'butoir', 'hectolitre']):
        return 'rendement'
    
    return 'general'


def score_pages(question: str, tokens_index: Dict, debug: bool = False) -> List[Tuple[int, float]]:
    """
    Score les pages du document pour la question.
    Retourne [(page, score), ...] triés par score décroissant.
    """
    q_tokens = set(tokenize(question))
    page_scores: Counter = Counter()
    
    index = tokens_index.get('index', {})
    
    # Déterminer les tokens pertinents pour la question
    relevant_tokens = set()
    q_type = detect_question_type(question)
    if q_type in METIER_TOKENS:
        relevant_tokens.update(METIER_TOKENS[q_type])
    relevant_tokens.update(q_tokens)
    
    for token in relevant_tokens:
        token_norm = normalize_text(token)
        if token_norm in index:
            for entry in index[token_norm]:
                page = entry['page']
                count = entry['count']
                score = entry.get('score', 1.0)
                
                # Bonus si token dans la question
                multiplier = 2.0 if token_norm in q_tokens else 1.0
                
                # Pénalité boilerplate
                if token_norm in BOILERPLATE_TOKENS:
                    multiplier *= 0.2
                
                page_scores[page] += count * score * multiplier
    
    # Trier par score
    sorted_pages = page_scores.most_common(10)
    
    if debug:
        log(f"Page scores: {sorted_pages[:5]}", "DEBUG", debug)
    
    return sorted_pages


def load_page_text(rag_dir: Path, doc_id: str, page_num: int) -> str:
    """Charge le texte d'une page."""
    pages_file = rag_dir / 'docs' / doc_id / 'pages.jsonl'
    if not pages_file.exists():
        return ""
    
    with open(pages_file, 'r', encoding=ENCODING) as f:
        for line in f:
            data = json.loads(line)
            if data.get('page') == page_num:
                return data.get('text', '')
    return ""


def build_context(rag_dir: Path, doc_id: str, pages: List[int], max_chars: int = 4000) -> str:
    """Construit le contexte à partir des pages sélectionnées."""
    context_parts = []
    total_chars = 0
    
    for page_num in pages:
        text = load_page_text(rag_dir, doc_id, page_num)
        if not text:
            continue
        
        # Limiter la taille
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        
        if len(text) > remaining:
            text = text[:remaining] + "..."
        
        context_parts.append(f"[PAGE {page_num}]\n{text}")
        total_chars += len(text)
    
    return "\n\n".join(context_parts)


# ============================================================================
# LLM INTERFACE
# ============================================================================

def call_ollama(prompt: str, system: str, model: str = OLLAMA_MODEL, debug: bool = False) -> str:
    """Appelle Ollama via subprocess."""
    try:
        import requests
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500,
            }
        }
        
        if debug:
            log(f"Appel Ollama: {model}", "DEBUG", debug)
        
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', '')
        
    except ImportError:
        # Fallback subprocess
        log("requests non disponible, utilisation subprocess", "WARN")
        return call_ollama_subprocess(prompt, system, model, debug)
    except Exception as e:
        log(f"Erreur Ollama: {e}", "ERROR")
        return ""


def call_ollama_subprocess(prompt: str, system: str, model: str, debug: bool = False) -> str:
    """Fallback via subprocess ollama run."""
    try:
        full_prompt = f"{system}\n\n{prompt}"
        
        result = subprocess.run(
            ['ollama', 'run', model],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8'
        )
        
        return result.stdout.strip()
    except Exception as e:
        log(f"Erreur subprocess: {e}", "ERROR")
        return ""


# ============================================================================
# VALIDATION
# ============================================================================

def validate_response(response: str, question: str, debug: bool = False) -> Tuple[bool, str]:
    """
    Valide la réponse du LLM.
    Retourne (is_valid, reason).
    """
    response_lower = response.lower()
    
    # Doit contenir "Sources:" ou "page"
    has_sources = 'sources:' in response_lower or 'page' in response_lower
    if not has_sources:
        return False, "Pas de citation de sources"
    
    # Vérifier le type de question
    q_type = detect_question_type(question)
    
    if q_type in UNIT_CHECKS:
        checks = UNIT_CHECKS[q_type]
        expected = checks['expected']
        forbidden = checks.get('forbidden_alone', [])
        
        # Vérifier présence d'unités attendues
        has_expected = any(u in response_lower for u in expected)
        has_forbidden = any(u in response_lower for u in forbidden)
        
        # Si on a des unités interdites SANS les unités attendues
        if has_forbidden and not has_expected:
            return False, f"Unités incorrectes pour {q_type} (attendu: {expected})"
    
    # Vérifier boilerplate non sollicité
    q_lower = question.lower()
    if not any(w in q_lower for w in ['controle', 'inao', 'organisme']):
        if 'montreuil' in response_lower or 'tsa 30003' in response_lower:
            return False, "Réponse boilerplate non pertinente"
    
    return True, "OK"


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def ask(
    question: str,
    rag_dir: Path = RAG_DIR,
    doc_id: Optional[str] = None,
    debug: bool = False,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Pipeline RAG complet.
    """
    result = {
        'question': question,
        'doc_id': None,
        'pages_tried': [],
        'response': None,
        'valid': False,
        'validation_reason': None,
    }
    
    # 1. Doc routing
    if doc_id:
        doc_ids = [doc_id]
        log(f"Doc forcé: {doc_id}", "DEBUG", debug)
    else:
        app_index = load_appellation_index(rag_dir)
        doc_ids = resolve_doc_ids(question, app_index)
        log(f"Doc routing: {doc_ids}", "DEBUG", debug)
    
    if not doc_ids:
        result['response'] = "Je ne sais pas quel document consulter. Précise l'appellation."
        return result
    
    # Utiliser le premier doc_id
    selected_doc_id = doc_ids[0]
    result['doc_id'] = selected_doc_id
    log(f"Doc sélectionné: {selected_doc_id}", "INFO")
    
    # 2. Page routing
    tokens_index = load_tokens_index(rag_dir, selected_doc_id)
    if not tokens_index:
        result['response'] = f"Index non trouvé pour {selected_doc_id}"
        return result
    
    page_scores = score_pages(question, tokens_index, debug)
    if not page_scores:
        result['response'] = "Aucune page pertinente trouvée."
        return result
    
    top_pages = [p for p, s in page_scores[:5]]
    log(f"Pages candidates: {top_pages}", "INFO")
    
    # 3. Fallback loop: essayer les pages une par une si invalide
    for attempt in range(min(max_retries, len(top_pages))):
        # Sélectionner les pages pour cette tentative
        if attempt == 0:
            pages_to_use = top_pages[:2]  # Top 2 pages
        else:
            # Essayer la page suivante
            pages_to_use = [top_pages[attempt]]
        
        result['pages_tried'].append(pages_to_use)
        log(f"Tentative {attempt + 1}: pages {pages_to_use}", "DEBUG", debug)
        
        # 4. Construire contexte
        context = build_context(rag_dir, selected_doc_id, pages_to_use)
        if not context:
            continue
        
        # 5. Appel LLM
        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            doc_id=selected_doc_id,
            context=context
        )
        
        response = call_ollama(user_prompt, SYSTEM_PROMPT, debug=debug)
        
        if not response:
            log(f"Pas de réponse LLM, tentative {attempt + 1}", "WARN")
            continue
        
        # 6. Validation
        is_valid, reason = validate_response(response, question, debug)
        
        if is_valid:
            result['response'] = response
            result['valid'] = True
            result['validation_reason'] = reason
            log(f"Réponse validée à la tentative {attempt + 1}", "INFO")
            return result
        else:
            log(f"Réponse invalide ({reason}), retry...", "DEBUG", debug)
    
    # Échec après tous les retries
    result['response'] = "Je ne sais pas à partir des extraits fournis.\n\nMots-clés suggérés: " + ", ".join(tokenize(question)[:5])
    result['valid'] = False
    result['validation_reason'] = "Toutes les tentatives ont échoué"
    
    return result


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Interrogation RAG avec routing pages et fallback"
    )
    parser.add_argument(
        'question',
        help="Question à poser"
    )
    parser.add_argument(
        '--doc', dest='doc_id', default=None,
        help="Forcer un doc_id spécifique"
    )
    parser.add_argument(
        '--dir', dest='rag_dir', default=None,
        help="Dossier rag_out (défaut: ./rag_out)"
    )
    parser.add_argument(
        '--debug', action='store_true',
        help="Mode debug verbeux"
    )
    parser.add_argument(
        '--model', dest='model', default=OLLAMA_MODEL,
        help=f"Modèle Ollama (défaut: {OLLAMA_MODEL})"
    )
    args = parser.parse_args()
    
    rag_dir = Path(args.rag_dir).resolve() if args.rag_dir else RAG_DIR
    
    if args.debug:
        log(f"Question: {args.question}")
        log(f"RAG dir: {rag_dir}")
        log(f"Model: {args.model}")
    
    # Exécuter le pipeline
    result = ask(
        question=args.question,
        rag_dir=rag_dir,
        doc_id=args.doc_id,
        debug=args.debug,
    )
    
    # Afficher le résultat
    print("\n" + "=" * 60)
    print(f"DOC: {result['doc_id']}")
    print(f"PAGES: {result['pages_tried']}")
    print(f"VALID: {result['valid']} ({result['validation_reason']})")
    print("=" * 60)
    print("\nRÉPONSE:\n")
    print(result['response'])
    print()


if __name__ == '__main__':
    main()

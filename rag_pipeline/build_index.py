#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE 2 — Index "tokens significatifs → pages" pour chaque document.

Usage:
    py -u build_index.py                          # utilise ./rag_out
    py -u build_index.py --dir ./rag_out
    py -u build_index.py --force                  # rebuild complet

Produit:
    rag_out/docs/<doc_id>/tokens_index.json
    rag_out/global_df.json  (document frequency globale)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

ENCODING = 'utf-8'

# Stopwords français (mots très fréquents à ignorer)
STOPWORDS_FR = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'est', 'en', 'au', 'aux',
    'ce', 'ces', 'cette', 'que', 'qui', 'dans', 'pour', 'par', 'sur', 'avec', 'sans',
    'son', 'sa', 'ses', 'leur', 'leurs', 'mais', 'ou', 'donc', 'ni', 'car', 'pas',
    'ne', 'plus', 'moins', 'tout', 'tous', 'toute', 'toutes', 'autre', 'autres',
    'etre', 'avoir', 'faire', 'peut', 'sont', 'ont', 'fait', 'elle', 'il', 'ils',
    'elles', 'nous', 'vous', 'je', 'tu', 'on', 'si', 'comme', 'dont', 'aussi',
    'bien', 'entre', 'apres', 'avant', 'sous', 'chez', 'vers', 'depuis', 'lors',
    'ainsi', 'cela', 'celui', 'celle', 'ceux', 'celles', 'meme', 'peu', 'tres',
    'tant', 'tel', 'telle', 'tels', 'telles', 'quelque', 'quelques', 'chaque',
    'page', 'article', 'alinea', 'paragraphe', 'chapitre', 'section', 'point',
}

# Tokens métier viticoles (haute priorité)
METIER_TOKENS = {
    # Densité / plantation
    'densite', 'plantation', 'pieds', 'hectare', 'inter-rang', 'interrang',
    'ecartement', 'superficie', 'metre', 'rang', 'cep', 'ceps',
    # Rendement
    'rendement', 'hectolitre', 'hectolitres', 'butoir',
    # Charge
    'charge', 'maximale', 'kilogramme', 'kilogrammes', 'parcelle',
    # Vinification
    'vinification', 'fermentation', 'elevage', 'pressurage', 'maceration',
    'sulfitage', 'so2', 'levurage', 'assemblage', 'cuvaison',
    # Cépages
    'cepage', 'cepages', 'merlot', 'cabernet', 'sauvignon', 'semillon',
    'muscadelle', 'malbec', 'tannat', 'fer', 'servadou', 'syrah',
    'grenache', 'mourvedre', 'carignan', 'cinsault', 'chardonnay',
    'chenin', 'pinot', 'gamay', 'riesling', 'gewurztraminer',
    # Sucre / alcool
    'sucre', 'sucres', 'richesse', 'mout', 'mouts', 'titre', 'alcoometrique',
    'volumique', 'naturel', 'acquis', 'grammes', 'litre',
    # Couleur / type
    'rouge', 'rouges', 'blanc', 'blancs', 'rose', 'roses', 'sec', 'secs',
    'moelleux', 'liquoreux', 'doux', 'effervescent', 'petillant',
    # Récolte
    'recolte', 'vendange', 'vendanges', 'maturite', 'trie', 'tries',
    'mecanique', 'manuelle',
    # Aire / zone
    'aire', 'geographique', 'commune', 'communes', 'parcellaire', 'delimitation',
    # Contrôle
    'organisme', 'controle', 'inao', 'agrement', 'declaration',
}

# Tokens boilerplate (à pénaliser)
BOILERPLATE_TOKENS = {
    'inao', 'tsa', 'montreuil', 'cedex', 'adresse', 'telephone', 'fax',
    'courriel', 'email', 'mel', 'secretariat', 'direction', 'service',
    'institut', 'national', 'origine', 'qualite',
}


# ============================================================================
# HELPERS
# ============================================================================

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def normalize_token(text: str) -> str:
    """Normalise un token (minuscules, sans accents)."""
    text = unicodedata.normalize('NFKD', text.lower())
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text


def tokenize(text: str) -> List[str]:
    """
    Tokenise un texte français.
    Retourne les tokens normalisés, filtrés.
    """
    # Extraire les mots (lettres, chiffres, tirets internes)
    raw_tokens = re.findall(r"[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9'-]*[a-zA-ZÀ-ÿ0-9]|[a-zA-ZÀ-ÿ]", text)
    
    tokens = []
    for t in raw_tokens:
        norm = normalize_token(t)
        # Filtrer tokens trop courts ou stopwords
        if len(norm) < 3:
            continue
        if norm in STOPWORDS_FR:
            continue
        tokens.append(norm)
    
    return tokens


def is_significant_token(token: str, doc_freq: Dict[str, int], total_docs: int) -> Tuple[bool, float]:
    """
    Détermine si un token est significatif et retourne son score.
    Score élevé = token rare ou métier.
    """
    # Tokens métier = toujours significatifs, score élevé
    if token in METIER_TOKENS:
        return True, 10.0
    
    # Tokens boilerplate = score négatif (pénalité)
    if token in BOILERPLATE_TOKENS:
        return True, -5.0
    
    # Tokens rares (DF faible) = significatifs
    df = doc_freq.get(token, 0)
    if df == 0:
        return False, 0.0
    
    # IDF-like score: plus le token est rare, plus il est significatif
    # On considère significatif si présent dans moins de 50% des docs
    doc_ratio = df / total_docs if total_docs > 0 else 1.0
    
    if doc_ratio < 0.1:  # Très rare (< 10% docs)
        return True, 5.0
    elif doc_ratio < 0.3:  # Rare (< 30% docs)
        return True, 3.0
    elif doc_ratio < 0.5:  # Moyennement fréquent
        return True, 1.0
    else:
        return False, 0.0


# ============================================================================
# PROCESSING
# ============================================================================

def compute_global_df(rag_out_dir: Path) -> Dict[str, int]:
    """
    Calcule la document frequency globale (combien de docs contiennent chaque token).
    """
    doc_tokens: Dict[str, Set[str]] = {}
    
    docs_dir = rag_out_dir / 'docs'
    if not docs_dir.exists():
        return {}
    
    for doc_dir in docs_dir.iterdir():
        if not doc_dir.is_dir():
            continue
        
        pages_file = doc_dir / 'pages.jsonl'
        if not pages_file.exists():
            continue
        
        doc_id = doc_dir.name
        unique_tokens: Set[str] = set()
        
        with open(pages_file, 'r', encoding=ENCODING) as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                text = data.get('text', '')
                tokens = tokenize(text)
                unique_tokens.update(tokens)
        
        doc_tokens[doc_id] = unique_tokens
    
    # Compter dans combien de docs chaque token apparaît
    df: Dict[str, int] = Counter()
    for tokens in doc_tokens.values():
        for token in tokens:
            df[token] += 1
    
    return dict(df)


def build_token_index(
    doc_dir: Path,
    global_df: Dict[str, int],
    total_docs: int,
    force: bool = False
) -> Dict[str, Any]:
    """
    Construit l'index token → pages pour un document.
    """
    doc_id = doc_dir.name
    pages_file = doc_dir / 'pages.jsonl'
    index_file = doc_dir / 'tokens_index.json'
    
    if not pages_file.exists():
        return {'doc_id': doc_id, 'status': 'SKIP', 'reason': 'no pages.jsonl'}
    
    # Vérifier si déjà traité
    if not force and index_file.exists():
        log(f"SKIP {doc_id} (index existe)", "SKIP")
        return {'doc_id': doc_id, 'status': 'SKIP', 'reason': 'already exists'}
    
    log(f"Indexation: {doc_id}")
    
    # Lire les pages et construire l'index
    token_pages: Dict[str, List[Dict]] = defaultdict(list)
    page_token_counts: Dict[int, Counter] = {}
    
    with open(pages_file, 'r', encoding=ENCODING) as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            page_num = data.get('page', 0)
            text = data.get('text', '')
            
            tokens = tokenize(text)
            counts = Counter(tokens)
            page_token_counts[page_num] = counts
    
    # Construire l'index inversé (token -> pages)
    for page_num, counts in page_token_counts.items():
        for token, count in counts.items():
            is_sig, score = is_significant_token(token, global_df, total_docs)
            if is_sig or count >= 3:  # Garder si significatif OU fréquent sur la page
                token_pages[token].append({
                    'page': page_num,
                    'count': count,
                    'score': round(score, 2),
                })
    
    # Trier les pages par count décroissant pour chaque token
    for token in token_pages:
        token_pages[token].sort(key=lambda x: (-x['score'], -x['count']))
    
    # Filtrer pour garder une taille raisonnable
    # Garder max 20 pages par token, priorité aux tokens métier
    filtered_index = {}
    for token, pages in token_pages.items():
        # Garder plus de pages pour tokens métier
        max_pages = 20 if token in METIER_TOKENS else 10
        filtered_index[token] = pages[:max_pages]
    
    # Écrire l'index
    index_data = {
        'doc_id': doc_id,
        'generated_at': datetime.now().isoformat(),
        'total_tokens': len(filtered_index),
        'metier_tokens': [t for t in filtered_index if t in METIER_TOKENS],
        'boilerplate_tokens': [t for t in filtered_index if t in BOILERPLATE_TOKENS],
        'index': filtered_index,
    }
    
    with open(index_file, 'w', encoding=ENCODING) as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    log(f"  -> {len(filtered_index)} tokens indexés, {len(index_data['metier_tokens'])} métier")
    
    return {
        'doc_id': doc_id,
        'status': 'OK',
        'tokens': len(filtered_index),
        'metier': len(index_data['metier_tokens']),
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Construction des index tokens → pages"
    )
    parser.add_argument(
        '--dir', dest='rag_dir', default='./rag_out',
        help="Dossier rag_out (défaut: ./rag_out)"
    )
    parser.add_argument(
        '--force', action='store_true',
        help="Forcer le rebuild même si index existe"
    )
    args = parser.parse_args()
    
    rag_dir = Path(args.rag_dir).resolve()
    
    log(f"RAG dir: {rag_dir}")
    log(f"Force:   {args.force}")
    
    if not rag_dir.exists():
        log(f"ERREUR: dossier n'existe pas: {rag_dir}", "ERROR")
        sys.exit(1)
    
    docs_dir = rag_dir / 'docs'
    if not docs_dir.exists():
        log(f"ERREUR: dossier docs/ n'existe pas", "ERROR")
        sys.exit(1)
    
    # Étape 1: Calculer la document frequency globale
    log("Calcul de la document frequency globale...")
    global_df = compute_global_df(rag_dir)
    total_docs = len(list(docs_dir.iterdir()))
    
    log(f"  -> {len(global_df)} tokens uniques sur {total_docs} docs")
    
    # Sauvegarder la DF globale
    df_file = rag_dir / 'global_df.json'
    with open(df_file, 'w', encoding=ENCODING) as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_docs': total_docs,
            'total_tokens': len(global_df),
            'df': global_df,
        }, f, ensure_ascii=False)
    log(f"  -> global_df.json écrit")
    
    log("=" * 60)
    
    # Étape 2: Construire l'index pour chaque doc
    results = []
    for doc_dir in sorted(docs_dir.iterdir()):
        if not doc_dir.is_dir():
            continue
        result = build_token_index(doc_dir, global_df, total_docs, force=args.force)
        results.append(result)
    
    log("=" * 60)
    
    # Stats finales
    ok_count = sum(1 for r in results if r.get('status') == 'OK')
    skip_count = sum(1 for r in results if r.get('status') == 'SKIP')
    
    log(f"Terminé: {ok_count} indexés, {skip_count} skippés")


if __name__ == '__main__':
    main()

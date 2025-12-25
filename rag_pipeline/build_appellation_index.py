#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE 3 — Index "appellation → doc_id" pour routing document.

Usage:
    py -u build_appellation_index.py                    # utilise ./rag_out
    py -u build_appellation_index.py --dir ./rag_out

Produit:
    rag_out/appellation_index.json

Méthode:
    1. Parse les noms de fichiers pour extraire l'appellation
    2. Applique des heuristiques (retirer cdc, aop, igp, dates)
    3. Permet des overrides manuels via appellation_overrides.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# ============================================================================
# CONFIGURATION
# ============================================================================

ENCODING = 'utf-8'

# Mots à retirer des noms pour extraire l'appellation
REMOVE_PATTERNS = [
    r'\bcdc\b',           # cahier des charges
    r'\baop\b',           # appellation origine protégée
    r'\baoc\b',           # appellation origine contrôlée
    r'\bigp\b',           # indication géographique protégée
    r'\bpno\b',           # projet national opposition
    r'\bagrt\d+[a-z]?\b', # codes AGRT
    r'\bmodif\b',
    r'\bvdef\b',
    r'\bvprov\b',
    r'\bcn\d+\b',         # codes CN
    r'\b\d{6,}\b',        # dates longues (YYYYMMDD)
    r'\b20\d{2}\b',       # années 20XX
    r'\bv\d+\b',          # versions vXXX
    r'\b\d{1,2}\b',       # numéros seuls
]

# Aliases connus pour normalisation
APPELLATION_ALIASES = {
    'cotes de duras': ['duras', 'cotes-de-duras', 'cotes de duras'],
    'cotes du rhone': ['rhone', 'cotes-du-rhone', 'cotes du rhone'],
    'cotes de provence': ['provence', 'cotes-de-provence'],
    'bordeaux': ['bordeaux'],
    'bordeaux superieur': ['bordeaux-superieur', 'bordeaux superieur'],
    'languedoc': ['languedoc'],
    'alsace': ['alsace'],
    'alsace grands crus': ['alsace-grands-crus', 'grands crus alsace'],
    'champagne': ['champagne'],
    'bourgogne': ['bourgogne'],
    'bourgogne aligote': ['bourgogne-aligote', 'aligote'],
    'savoie': ['savoie'],
    'anjou': ['anjou', 'cabernet anjou', 'rose anjou'],
    'corse': ['corse', 'vin corse'],
    'montlouis': ['montlouis', 'montlouis-sur-loire'],
    'pacherenc': ['pacherenc', 'vic-bilh', 'pacherenc du vic bilh'],
    'tursan': ['tursan'],
    'marmandais': ['marmandais', 'cotes du marmandais'],
    'clairette': ['clairette', 'clairette de die', 'clairette du languedoc'],
    'moselle': ['moselle'],
    'alpes maritimes': ['alpes-maritimes', 'alpes maritimes'],
}


# ============================================================================
# HELPERS
# ============================================================================

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def normalize_text(text: str) -> str:
    """Normalise un texte (minuscules, sans accents, espaces simples)."""
    text = unicodedata.normalize('NFKD', text.lower())
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_appellation_from_filename(filename: str) -> str:
    """
    Extrait l'appellation d'un nom de fichier PDF.
    Applique les heuristiques de nettoyage.
    """
    # Retirer extension
    name = os.path.splitext(filename)[0]
    
    # Normaliser
    name = normalize_text(name)
    
    # Appliquer les patterns de suppression
    for pattern in REMOVE_PATTERNS:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Nettoyer les espaces multiples
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def find_canonical_appellation(extracted: str) -> Optional[str]:
    """
    Trouve l'appellation canonique à partir du texte extrait.
    """
    extracted_norm = normalize_text(extracted)
    
    # Chercher dans les aliases
    for canonical, aliases in APPELLATION_ALIASES.items():
        # Match exact
        if extracted_norm == canonical:
            return canonical
        
        # Match partiel (l'appellation est contenue)
        for alias in aliases:
            if alias in extracted_norm or extracted_norm in alias:
                return canonical
    
    # Pas trouvé, retourner tel quel
    return extracted_norm if extracted_norm else None


def resolve_doc_id(question: str, appellation_index: Dict) -> List[str]:
    """
    Résout le(s) doc_id(s) pour une question utilisateur.
    Retourne une liste de doc_ids candidats (max 3).
    """
    question_norm = normalize_text(question)
    
    candidates = []
    scores = {}
    
    # Chercher les appellations mentionnées
    for appellation, doc_ids in appellation_index.get('appellations', {}).items():
        app_norm = normalize_text(appellation)
        
        # Match exact
        if app_norm in question_norm:
            for doc_id in doc_ids:
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += 10  # Bonus match exact
        
        # Match partiel (mots de l'appellation présents)
        app_words = set(app_norm.split())
        question_words = set(question_norm.split())
        common = app_words & question_words
        if len(common) >= 2 or (len(common) == 1 and len(app_words) == 1):
            for doc_id in doc_ids:
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += len(common) * 3
    
    # Trier par score décroissant
    sorted_docs = sorted(scores.items(), key=lambda x: -x[1])
    
    # Retourner max 3 candidats
    return [doc_id for doc_id, score in sorted_docs[:3] if score > 0]


# ============================================================================
# PROCESSING
# ============================================================================

def build_appellation_index(rag_dir: Path) -> Dict:
    """
    Construit l'index appellation → doc_id.
    """
    manifest_file = rag_dir / 'manifest.json'
    overrides_file = rag_dir / 'appellation_overrides.json'
    
    if not manifest_file.exists():
        log(f"ERREUR: manifest.json non trouvé", "ERROR")
        return {}
    
    with open(manifest_file, 'r', encoding=ENCODING) as f:
        manifest = json.load(f)
    
    # Charger les overrides si présents
    overrides = {}
    if overrides_file.exists():
        with open(overrides_file, 'r', encoding=ENCODING) as f:
            overrides = json.load(f)
        log(f"Chargé {len(overrides)} overrides")
    
    # Construire l'index
    appellations: Dict[str, List[str]] = {}
    doc_to_appellation: Dict[str, str] = {}
    
    for doc in manifest.get('docs', []):
        doc_id = doc.get('doc_id', '')
        source_file = doc.get('source_file', '')
        status = doc.get('status', '')
        
        if status != 'OK':
            continue
        
        # Override manuel ?
        if doc_id in overrides:
            appellation = overrides[doc_id]
            log(f"  Override: {doc_id} -> {appellation}")
        else:
            # Extraire de filename
            extracted = extract_appellation_from_filename(source_file)
            appellation = find_canonical_appellation(extracted)
            
            if not appellation:
                appellation = doc_id  # Fallback
                log(f"  Fallback: {doc_id} (pas d'appellation trouvée)", "WARN")
        
        # Enregistrer
        if appellation not in appellations:
            appellations[appellation] = []
        if doc_id not in appellations[appellation]:
            appellations[appellation].append(doc_id)
        
        doc_to_appellation[doc_id] = appellation
        log(f"  {doc_id} -> '{appellation}'")
    
    return {
        'generated_at': datetime.now().isoformat(),
        'total_appellations': len(appellations),
        'total_docs': len(doc_to_appellation),
        'appellations': appellations,
        'doc_to_appellation': doc_to_appellation,
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Construction de l'index appellation → doc_id"
    )
    parser.add_argument(
        '--dir', dest='rag_dir', default='./rag_out',
        help="Dossier rag_out (défaut: ./rag_out)"
    )
    args = parser.parse_args()
    
    rag_dir = Path(args.rag_dir).resolve()
    
    log(f"RAG dir: {rag_dir}")
    
    if not rag_dir.exists():
        log(f"ERREUR: dossier n'existe pas: {rag_dir}", "ERROR")
        sys.exit(1)
    
    log("Construction de l'index appellation...")
    log("=" * 60)
    
    index = build_appellation_index(rag_dir)
    
    log("=" * 60)
    
    # Écrire l'index
    index_file = rag_dir / 'appellation_index.json'
    with open(index_file, 'w', encoding=ENCODING) as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    log(f"Index écrit: {index_file}")
    log(f"Total: {index['total_appellations']} appellations, {index['total_docs']} docs")
    
    # Test rapide
    log("")
    log("Test de résolution:")
    test_questions = [
        "Quelle est la densité de plantation en Côtes de Duras ?",
        "Rendement Bourgogne",
        "cepage bordeaux",
    ]
    for q in test_questions:
        results = resolve_doc_id(q, index)
        log(f"  '{q[:50]}...' -> {results}")


if __name__ == '__main__':
    main()

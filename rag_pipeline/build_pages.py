#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ÉTAPE 1 — Extraction page par page des PDFs vers JSONL.

Usage:
    py -u build_pages.py                          # dossier courant -> ./rag_out
    py -u build_pages.py --in ./pdfs --out ./rag_out
    py -u build_pages.py --force                  # rebuild complet

Produit:
    rag_out/docs/<doc_id>/pages.jsonl   (1 ligne JSON = 1 page)
    rag_out/docs/<doc_id>/meta.json     (métadonnées doc)
    rag_out/manifest.json               (index global)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("[ERREUR] PyPDF2 requis. Installez: pip install PyPDF2")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

MIN_TEXT_LENGTH = 100  # Seuil pour détecter un scan (texte quasi vide)
ENCODING = 'utf-8'


# ============================================================================
# HELPERS
# ============================================================================

def log(msg: str, level: str = "INFO") -> None:
    """Log avec horodatage."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def slugify(text: str) -> str:
    """Convertit un nom de fichier en doc_id slug."""
    # Enlever extension
    text = os.path.splitext(text)[0]
    # Normaliser unicode
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Minuscules, remplacer espaces/underscores par tirets
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


def compute_sha256(filepath: Path) -> str:
    """Calcule le hash SHA256 d'un fichier."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extrait le texte de chaque page d'un PDF.
    Retourne une liste de dicts {page, text}.
    """
    pages = []
    try:
        reader = PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ''
            # Nettoyer le texte
            text = text.strip()
            pages.append({
                'page': i,
                'text': text,
            })
    except Exception as e:
        raise RuntimeError(f"Erreur extraction PDF: {e}")
    return pages


def is_scan_pdf(pages: List[Dict[str, Any]]) -> bool:
    """
    Détecte si le PDF est probablement un scan (peu de texte extrait).
    """
    total_text = sum(len(p['text']) for p in pages)
    avg_per_page = total_text / len(pages) if pages else 0
    return avg_per_page < MIN_TEXT_LENGTH


# ============================================================================
# PROCESSING
# ============================================================================

def process_pdf(
    pdf_path: Path,
    out_dir: Path,
    force: bool = False
) -> Dict[str, Any]:
    """
    Traite un PDF et produit pages.jsonl + meta.json.
    Retourne les infos pour le manifest.
    """
    source_file = pdf_path.name
    doc_id = slugify(source_file)
    sha256 = compute_sha256(pdf_path)
    
    # Dossier de sortie pour ce doc
    doc_out_dir = out_dir / 'docs' / doc_id
    pages_file = doc_out_dir / 'pages.jsonl'
    meta_file = doc_out_dir / 'meta.json'
    
    # Vérifier si déjà traité (idempotent)
    if not force and meta_file.exists():
        try:
            with open(meta_file, 'r', encoding=ENCODING) as f:
                existing_meta = json.load(f)
            if existing_meta.get('sha256') == sha256:
                log(f"SKIP {source_file} (déjà traité, même hash)", "SKIP")
                return existing_meta
        except Exception:
            pass  # Si erreur lecture, on retraite
    
    log(f"Traitement: {source_file} -> {doc_id}")
    
    # Extraction
    try:
        pages = extract_pages(pdf_path)
    except Exception as e:
        log(f"ERREUR extraction {source_file}: {e}", "ERROR")
        return {
            'doc_id': doc_id,
            'source_file': source_file,
            'sha256': sha256,
            'pages': 0,
            'status': 'FAIL',
            'error': str(e),
        }
    
    # Vérifier si scan
    if is_scan_pdf(pages):
        log(f"WARN {source_file}: texte quasi vide, scan probable", "WARN")
        status = 'FAIL'
        error = 'Texte quasi vide après extraction (scan image probable)'
    else:
        status = 'OK'
        error = None
    
    # Créer dossier sortie
    doc_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Écrire pages.jsonl
    with open(pages_file, 'w', encoding=ENCODING) as f:
        for p in pages:
            line = {
                'doc_id': doc_id,
                'source_file': source_file,
                'sha256': sha256,
                'page': p['page'],
                'text': p['text'],
            }
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
    
    # Écrire meta.json
    meta = {
        'doc_id': doc_id,
        'source_file': source_file,
        'sha256': sha256,
        'pages': len(pages),
        'status': status,
        'error': error,
        'processed_at': datetime.now().isoformat(),
    }
    with open(meta_file, 'w', encoding=ENCODING) as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    log(f"  -> {len(pages)} pages, status={status}")
    
    return meta


def build_manifest(results: List[Dict[str, Any]], out_dir: Path) -> None:
    """Produit le manifest.json global."""
    manifest = {
        'generated_at': datetime.now().isoformat(),
        'total_docs': len(results),
        'ok': sum(1 for r in results if r.get('status') == 'OK'),
        'fail': sum(1 for r in results if r.get('status') == 'FAIL'),
        'docs': results,
    }
    
    manifest_file = out_dir / 'manifest.json'
    with open(manifest_file, 'w', encoding=ENCODING) as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    log(f"Manifest écrit: {manifest_file}")
    log(f"Total: {manifest['total_docs']} docs, {manifest['ok']} OK, {manifest['fail']} FAIL")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extraction page par page des PDFs vers JSONL"
    )
    parser.add_argument(
        '--in', dest='input_dir', default='.',
        help="Dossier contenant les PDFs (défaut: .)"
    )
    parser.add_argument(
        '--out', dest='output_dir', default='./rag_out',
        help="Dossier de sortie (défaut: ./rag_out)"
    )
    parser.add_argument(
        '--force', action='store_true',
        help="Forcer le rebuild même si déjà traité"
    )
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    log(f"Input:  {input_dir}")
    log(f"Output: {output_dir}")
    log(f"Force:  {args.force}")
    
    # Vérifier dossier input
    if not input_dir.exists():
        log(f"ERREUR: dossier input n'existe pas: {input_dir}", "ERROR")
        sys.exit(1)
    
    # Créer dossier output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Lister les PDFs
    pdf_files = sorted(input_dir.glob('*.pdf'))
    if not pdf_files:
        log(f"Aucun PDF trouvé dans {input_dir}", "WARN")
        sys.exit(0)
    
    log(f"Trouvé {len(pdf_files)} PDFs à traiter")
    log("=" * 60)
    
    # Traiter chaque PDF
    results = []
    for pdf_path in pdf_files:
        try:
            meta = process_pdf(pdf_path, output_dir, force=args.force)
            results.append(meta)
        except Exception as e:
            log(f"ERREUR FATALE {pdf_path.name}: {e}", "ERROR")
            results.append({
                'doc_id': slugify(pdf_path.name),
                'source_file': pdf_path.name,
                'sha256': '',
                'pages': 0,
                'status': 'FAIL',
                'error': str(e),
            })
    
    log("=" * 60)
    
    # Générer manifest
    build_manifest(results, output_dir)
    
    log("Terminé!")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch RAG chunker for a folder of CDC PDFs.

✅ Defaults for "Run" buttons (Windsurf) / double-click:
  - input dir: current working directory (.)
  - output dir: ./rag_out

Usage:
  py -u cahier_des_charges.py
  py -u cahier_des_charges.py --in . --out .\\rag_out
  py -u cahier_des_charges.py --force
"""

import argparse
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyPDF2 import PdfReader


# -----------------------------
# Helpers
# -----------------------------

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9àâäçéèêëîïôöùûüÿñæœ\-_\s]", " ", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    return s[:80] if s else "doc"

def clean_text(s: str) -> str:
    s = s.replace("\r", "")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def approx_tokens(s: str) -> int:
    # Rough but OK for chunk sizing: ~4 chars/token
    return int(math.ceil(len(s) / 4))

def tokenize_for_find(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def safe_extract_page_text(page) -> str:
    try:
        return page.extract_text() or ""
    except Exception:
        return ""

# Headings heuristic: adjust if needed for your CDC layout
HEADING_RE = re.compile(
    r"(?m)^(Chapitre\s+[IVXLC]+.*|CHAPITRE\s+[IVXLC]+.*|"
    r"(?:Article|ARTICLE)\s+\d+.*|"
    r"\d+\s*[—-]\s*.*|"
    r"\d+(?:\.\d+){0,3}\s*[-–—]\s*.*)$"
)

def split_by_headings(text: str) -> List[str]:
    ms = list(HEADING_RE.finditer(text))
    if not ms:
        return [text.strip()] if text.strip() else []
    segs = []
    for i, m in enumerate(ms):
        start = m.start()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        seg = text[start:end].strip()
        if seg:
            segs.append(seg)
    return segs

def chunkify(segment: str, target_tokens: int = 450) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", segment) if p.strip()]
    chunks = []
    cur: List[str] = []
    cur_tok = 0

    for p in paras:
        t = approx_tokens(p) + 8
        if cur and cur_tok + t > target_tokens:
            chunks.append("\n\n".join(cur).strip())
            cur = [p]
            cur_tok = t
        else:
            cur.append(p)
            cur_tok += t

    if cur:
        chunks.append("\n\n".join(cur).strip())

    # Safety: if a chunk is still too big, split by sentences
    out: List[str] = []
    for c in chunks:
        if approx_tokens(c) <= int(target_tokens * 1.35):
            out.append(c)
            continue

        sents = re.split(r"(?<=[\.\!\?])\s+", c)
        cc: List[str] = []
        tok = 0
        for s in sents:
            if not s.strip():
                continue
            t = approx_tokens(s) + 3
            if cc and tok + t > target_tokens:
                out.append(" ".join(cc).strip())
                cc = [s]
                tok = t
            else:
                cc.append(s)
                tok += t
        if cc:
            out.append(" ".join(cc).strip())

    return [x for x in out if x]


def guess_page_for_chunk(chunk: str, page_texts: List[str]) -> Optional[int]:
    prefix = tokenize_for_find(chunk[:140])
    if prefix:
        for i, pt in enumerate(page_texts):
            if prefix in tokenize_for_find(pt):
                return i + 1

    words = re.findall(r"\w+", chunk)[:10]
    key = " ".join(words[:5]).strip()
    if key:
        for i, pt in enumerate(page_texts):
            if key in pt:
                return i + 1

    return None


# -----------------------------
# Core processing
# -----------------------------

@dataclass
class DocResult:
    doc_id: str
    source_file: str
    sha256: str
    pages: int
    chunks: int
    out_jsonl: str
    error: Optional[str] = None
    seconds: float = 0.0


def process_pdf(pdf_path: Path, out_dir: Path, target_tokens: int, force: bool) -> DocResult:
    t0 = time.time()
    source_file = pdf_path.name
    doc_id = slugify(pdf_path.stem)

    out_jsonl = out_dir / f"chunks_{doc_id}.jsonl"
    sha = sha256_file(pdf_path)

    if out_jsonl.exists() and not force:
        # Skip reprocessing (but keep hash so manifest stays useful)
        return DocResult(
            doc_id=doc_id,
            source_file=source_file,
            sha256=sha,
            pages=0,
            chunks=0,
            out_jsonl=str(out_jsonl),
            error=None,
            seconds=0.0,
        )

    try:
        reader = PdfReader(str(pdf_path))
        page_texts = [clean_text(safe_extract_page_text(p)) for p in reader.pages]
        pages = len(page_texts)

        full = clean_text("\n\n".join([t for t in page_texts if t]))

        if len(full) < 200:
            raise RuntimeError("Texte PDF quasi vide après extraction (scan image ?).")

        segments = split_by_headings(full)
        all_chunks: List[Dict] = []
        chunk_num = 0

        for seg in segments:
            first_line = seg.splitlines()[0].strip() if seg.splitlines() else "SECTION"
            section = first_line[:140] if first_line else "SECTION"

            for ch_text in chunkify(seg, target_tokens=target_tokens):
                chunk_num += 1
                page = guess_page_for_chunk(ch_text, page_texts)

                all_chunks.append({
                    "id": f"{doc_id.upper()}-{chunk_num:04d}",
                    "doc_id": doc_id,
                    "source_file": source_file,
                    "source_path": str(pdf_path),
                    "sha256": sha,
                    "page": page,
                    "section": section,
                    "tokens_approx": approx_tokens(ch_text),
                    "tags": ["cdc", "reglementaire"],
                    "text": ch_text,
                })

        with out_jsonl.open("w", encoding="utf-8") as f:
            for obj in all_chunks:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

        return DocResult(
            doc_id=doc_id,
            source_file=source_file,
            sha256=sha,
            pages=pages,
            chunks=len(all_chunks),
            out_jsonl=str(out_jsonl),
            error=None,
            seconds=time.time() - t0,
        )

    except Exception as e:
        return DocResult(
            doc_id=doc_id,
            source_file=source_file,
            sha256=sha,
            pages=0,
            chunks=0,
            out_jsonl=str(out_jsonl),
            error=str(e),
            seconds=time.time() - t0,
        )


def merge_jsonls(out_dir: Path, merged_name: str = "chunks_ALL.jsonl") -> Tuple[str, int]:
    merged_path = out_dir / merged_name
    count = 0
    with merged_path.open("w", encoding="utf-8") as out_f:
        for p in sorted(out_dir.glob("chunks_*.jsonl")):
            if p.name == merged_name:
                continue
            with p.open("r", encoding="utf-8") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line)
                        count += 1
    return str(merged_path), count


def main():
    ap = argparse.ArgumentParser()
    # ✅ MODIF: plus required, defaults added
    ap.add_argument("--in", dest="in_dir", default=".",
                    help="Dossier contenant les PDFs (CDC) [défaut: .]")
    ap.add_argument("--out", dest="out_dir", default="./rag_out",
                    help="Dossier de sortie (JSONL + manifest) [défaut: ./rag_out]")

    ap.add_argument("--target-tokens", type=int, default=450,
                    help="Taille cible d’un chunk (tokens approx)")
    ap.add_argument("--force", action="store_true",
                    help="Reprocess même si JSONL existe déjà")
    ap.add_argument("--max-pdfs", type=int, default=0,
                    help="Limiter le nb de PDFs (0 = tous)")
    args = ap.parse_args()

    in_dir = Path(args.in_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(in_dir.glob("*.pdf"))
    if args.max_pdfs and args.max_pdfs > 0:
        pdfs = pdfs[: args.max_pdfs]

    if not pdfs:
        print(f"Aucun PDF trouvé dans {in_dir}", file=sys.stderr)
        sys.exit(1)

    results: List[Dict] = []
    ok = 0
    fail = 0

    print(f"📄 PDFs trouvés: {len(pdfs)}")
    print(f"📥 IN : {in_dir}")
    print(f"📤 OUT: {out_dir}\n")

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] Processing: {pdf.name}")
        r = process_pdf(pdf, out_dir, target_tokens=args.target_tokens, force=args.force)
        results.append(r.__dict__)
        if r.error:
            fail += 1
            print(f"  ❌ ERROR: {r.error}")
        else:
            ok += 1
            # pages/chunks=0 when skipped: still OK
            extra = " (skipped)" if (r.pages == 0 and r.chunks == 0 and not args.force) else ""
            print(f"  ✅ chunks={r.chunks} pages={r.pages} time={r.seconds:.2f}s -> {Path(r.out_jsonl).name}{extra}")

    merged_path, merged_count = merge_jsonls(out_dir)

    manifest = {
        "input_dir": str(in_dir),
        "output_dir": str(out_dir),
        "target_tokens": args.target_tokens,
        "processed": len(pdfs),
        "ok": ok,
        "fail": fail,
        "merged_jsonl": merged_path,
        "merged_chunks": merged_count,
        "results": results,
        "notes": [
            "Si certains PDFs sont scannés (images), PyPDF2 peut extraire quasi rien.",
            "Dans ce cas: passer sur OCR (tesseract) ou un extracteur plus robuste (pdfminer + OCR)."
        ],
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n---")
    print(f"✅ OK: {ok} | ❌ FAIL: {fail}")
    print(f"📦 Merged JSONL: {merged_path} (chunks={merged_count})")
    print(f"🧾 Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import difflib
import json
import os
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple

from django.conf import settings

DOCS_PATH = os.path.join(os.path.dirname(__file__), 'knowledge')
MANIFEST_PATH = getattr(
    settings,
    'RAG_MANIFEST_PATH',
    os.path.join(os.path.dirname(__file__), '..', 'Cahier des charges', 'pdfs', 'rag_out', 'manifest.json')
)
MAX_CHARS_DEFAULT = 1500
BOILERPLATE_KEYWORDS = (
    'structure de contrôle',
    'structure de controle',
    'inao',
    'tsa 30003',
    'montreuil cedex',
    'organisme de contrôle',
    'organisme de controle',
)
QUERY_BOILERPLATE_WHITELIST = ('contrôle', 'controle', 'inao', 'organisme', 'audit')


@dataclass
class Chunk:
    doc_id: str
    uid: str
    header: str
    text: str
    tokens: List[str]
    term_freq: Dict[str, int]
    boilerplate: bool = False


def _normalize_text(text: str) -> str:
    if not text:
        return ''
    norm = unicodedata.normalize('NFKD', text)
    norm = norm.encode('ascii', 'ignore').decode('ascii').lower()
    norm = re.sub(r'[^a-z0-9]+', ' ', norm)
    return norm.strip()


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if len(t) > 2]


class ManifestRouter:
    """Map appellations to doc_ids using manifest + heuristics."""

    def __init__(self):
        self.raw_manifest = self._load_manifest()
        self.norm_index: Dict[str, str] = {}
        self.doc_aliases: Dict[str, str] = {}
        self._index_manifest()

    def _load_manifest(self):
        path = MANIFEST_PATH
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _index_manifest(self):
        results = self.raw_manifest.get('results') or []
        for entry in results:
            doc_id = entry.get('doc_id')
            if not doc_id:
                continue
            norm = _normalize_text(doc_id)
            self.norm_index[norm] = doc_id

    def doc_id_for_slug(self, slug: str) -> str | None:
        if not self.norm_index:
            return None
        norm = _normalize_text(slug)
        if norm in self.norm_index:
            return self.norm_index[norm]
        matches = difflib.get_close_matches(norm, list(self.norm_index.keys()), n=1, cutoff=0.75)
        if matches:
            return self.norm_index[matches[0]]
        return None


ROUTER_QUERY_HINTS = {
    'densite': [
        'densité', 'plantation', 'pieds par hectare', 'pieds/ha', 'inter-rang',
        'mètre', 'superficie par pied'
    ],
    'charge': [
        'charge maximale', 'kg/ha', 'kilogrammes par hectare', 'parcelle'
    ],
    'richesse': [
        'richesse en sucre', 'g/l', 'grammes par litre', 'moût'
    ],
    'rendement': [
        'rendement', 'hectolitres par hectare'
    ],
}


class SimpleRAG:
    def __init__(self):
        self.router = ManifestRouter()
        self.doc_chunks: Dict[str, List[Chunk]] = {}
        self.doc_aliases: Dict[str, str] = {}
        self.doc_alias_reverse: Dict[str, str] = {}
        self.last_debug: List[Dict[str, str]] = []
        self.chunks: List[Chunk] = []
        self.doc_freq: Counter = Counter()
        self.avgdl = 1.0
        self._load_docs()

    def _load_docs(self):
        if not os.path.exists(DOCS_PATH):
            return
        for root_dir, _, files in os.walk(DOCS_PATH):
            for filename in files:
                if not filename.endswith('.md'):
                    continue
                abs_path = os.path.join(root_dir, filename)
                rel_path = os.path.relpath(abs_path, DOCS_PATH)
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc_id = self._doc_id_for_path(rel_path)
                sections = self._split_sections(content)
                chunk_list = self._build_chunks(doc_id, sections)
                if chunk_list:
                    self.doc_chunks[doc_id] = chunk_list
                    self.chunks.extend(chunk_list)
                    self._register_aliases(doc_id, content)
        for chunk in self.chunks:
            unique_tokens = set(chunk.term_freq.keys())
            for token in unique_tokens:
                self.doc_freq[token] += 1
        self.avgdl = (
            sum(len(chunk.tokens) for chunk in self.chunks) / len(self.chunks)
            if self.chunks else 1.0
        )

    def _doc_id_for_path(self, rel_path: str) -> str:
        base = os.path.splitext(rel_path)[0].replace('\\', '/')
        candidate = self.router.doc_id_for_slug(base)
        return candidate or base

    def _split_sections(self, content: str) -> List[Tuple[str, List[str]]]:
        sections: List[Tuple[str, List[str]]] = []
        current_header = 'Introduction'
        current_lines: List[str] = []
        for line in content.splitlines():
            if line.startswith('## '):
                if current_lines:
                    sections.append((current_header, self._group_paragraphs(current_lines)))
                current_header = line[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines:
            sections.append((current_header, self._group_paragraphs(current_lines)))
        return sections

    def _group_paragraphs(self, lines: List[str]) -> List[str]:
        paragraphs: List[str] = []
        buffer: List[str] = []
        for line in lines:
            if not line.strip():
                if buffer:
                    paragraphs.append('\n'.join(buffer).strip())
                    buffer = []
                continue
            buffer.append(line.rstrip())
        if buffer:
            paragraphs.append('\n'.join(buffer).strip())
        return paragraphs

    def _build_chunks(self, doc_id: str, sections: List[Tuple[str, List[str]]]) -> List[Chunk]:
        chunks: List[Chunk] = []
        chunk_idx = 1
        for header, paragraphs in sections:
            buffer: List[str] = []
            current_len = 0
            for para in paragraphs:
                text = para.strip()
                if not text:
                    continue
                if buffer and current_len + len(text) > MAX_CHARS_DEFAULT:
                    chunk = self._make_chunk(doc_id, header, buffer, chunk_idx)
                    chunks.append(chunk)
                    chunk_idx += 1
                    buffer = []
                    current_len = 0
                buffer.append(text)
                current_len += len(text) + 1
            if buffer:
                chunk = self._make_chunk(doc_id, header, buffer, chunk_idx)
                chunks.append(chunk)
                chunk_idx += 1
        return chunks

    def _make_chunk(self, doc_id: str, header: str, lines: List[str], index: int) -> Chunk:
        text = '\n'.join(lines).strip()
        tokens = _tokenize(text)
        term_freq = Counter(tokens)
        text_lower = text.lower()
        boilerplate = any(keyword in text_lower for keyword in BOILERPLATE_KEYWORDS)
        return Chunk(
            doc_id=doc_id,
            uid=f"{doc_id}::C{index}",
            header=header,
            text=text,
            tokens=tokens,
            term_freq=term_freq,
            boilerplate=boilerplate,
        )

    def _register_aliases(self, doc_id: str, content: str):
        alias = self._extract_appellation_name(content)
        if not alias:
            alias = doc_id
        normalized = _normalize_text(alias)
        if normalized:
            self.doc_aliases[normalized] = doc_id
            if doc_id not in self.doc_alias_reverse:
                self.doc_alias_reverse[doc_id] = alias

    def _extract_appellation_name(self, content: str) -> str | None:
        match = re.search(
            r"appellation d['’]origine\s+(?:contr[oô]l[ée]e|prot[ée]g[ée])\s+«\s*([^»]+)\s*»",
            content,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
        return None

    def _route_doc_ids(self, query: str) -> List[str]:
        normalized = _normalize_text(query)
        hits = []
        for alias, doc_id in self.doc_aliases.items():
            if alias and alias in normalized:
                hits.append(doc_id)
        return hits[:3]

    def route(self, question: str) -> Dict[str, object]:
        normalized = _normalize_text(question)
        doc_ids = self._route_doc_ids(question)
        doc_ids = list(dict.fromkeys(doc_ids))[:3]
        normalized_appellation = ''
        if doc_ids:
            normalized_appellation = self.doc_alias_reverse.get(doc_ids[0], '')
        query_terms = self._query_terms(normalized)
        return {
            "doc_ids": doc_ids,
            "normalized_appellation": normalized_appellation,
            "query_terms": query_terms,
        }

    def _query_terms(self, normalized_question: str) -> List[str]:
        hints: List[str] = []
        for key, terms in ROUTER_QUERY_HINTS.items():
            if key in normalized_question:
                hints.extend(terms)
        if not hints:
            tokens = [token for token in normalized_question.split() if len(token) > 3]
            hints = tokens[:5]
        return hints[:6]

    def retrieve(
        self,
        query: str,
        route: Dict[str, object] | None = None,
        limit: int = MAX_CHARS_DEFAULT,
        top_k: int = 5,
    ) -> str:
        if not query or not self.chunks:
            self.last_debug = []
            return ''
        q_tokens = _tokenize(query)
        if not q_tokens:
            self.last_debug = []
            return ''
        query_counts = Counter(q_tokens)

        # Inject router query terms to bias scoring
        if route:
            for term in route.get('query_terms') or []:
                norm_term = _normalize_text(term)
                if not norm_term:
                    continue
                query_counts[norm_term] += 1

        candidate_doc_ids = []
        if route:
            candidate_doc_ids = route.get('doc_ids') or []
        if not candidate_doc_ids:
            candidate_doc_ids = self._route_doc_ids(query)
        if candidate_doc_ids:
            candidate_chunks = [chunk for chunk in self.chunks if chunk.doc_id in candidate_doc_ids]
        else:
            candidate_chunks = self.chunks
        scored: List[Tuple[float, Chunk]] = []
        for chunk in candidate_chunks:
            score = self._bm25(query_counts, chunk)
            if score <= 0:
                continue
            if chunk.boilerplate and not any(word in query.lower() for word in QUERY_BOILERPLATE_WHITELIST):
                score *= 0.2
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        snippets = []
        total = 0
        debug = []
        for score, chunk in scored[:top_k]:
            formatted = f"[DOCUMENT: {chunk.doc_id} | CHUNK: {chunk.uid} | SECTION: {chunk.header} | score={score:.2f}]\n{chunk.text}"
            if total + len(formatted) > limit and snippets:
                break
            snippets.append(formatted)
            total += len(formatted)
            debug.append({
                'doc_id': chunk.doc_id,
                'chunk': chunk.uid,
                'section': chunk.header,
                'score': f"{score:.2f}",
            })
        self.last_debug = debug
        return '\n\n'.join(snippets)

    def _bm25(self, query_counts: Counter, chunk: Chunk) -> float:
        if not chunk.tokens:
            return 0.0
        score = 0.0
        dl = len(chunk.tokens)
        k1 = 1.5
        b = 0.75
        for token, qtf in query_counts.items():
            tf = chunk.term_freq.get(token)
            if not tf:
                continue
            df = self.doc_freq.get(token, 0)
            if df == 0:
                continue
            idf = math.log(1 + (len(self.chunks) - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * dl / self.avgdl)
            score += idf * ((tf * (k1 + 1)) / denom) * qtf
        return score


rag_engine = SimpleRAG()

from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import List
import unicodedata

DOC_FILENAME = '2-cdc-aopc-tes-de-duras-v20241203.md'
DOC_PATH = os.path.join(os.path.dirname(__file__), 'knowledge', 'cdc', DOC_FILENAME)
DOC_ID = 'cdc_cotes_de_duras_2025'
DURAS_PATTERN = re.compile(r"(?i)\bc[oô]tes?\s+de\s+duras|\bduras\b")
WORD_PATTERN = re.compile(r"[a-zàâäçéèêëîïôöùûüÿñœæ0-9']+")
MAX_CHARS = 900
MIN_CHARS = 250
FACT_SNIPPETS = [
    {
        "id": "FACT_CHARGE",
        "keywords": {"charge", "charges", "parcelle", "kg", "kilogramme", "maximum", "maximale"},
        "text": (
            "[DURAS::FACT::CHARGE | Chapitre Ier §VI.1.d — Conduite du vignoble]\n"
            "Charge maximale moyenne à la parcelle (en kilogrammes par hectare) :\n"
            "- Vins blancs secs (densité >= 4000 pieds/ha) : 10 000 kg/ha\n"
            "- Vins blancs secs (3300 <= densité < 4000 pieds/ha) : 9 500 kg/ha\n"
            "- Autres vins blancs : 8 500 kg/ha\n"
            "- Vins rouges et rosés : 10 000 kg/ha\n"
            "ATTENTION : Ne pas confondre avec le rendement butoir (en hectolitres/ha)."
        ),
    },
    {
        "id": "FACT_DENSITE",
        "keywords": {"densité", "plantation", "pieds"},
        "text": (
            "[DURAS::FACT::DENSITE | Chapitre Ier §VI.1.a — Densité de plantation]\n"
            "Les vignes présentent une densité minimale de 4 000 pieds/ha (écartement inter-rang <= 2,50 m, 2,50 m²/pied).\n"
            "Pour les plantations destinées aux vins blancs secs : densité possible abaissée à 3 300 pieds/ha "
            "avec inter-rang < 3 m et espacement intra-rang > 0,85 m."
        ),
    },
    {
        "id": "FACT_RICHESSE",
        "keywords": {"richesse", "sucre", "liquoreux", "grammes"},
        "text": (
            "[DURAS::FACT::RICHESSE | Chapitre Ier §VII.2.a — Maturité du raisin]\n"
            "Richesse minimale en sucres des raisins (g/L de moût) :\n"
            "- Vins blancs secs : 170 g/L (TAV naturel >= 10,5 %)\n"
            "- Autres vins blancs (moelleux/liquoreux) : 185 g/L (TAV naturel >= 11,5 %)\n"
            "- Vins rouges et rosés : 180 g/L (TAV naturel >= 10,5 %)."
        ),
    },
    {
        "id": "FACT_RECOLTE",
        "keywords": {"récolte", "vendange", "vendanges", "créneaux", "rosé", "rosés", "maturité"},
        "text": (
            "[DURAS::FACT::RECOLTE | Chapitre Ier §VII.1 — Récolte]\n"
            "Les raisins destinés aux vins Côtes de Duras (y compris rosés) doivent être récoltés à bonne maturité. "
            "Il n'existe pas de créneaux horaires spécifiques pour les rosés. "
            "La seule exigence est la bonne maturité des raisins, fixée par l'ODG."
        ),
    },
]


@dataclass
class Chunk:
    uid: str
    title: str
    text: str
    tokens: List[str]
    term_freq: Counter


class DurasRAG:
    def __init__(self):
        self.chunks: List[Chunk] = self._build_chunks()
        self.doc_freq: Counter = Counter()
        for chunk in self.chunks:
            for token in chunk.term_freq.keys():
                self.doc_freq[token] += 1
        self.num_docs = len(self.chunks)
        self.avgdl = (
            sum(len(chunk.tokens) for chunk in self.chunks) / self.num_docs
            if self.num_docs
            else 1
        )

    def _build_chunks(self) -> List[Chunk]:
        if not os.path.exists(DOC_PATH):
            return []
        with open(DOC_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        sections = self._split_sections(content)
        chunks: List[Chunk] = []
        for idx, (title, text) in enumerate(sections):
            # Parse and inline tables before chunking
            text = self._parse_tables(text)
            if len(text) < MIN_CHARS:
                continue
            tokens = _tokenize(text)
            if not tokens:
                continue
            term_freq = Counter(tokens)
            uid = f"CHUNK_{idx:03d}"
            chunks.append(Chunk(uid=uid, title=title, text=text, tokens=tokens, term_freq=term_freq))
        return chunks
    
    def _parse_tables(self, text: str) -> str:
        """Convert Markdown tables to inline text for better retrieval"""
        lines = text.split('\n')
        result = []
        in_table = False
        table_buffer = []
        
        for line in lines:
            # Detect table rows (contains |)
            if '|' in line and not line.strip().startswith('#'):
                in_table = True
                table_buffer.append(line)
            else:
                if in_table and table_buffer:
                    # Convert table to text
                    result.append(self._table_to_text(table_buffer))
                    table_buffer = []
                    in_table = False
                result.append(line)
        
        # Handle trailing table
        if table_buffer:
            result.append(self._table_to_text(table_buffer))
        
        return '\n'.join(result)
    
    def _table_to_text(self, table_lines: List[str]) -> str:
        """Convert table lines to readable text"""
        if not table_lines:
            return ""
        
        # Parse header and rows
        rows = []
        for line in table_lines:
            # Skip separator lines (---)
            if re.match(r'^\s*\|[\s\-:]+\|\s*$', line):
                continue
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                rows.append(cells)
        
        if not rows:
            return ""
        
        # Format as bullet points
        header = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        result = []
        for row in data_rows:
            parts = []
            for i, cell in enumerate(row):
                if i < len(header):
                    parts.append(f"{header[i]}: {cell}")
                else:
                    parts.append(cell)
            result.append("- " + " | ".join(parts))
        
        return "\n".join(result)

    def _split_sections(self, content: str):
        sections: List[tuple[str, str]] = []
        current_title = 'Introduction'
        current_lines: List[str] = []
        for line in content.splitlines():
            if line.startswith('## '):
                if current_lines:
                    sections.append((current_title, '\n'.join(current_lines)))
                current_title = line[3:].strip()
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines:
            sections.append((current_title, '\n'.join(current_lines)))
        return sections

    def retrieve(self, query: str, limit_chars: int = 1500, top_k: int = 4) -> str:
        if not self.chunks or not query:
            return ''
        q_tokens = _tokenize(query)
        if not q_tokens:
            return ''
        query_counts = Counter(q_tokens)
        
        # Get fact snippets first
        facts = self._facts_for_query(query)
        
        # If we have facts, only return those (no BM25 chunks to avoid confusion)
        if facts:
            snippets = []
            total = 0
            for fact in facts:
                if total + len(fact) > limit_chars:
                    break
                snippets.append(fact)
                total += len(fact)
            return '\n\n'.join(snippets)
        
        # Otherwise, use BM25 scoring for chunks
        scored = []
        for chunk in self.chunks:
            score = self._bm25(query_counts, chunk)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        
        snippets = []
        total = 0
        for score, chunk in scored[:top_k]:
            formatted = f"[DURAS::{chunk.uid} | {chunk.title} | score={score:.2f}]\n{chunk.text}"
            if total + len(formatted) > limit_chars and snippets:
                break
            snippets.append(formatted)
            total += len(formatted)
        return '\n\n'.join(snippets[:10])

    def _facts_for_query(self, query: str) -> List[str]:
        normalized = _normalize_text(query)
        matches = []
        for fact in FACT_SNIPPETS:
            if any(keyword in normalized for keyword in fact["keywords"]):
                matches.append(fact["text"])
        return matches

    def _bm25(self, query_counts: Counter, chunk: Chunk) -> float:
        if not chunk.tokens:
            return 0.0
        score = 0.0
        dl = len(chunk.tokens)
        k1 = 1.4
        b = 0.75
        for token, qtf in query_counts.items():
            tf = chunk.term_freq.get(token)
            if not tf:
                continue
            df = self.doc_freq.get(token, 0)
            if df == 0:
                continue
            idf = math.log(1 + (self.num_docs - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * dl / self.avgdl)
            score += idf * ((tf * (k1 + 1)) / denom)
        return score


def _group_paragraphs(lines: List[str]) -> List[str]:
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


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [match.group(0) for match in WORD_PATTERN.finditer(text.lower()) if len(match.group(0)) > 2]


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching"""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', text.lower())
    normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    return normalized


def _wants_duras(question: str) -> bool:
    if not question:
        return False
    return bool(DURAS_PATTERN.search(question))


_duras_rag = DurasRAG()


def retrieve_duras_context(question: str, limit_chars: int = 1500) -> str:
    if not _wants_duras(question):
        return ''
    return _duras_rag.retrieve(question, limit_chars=limit_chars)

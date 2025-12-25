import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "Cahier des charges" / "pdfs" / "rag_out" / "chunks_ALL.jsonl"
OUT_DIR = ROOT / "apps" / "ai" / "knowledge" / "cdc"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "doc"


def load_chunks() -> dict[str, list[dict]]:
    chunks_by_doc: dict[str, list[dict]] = defaultdict(list)
    with CHUNKS_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            doc_id = data.get("doc_id") or data.get("source_file") or "doc"
            chunks_by_doc[doc_id].append(data)
    return chunks_by_doc


def ensure_paths() -> None:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_PATH}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def chunk_to_markdown(doc_id: str, chunks: list[dict]) -> str:
    chunks.sort(key=lambda c: (c.get("page") or 0, c.get("id") or ""))
    source = chunks[0].get("source_file", "unknown")
    sha = chunks[0].get("sha256", "")

    parts = [f"# Cahier des charges — {doc_id}\n\n",
             f"> Source: {source}\n\n> SHA256: {sha}\n\n"]

    for chunk in chunks:
        section = chunk.get("section") or "Section"
        page = chunk.get("page")
        if page is not None:
            parts.append(f"## {section} (page {page})\n\n")
        else:
            parts.append(f"## {section}\n\n")
        text = (chunk.get("text") or "").strip()
        parts.append(text + "\n\n")

    return "".join(parts)


def write_markdown(doc_id: str, content: str) -> Path:
    filename = slugify(doc_id) + ".md"
    out_file = OUT_DIR / filename
    out_file.write_text(content, encoding="utf-8")
    return out_file


def main() -> None:
    ensure_paths()
    chunks_by_doc = load_chunks()
    written = []
    for doc_id, chunks in chunks_by_doc.items():
        content = chunk_to_markdown(doc_id, chunks)
        out_file = write_markdown(doc_id, content)
        written.append(out_file)
    print(f"Converted {len(written)} documents into {OUT_DIR}")


if __name__ == "__main__":
    main()

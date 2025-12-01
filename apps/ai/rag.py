import os
import re
from django.conf import settings

DOCS_PATH = os.path.join(os.path.dirname(__file__), 'knowledge')

class SimpleRAG:
    def __init__(self):
        self.documents = {}
        self._load_docs()

    def _load_docs(self):
        """Load all markdown files from the knowledge directory."""
        if not os.path.exists(DOCS_PATH):
            return

        for filename in os.listdir(DOCS_PATH):
            if filename.endswith('.md'):
                path = os.path.join(DOCS_PATH, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documents[filename] = self._parse_sections(content)
                except Exception as e:
                    print(f"Error loading doc {filename}: {e}")

    def _parse_sections(self, content):
        """Split markdown content by H2 headers."""
        sections = {}
        current_header = "General"
        current_text = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_text:
                    sections[current_header] = '\n'.join(current_text).strip()
                current_header = line.replace('## ', '').strip()
                current_text = [line] # Keep the header in the text
            else:
                current_text.append(line)
        
        if current_text:
            sections[current_header] = '\n'.join(current_text).strip()
            
        return sections

    def retrieve(self, query, limit=1500):
        """Retrieve relevant sections based on simple keyword matching."""
        query = query.lower()
        hits = []
        
        # Keywords mapping to sections (heuristic)
        keywords = {
            'production': ['production', 'vigne', 'chai', 'cuve', 'vendange', 'vinification', 'élevage', 'mise'],
            'ventes': ['vente', 'client', 'commande', 'devis', 'facture', 'primeur', 'vrac'],
            'drm': ['drm', 'douane', 'crd', 'inao', 'r&eacute;glementaire', 'dsa', 'dae'],
            'stocks': ['stock', 'inventaire', 'matière', 'produit'],
            'référentiels': ['référentiel', 'cépage', 'contenant', 'config'],
            'onboarding': ['démarrage', 'commencer', 'aide', 'tuto']
        }

        # 1. Check generic sections mapping
        for section_key, terms in keywords.items():
            if any(t in query for t in terms):
                # Find matching sections in docs
                for doc_sections in self.documents.values():
                    for header, text in doc_sections.items():
                        if section_key.lower() in header.lower() or any(t in header.lower() for t in terms):
                            hits.append(text)

        # 2. If no hits, full text search in sections
        if not hits:
            for doc_sections in self.documents.values():
                for header, text in doc_sections.items():
                    if any(word in text.lower() for word in query.split() if len(word) > 4):
                        hits.append(text)
        
        # Deduplicate
        hits = list(set(hits))
        
        # Join until limit
        result = ""
        for hit in hits:
            if len(result) + len(hit) < limit:
                result += hit + "\n\n"
            else:
                break
                
        return result.strip()

# Singleton instance
rag_engine = SimpleRAG()

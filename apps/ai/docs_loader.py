"""
Documentation Loader pour le module d'aide MonChai
Charge et indexe la documentation exhaustive pour l'aide contextuelle ULTRA performante
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from django.conf import settings

# Chemin vers la documentation
DOCS_PATH = Path(settings.BASE_DIR) / 'docs' / 'help'


class DocsLoader:
    """Chargeur et indexeur de documentation pour l'aide contextuelle"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.docs_cache: Dict[str, str] = {}
        self.contextual_index: Dict = {}
        self.glossary: Dict[str, str] = {}
        self.faq: List[Dict] = []
        self.shortcuts: Dict = {}
        self.url_map: Dict[str, Dict] = {}
        self._load_all()
    
    def _load_all(self):
        """Charge toute la documentation"""
        self._load_markdown_docs()
        self._load_contextual_index()
        self._parse_glossary()
        self._parse_faq()
    
    def _load_markdown_docs(self):
        """Charge tous les fichiers markdown"""
        if not DOCS_PATH.exists():
            return
        
        for md_file in DOCS_PATH.glob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                self.docs_cache[md_file.stem] = content
            except Exception:
                pass
    
    def _load_contextual_index(self):
        """Charge l'index contextuel JSON"""
        index_path = DOCS_PATH / 'CONTEXTUAL_HELP_INDEX.json'
        if not index_path.exists():
            return
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.contextual_index = data.get('pages', {})
            self.shortcuts = data.get('shortcuts', {})
            self.faq = data.get('faq', [])
            self.glossary = data.get('glossary', {})
            
            # Créer un mapping URL -> aide
            for url, info in self.contextual_index.items():
                self.url_map[url] = info
                
        except Exception:
            pass
    
    def _parse_glossary(self):
        """Parse le glossaire depuis le markdown"""
        if 'GLOSSARY' not in self.docs_cache:
            return
        
        content = self.docs_cache['GLOSSARY']
        # Parse les définitions du glossaire (format: | **Terme** | Définition |)
        pattern = r'\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(pattern, content)
        
        for term, definition in matches:
            term = term.strip()
            definition = definition.strip()
            if term and definition and not term.startswith('---'):
                self.glossary[term.lower()] = definition
    
    def _parse_faq(self):
        """Parse la FAQ depuis le markdown"""
        if 'FAQ' not in self.docs_cache:
            return
        
        content = self.docs_cache['FAQ']
        # Parse les Q&A (format: ### Question\n...réponse...)
        pattern = r'###\s*([^\n]+)\n((?:(?!###)[^\n]*\n)*)'
        matches = re.findall(pattern, content)
        
        for question, answer in matches:
            question = question.strip()
            answer = answer.strip()
            if question and answer and '?' in question:
                self.faq.append({
                    'question': question,
                    'answer': answer[:500]  # Limite la taille
                })
    
    @lru_cache(maxsize=100)
    def get_help_for_url(self, url: str) -> Optional[Dict]:
        """Retourne l'aide contextuelle pour une URL donnée"""
        # Recherche exacte
        if url in self.url_map:
            return self.url_map[url]
        
        # Recherche avec trailing slash
        url_with_slash = url.rstrip('/') + '/'
        if url_with_slash in self.url_map:
            return self.url_map[url_with_slash]
        
        # Recherche par préfixe
        url_clean = url.rstrip('/')
        best_match = None
        best_len = 0
        
        for mapped_url, info in self.url_map.items():
            mapped_clean = mapped_url.rstrip('/')
            if url_clean.startswith(mapped_clean) and len(mapped_clean) > best_len:
                best_match = info
                best_len = len(mapped_clean)
        
        return best_match
    
    def get_definition(self, term: str) -> Optional[str]:
        """Retourne la définition d'un terme du glossaire"""
        term_lower = term.lower().strip()
        return self.glossary.get(term_lower)
    
    def search_faq(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche dans la FAQ"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        for item in self.faq:
            question_lower = item['question'].lower()
            # Score basé sur les mots communs
            question_words = set(question_lower.split())
            common = len(query_words & question_words)
            if common > 0:
                results.append((common, item))
        
        # Trier par score décroissant
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]
    
    def search_docs(self, query: str, limit: int = 3) -> List[Tuple[str, str]]:
        """Recherche dans toute la documentation"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        for doc_name, content in self.docs_cache.items():
            content_lower = content.lower()
            # Score basé sur le nombre de mots trouvés
            score = sum(1 for word in query_words if word in content_lower)
            
            if score > 0:
                # Extraire un snippet pertinent
                snippet = self._extract_snippet(content, query_words)
                results.append((score, doc_name, snippet))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [(name, snippet) for _, name, snippet in results[:limit]]
    
    def _extract_snippet(self, content: str, query_words: set, max_len: int = 300) -> str:
        """Extrait un snippet pertinent du contenu"""
        lines = content.split('\n')
        best_line = ""
        best_score = 0
        
        for line in lines:
            line_lower = line.lower()
            score = sum(1 for word in query_words if word in line_lower)
            if score > best_score:
                best_score = score
                best_line = line
        
        if best_line:
            return best_line[:max_len].strip()
        return content[:max_len].strip()
    
    def get_shortcuts(self, category: str = 'global') -> Dict:
        """Retourne les raccourcis clavier"""
        return self.shortcuts.get(category, {})
    
    def get_all_shortcuts(self) -> Dict:
        """Retourne tous les raccourcis clavier"""
        return self.shortcuts
    
    def build_context_for_query(self, query: str, url: str = '') -> str:
        """Construit un contexte enrichi pour une requête d'aide"""
        context_parts = []
        
        # 1. Aide contextuelle de la page
        if url:
            page_help = self.get_help_for_url(url)
            if page_help:
                context_parts.append(f"[PAGE: {page_help.get('title', 'N/A')}]")
                if page_help.get('help_text'):
                    context_parts.append(page_help['help_text'])
                if page_help.get('tips'):
                    context_parts.append("Tips: " + " | ".join(page_help['tips'][:3]))
        
        # 2. Recherche FAQ
        faq_results = self.search_faq(query, limit=2)
        for faq_item in faq_results:
            context_parts.append(f"[FAQ: {faq_item['question']}]")
            context_parts.append(faq_item['answer'][:200])
        
        # 3. Recherche docs
        doc_results = self.search_docs(query, limit=2)
        for doc_name, snippet in doc_results:
            context_parts.append(f"[DOC: {doc_name}]")
            context_parts.append(snippet)
        
        # 4. Définitions de termes
        query_words = query.lower().split()
        for word in query_words:
            definition = self.get_definition(word)
            if definition:
                context_parts.append(f"[GLOSSAIRE: {word}] {definition}")
        
        return "\n".join(context_parts)
    
    def reload(self):
        """Recharge toute la documentation"""
        self.docs_cache.clear()
        self.contextual_index.clear()
        self.glossary.clear()
        self.faq.clear()
        self.shortcuts.clear()
        self.url_map.clear()
        self.get_help_for_url.cache_clear()
        self._load_all()


# Instance singleton
docs_loader = DocsLoader()


def get_contextual_help(url: str) -> Dict:
    """Helper function pour obtenir l'aide contextuelle d'une URL"""
    return docs_loader.get_help_for_url(url) or {}


def search_help(query: str, url: str = '') -> str:
    """Helper function pour rechercher dans la documentation"""
    return docs_loader.build_context_for_query(query, url)


def get_faq_answer(question: str) -> Optional[str]:
    """Helper function pour trouver une réponse FAQ"""
    results = docs_loader.search_faq(question, limit=1)
    if results:
        return results[0]['answer']
    return None


def get_term_definition(term: str) -> Optional[str]:
    """Helper function pour obtenir une définition"""
    return docs_loader.get_definition(term)

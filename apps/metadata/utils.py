"""
Utilitaires pour la recherche et normalisation de texte
Roadmap Meta Base de Données - Phase P2
"""

import re
import unicodedata
from typing import List, Optional
from django.db import connection


def normalize_text(text: str) -> str:
    """
    Normalise un texte pour la recherche
    Roadmap P2: util normalize(text) (lowercase, unaccent, trim, collapse spaces)
    
    Args:
        text: Texte à normaliser
        
    Returns:
        Texte normalisé
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Supprimer les accents (unaccent)
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Trim et collapse spaces
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Supprimer la ponctuation pour la recherche
    text = re.sub(r'[^\w\s-]', ' ', text)
    
    # Collapse les espaces après suppression ponctuation
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text


def split_search_terms(query: str) -> List[str]:
    """
    Divise une requête en termes de recherche
    
    Args:
        query: Requête de recherche
        
    Returns:
        Liste des termes normalisés
    """
    normalized = normalize_text(query)
    if not normalized:
        return []
    
    # Diviser sur les espaces et tirets
    terms = re.split(r'[\s\-]+', normalized)
    
    # Filtrer les termes trop courts
    terms = [term for term in terms if len(term) >= 2]
    
    return terms


def build_tsquery(query: str, language: str = 'simple') -> str:
    """
    Construit une requête tsquery PostgreSQL à partir d'une requête utilisateur
    
    Args:
        query: Requête utilisateur
        language: Langue pour le dictionnaire PostgreSQL
        
    Returns:
        Requête tsquery formatée
    """
    terms = split_search_terms(query)
    if not terms:
        return ""
    
    # Joindre les termes avec l'opérateur AND
    # Chaque terme peut être préfixé pour la recherche partielle
    formatted_terms = []
    for term in terms:
        if len(term) >= 3:
            # Recherche exacte ET préfixe pour les termes longs
            formatted_terms.append(f"({term} | {term}:*)")
        else:
            # Recherche exacte seulement pour les termes courts
            formatted_terms.append(term)
    
    return " & ".join(formatted_terms)


def calculate_search_rank(
    tsv_column: str, 
    query: str, 
    exact_match_bonus: float = 0.5,
    title_bonus: float = 0.3
) -> str:
    """
    Calcule un score de pertinence pour la recherche
    Roadmap P2: Score = ts_rank_cd(tsv, query) + bonus exact match + bonus champs clés
    
    Args:
        tsv_column: Nom de la colonne tsvector
        query: Requête de recherche
        exact_match_bonus: Bonus pour correspondance exacte
        title_bonus: Bonus pour correspondance dans le titre
        
    Returns:
        Expression SQL pour le score
    """
    tsquery = build_tsquery(query)
    if not tsquery:
        return "0"
    
    base_rank = f"ts_rank_cd({tsv_column}, plainto_tsquery('simple', %s))"
    
    # Bonus pour correspondance exacte dans le nom
    exact_bonus = f"""
        CASE WHEN LOWER(unaccent(name)) LIKE LOWER(unaccent(%s)) 
        THEN {exact_match_bonus} ELSE 0 END
    """
    
    # Bonus pour correspondance au début du nom (titre)
    title_bonus_sql = f"""
        CASE WHEN LOWER(unaccent(name)) LIKE LOWER(unaccent(%s)) 
        THEN {title_bonus} ELSE 0 END
    """
    
    return f"({base_rank} + {exact_bonus} + {title_bonus_sql})"


def create_search_index(model_class, fields: List[str], index_name: Optional[str] = None):
    """
    Crée un index de recherche full-text pour un modèle
    Roadmap P2: Index tsvector + GIN
    
    Args:
        model_class: Classe du modèle Django
        fields: Liste des champs à indexer
        index_name: Nom de l'index (optionnel)
    """
    table_name = model_class._meta.db_table
    if not index_name:
        index_name = f"idx_{table_name}_search_tsv"
    
    # Construire l'expression tsvector
    field_expressions = []
    for field in fields:
        field_expressions.append(f"coalesce({field}, '')")
    
    tsvector_expr = f"to_tsvector('simple', unaccent({' || \' \' || '.join(field_expressions)}))"
    
    # SQL pour ajouter la colonne et l'index
    sql_commands = [
        f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS search_tsv tsvector;",
        f"UPDATE {table_name} SET search_tsv = {tsvector_expr};",
        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING GIN (search_tsv);",
    ]
    
    with connection.cursor() as cursor:
        for sql in sql_commands:
            cursor.execute(sql)


def create_trigram_index(model_class, field: str, index_name: Optional[str] = None):
    """
    Crée un index trigramme pour recherche fuzzy
    Roadmap P2: Index trigram pour fuzzy LIKE/ILIKE
    
    Args:
        model_class: Classe du modèle Django
        field: Champ à indexer
        index_name: Nom de l'index (optionnel)
    """
    table_name = model_class._meta.db_table
    if not index_name:
        index_name = f"idx_{table_name}_{field}_trgm"
    
    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} USING GIN ({field} gin_trgm_ops);"
    
    with connection.cursor() as cursor:
        cursor.execute(sql)


def fuzzy_search(query: str, field_name: str, similarity_threshold: float = 0.3) -> str:
    """
    Génère une condition de recherche fuzzy avec trigrammes
    
    Args:
        query: Requête de recherche
        field_name: Nom du champ
        similarity_threshold: Seuil de similarité (0.0 à 1.0)
        
    Returns:
        Condition SQL pour recherche fuzzy
    """
    normalized_query = normalize_text(query)
    return f"similarity({field_name}, %s) > {similarity_threshold}"


class SearchQueryBuilder:
    """
    Constructeur de requêtes de recherche sécurisé
    Roadmap P3: Query Builder serveur - traduction sécurisée → SQL paramétré
    """
    
    OPERATORS = {
        'eq': '= %s',
        'neq': '!= %s',
        'in': 'IN %s',
        'nin': 'NOT IN %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'like': 'LIKE %s',
        'ilike': 'ILIKE %s',
        'between': 'BETWEEN %s AND %s',
        'isnull': 'IS NULL',
        'isnotnull': 'IS NOT NULL',
    }
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.where_conditions = []
        self.params = []
        self.order_by = []
    
    def add_filter(self, field: str, operator: str, value=None):
        """
        Ajoute un filtre sécurisé
        
        Args:
            field: Nom du champ (doit être whitelisté)
            operator: Opérateur (eq, gt, like, etc.)
            value: Valeur à comparer
        """
        if operator not in self.OPERATORS:
            raise ValueError(f"Opérateur non supporté: {operator}")
        
        # Vérifier que le champ existe sur le modèle (sécurité)
        if not hasattr(self.model_class, field):
            raise ValueError(f"Champ non trouvé: {field}")
        
        sql_operator = self.OPERATORS[operator]
        
        if operator in ['isnull', 'isnotnull']:
            self.where_conditions.append(f"{field} {sql_operator}")
        elif operator == 'between':
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("L'opérateur 'between' nécessite une liste de 2 valeurs")
            self.where_conditions.append(f"{field} {sql_operator}")
            self.params.extend(value)
        else:
            self.where_conditions.append(f"{field} {sql_operator}")
            self.params.append(value)
    
    def add_search(self, query: str, fields: List[str]):
        """
        Ajoute une recherche full-text
        
        Args:
            query: Requête de recherche
            fields: Champs à rechercher
        """
        if not query.strip():
            return
        
        # Recherche dans search_tsv si disponible
        if hasattr(self.model_class, 'search_tsv'):
            tsquery = build_tsquery(query)
            self.where_conditions.append("search_tsv @@ plainto_tsquery('simple', unaccent(%s))")
            self.params.append(query)
        else:
            # Fallback sur recherche ILIKE
            field_conditions = []
            for field in fields:
                if hasattr(self.model_class, field):
                    field_conditions.append(f"LOWER(unaccent({field})) LIKE LOWER(unaccent(%s))")
                    self.params.append(f"%{query}%")
            
            if field_conditions:
                self.where_conditions.append(f"({' OR '.join(field_conditions)})")
    
    def add_order(self, field: str, direction: str = 'ASC'):
        """
        Ajoute un tri
        
        Args:
            field: Champ de tri
            direction: ASC ou DESC
        """
        if not hasattr(self.model_class, field):
            raise ValueError(f"Champ non trouvé: {field}")
        
        direction = direction.upper()
        if direction not in ['ASC', 'DESC']:
            raise ValueError("Direction doit être ASC ou DESC")
        
        self.order_by.append(f"{field} {direction}")
    
    def build_where_clause(self) -> tuple:
        """
        Construit la clause WHERE
        
        Returns:
            Tuple (sql, params)
        """
        if not self.where_conditions:
            return "", []
        
        sql = "WHERE " + " AND ".join(self.where_conditions)
        return sql, self.params
    
    def build_order_clause(self) -> str:
        """
        Construit la clause ORDER BY
        
        Returns:
            Clause SQL ORDER BY
        """
        if not self.order_by:
            return ""
        
        return "ORDER BY " + ", ".join(self.order_by)

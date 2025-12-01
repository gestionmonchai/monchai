"""
Métamodèle pour la gouvernance des données
Roadmap Meta Base de Données - Phase P1
"""

import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.accounts.models import Organization


class MetaEntity(models.Model):
    """
    Entité métier référencée dans le système
    Roadmap P1: meta_entity(id, org_id, name, code, domain, is_searchable, is_listable)
    """
    
    DOMAIN_CHOICES = [
        ('viticulture', 'Viticulture'),
        ('production', 'Production'),
        ('commercial', 'Commercial'),
        ('finance', 'Finance'),
        ('referentiel', 'Référentiel'),
        ('system', 'Système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='meta_entities',
        null=True, blank=True,  # Null pour entités système globales
        help_text="Organisation propriétaire, null pour entités système"
    )
    
    # Identification
    name = models.CharField(max_length=100, help_text="Nom humain de l'entité")
    code = models.CharField(max_length=50, help_text="Code technique unique")
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, help_text="Domaine métier")
    
    # Référence au modèle Django
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        help_text="Type de contenu Django correspondant"
    )
    
    # Configuration recherche
    is_searchable = models.BooleanField(default=True, help_text="Inclure dans la recherche globale")
    is_listable = models.BooleanField(default=True, help_text="Affichable dans les listes")
    
    # Métadonnées
    description = models.TextField(blank=True, help_text="Description de l'entité")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Soft delete")
    
    class Meta:
        verbose_name = "Entité métier"
        verbose_name_plural = "Entités métier"
        unique_together = [['organization', 'code'], ['content_type']]
        ordering = ['domain', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class MetaAttribute(models.Model):
    """
    Attribut d'une entité métier
    Roadmap P1: meta_attribute(id, entity_id, name, code, dtype, nullable, unit, ref_entity_id, is_facet, is_sort, is_fulltext)
    """
    
    DATA_TYPE_CHOICES = [
        ('text', 'Texte'),
        ('number', 'Nombre'),
        ('decimal', 'Décimal'),
        ('boolean', 'Booléen'),
        ('date', 'Date'),
        ('datetime', 'Date et heure'),
        ('choice', 'Choix (énumération)'),
        ('reference', 'Référence vers entité'),
        ('json', 'JSON'),
        ('file', 'Fichier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(MetaEntity, on_delete=models.CASCADE, related_name='attributes')
    
    # Identification
    name = models.CharField(max_length=100, help_text="Nom humain de l'attribut")
    code = models.CharField(max_length=50, help_text="Nom du champ en base")
    
    # Type et contraintes
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES)
    is_nullable = models.BooleanField(default=True, help_text="Peut être null")
    unit = models.CharField(max_length=20, blank=True, help_text="Unité (kg, L, °C, etc.)")
    
    # Référence (si data_type='reference')
    ref_entity = models.ForeignKey(
        MetaEntity, 
        on_delete=models.CASCADE, 
        related_name='referenced_by',
        null=True, blank=True,
        help_text="Entité référencée si type=reference"
    )
    
    # Configuration interface
    is_facet = models.BooleanField(default=False, help_text="Utilisable comme facette de filtrage")
    is_sortable = models.BooleanField(default=False, help_text="Utilisable pour le tri")
    is_fulltext = models.BooleanField(default=False, help_text="Inclure dans la recherche textuelle")
    is_required = models.BooleanField(default=False, help_text="Champ obligatoire")
    
    # Affichage
    display_order = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage")
    help_text = models.TextField(blank=True, help_text="Aide contextuelle")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Attribut métier"
        verbose_name_plural = "Attributs métier"
        unique_together = [['entity', 'code']]
        ordering = ['entity', 'display_order', 'name']
    
    def __str__(self):
        return f"{self.entity.name}.{self.name}"


class MetaRelation(models.Model):
    """
    Relation entre entités métier
    Roadmap P1: meta_relation(id, src_entity_id, dst_entity_id, rel_type, cardinality)
    """
    
    RELATION_TYPE_CHOICES = [
        ('one_to_one', 'Un vers un'),
        ('one_to_many', 'Un vers plusieurs'),
        ('many_to_many', 'Plusieurs vers plusieurs'),
        ('inheritance', 'Héritage'),
        ('composition', 'Composition'),
        ('aggregation', 'Agrégation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Entités liées
    source_entity = models.ForeignKey(
        MetaEntity, 
        on_delete=models.CASCADE, 
        related_name='relations_as_source'
    )
    target_entity = models.ForeignKey(
        MetaEntity, 
        on_delete=models.CASCADE, 
        related_name='relations_as_target'
    )
    
    # Type de relation
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPE_CHOICES)
    
    # Nommage
    source_name = models.CharField(max_length=50, help_text="Nom de la relation côté source")
    target_name = models.CharField(max_length=50, help_text="Nom de la relation côté cible")
    
    # Configuration
    is_navigable_forward = models.BooleanField(default=True, help_text="Navigation source → cible")
    is_navigable_backward = models.BooleanField(default=True, help_text="Navigation cible → source")
    
    # Métadonnées
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Relation métier"
        verbose_name_plural = "Relations métier"
        unique_together = [['source_entity', 'target_entity', 'source_name']]
        ordering = ['source_entity', 'target_entity']
    
    def __str__(self):
        return f"{self.source_entity.name} → {self.target_entity.name} ({self.relation_type})"


class MetaEnum(models.Model):
    """
    Valeurs énumérées pour attributs de type 'choice'
    Roadmap P1: meta_enum(id, attribute_id, value, label, order)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attribute = models.ForeignKey(
        MetaAttribute, 
        on_delete=models.CASCADE, 
        related_name='enum_values',
        limit_choices_to={'data_type': 'choice'}
    )
    
    # Valeur
    value = models.CharField(max_length=100, help_text="Valeur technique stockée")
    label = models.CharField(max_length=200, help_text="Libellé affiché à l'utilisateur")
    
    # Affichage
    display_order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, blank=True, help_text="Couleur hexadécimale #RRGGBB")
    icon = models.CharField(max_length=50, blank=True, help_text="Classe d'icône Bootstrap")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Valeur énumérée"
        verbose_name_plural = "Valeurs énumérées"
        unique_together = [['attribute', 'value']]
        ordering = ['attribute', 'display_order', 'label']
    
    def __str__(self):
        return f"{self.attribute.entity.name}.{self.attribute.name}: {self.label}"


class MetaGlossary(models.Model):
    """
    Dictionnaire de données humain
    Roadmap P1: meta_glossary(term, definition, lang, synonyms)
    """
    
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='glossary_terms',
        null=True, blank=True,  # Null pour termes système globaux
    )
    
    # Terme
    term = models.CharField(max_length=100, help_text="Terme métier")
    definition = models.TextField(help_text="Définition complète")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')
    
    # Synonymes et variantes
    synonyms = models.JSONField(default=list, blank=True, help_text="Liste des synonymes")
    abbreviations = models.JSONField(default=list, blank=True, help_text="Abréviations courantes")
    
    # Liens
    related_entities = models.ManyToManyField(
        MetaEntity, 
        blank=True, 
        related_name='glossary_terms',
        help_text="Entités liées à ce terme"
    )
    
    # Classification
    domain = models.CharField(max_length=50, blank=True, help_text="Domaine métier")
    tags = models.JSONField(default=list, blank=True, help_text="Tags de classification")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Terme du glossaire"
        verbose_name_plural = "Termes du glossaire"
        unique_together = [['organization', 'term', 'language']]
        ordering = ['term']
    
    def __str__(self):
        return f"{self.term} ({self.language})"


class MetaRule(models.Model):
    """
    Règles de qualité des données
    Roadmap P1: meta_rule (ex: regex SIRET, plage millésime)
    """
    
    RULE_TYPE_CHOICES = [
        ('regex', 'Expression régulière'),
        ('range', 'Plage de valeurs'),
        ('length', 'Longueur'),
        ('format', 'Format spécifique'),
        ('reference', 'Intégrité référentielle'),
        ('business', 'Règle métier'),
        ('custom', 'Règle personnalisée'),
    ]
    
    SEVERITY_CHOICES = [
        ('error', 'Erreur (bloquant)'),
        ('warning', 'Avertissement'),
        ('info', 'Information'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(MetaEntity, on_delete=models.CASCADE, related_name='quality_rules')
    attribute = models.ForeignKey(
        MetaAttribute, 
        on_delete=models.CASCADE, 
        related_name='quality_rules',
        null=True, blank=True,
        help_text="Attribut concerné, null pour règles sur l'entité complète"
    )
    
    # Règle
    name = models.CharField(max_length=100, help_text="Nom de la règle")
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    rule_config = models.JSONField(help_text="Configuration de la règle (regex, min/max, etc.)")
    
    # Comportement
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning')
    error_message = models.TextField(help_text="Message d'erreur à afficher")
    
    # Exécution
    is_active = models.BooleanField(default=True)
    check_on_save = models.BooleanField(default=True, help_text="Vérifier à la sauvegarde")
    check_on_batch = models.BooleanField(default=True, help_text="Vérifier en batch")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Règle de qualité"
        verbose_name_plural = "Règles de qualité"
        ordering = ['entity', 'attribute', 'name']
    
    def __str__(self):
        attr_part = f".{self.attribute.name}" if self.attribute else ""
        return f"{self.entity.name}{attr_part}: {self.name}"


class FeatureFlag(models.Model):
    """
    Feature Flags pour déploiement progressif
    GIGA ROADMAP S0: search_v2_read, search_v2_write, inline_edit_v2_enabled
    """
    
    name = models.CharField(max_length=100, unique=True, help_text="Nom du flag (ex: search_v2_read)")
    description = models.TextField(help_text="Description du flag et son impact")
    is_enabled = models.BooleanField(default=False, help_text="Flag activé globalement")
    
    # Activation par organisation (optionnel)
    enabled_organizations = models.ManyToManyField(
        Organization,
        blank=True,
        help_text="Organisations avec ce flag activé (si vide = global)"
    )
    
    # Activation par pourcentage (canary)
    rollout_percentage = models.PositiveIntegerField(
        default=0,
        help_text="Pourcentage d'utilisateurs avec ce flag (0-100)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feature Flag"
        verbose_name_plural = "Feature Flags"
        ordering = ['name']
    
    def __str__(self):
        status = "ON" if self.is_enabled else "OFF"
        return f"{self.name} ({status})"
    
    def is_enabled_for_organization(self, organization):
        """Vérifie si le flag est activé pour une organisation"""
        if not self.is_enabled:
            return False
        
        # Si pas d'orgs spécifiques, c'est global
        if not self.enabled_organizations.exists():
            return True
        
        # Sinon vérifier si l'org est dans la liste
        return self.enabled_organizations.filter(id=organization.id).exists()
    
    def is_enabled_for_user(self, user):
        """Vérifie si le flag est activé pour un utilisateur (canary)"""
        if not self.is_enabled:
            return False
        
        # Vérifier d'abord l'organisation
        if hasattr(user, 'get_active_membership'):
            membership = user.get_active_membership()
            if membership and not self.is_enabled_for_organization(membership.organization):
                return False
        
        # Puis vérifier le rollout percentage
        if self.rollout_percentage == 0:
            return False
        if self.rollout_percentage >= 100:
            return True
        
        # Hash stable basé sur user.id pour cohérence
        import hashlib
        user_hash = int(hashlib.md5(f"{user.id}:{self.name}".encode()).hexdigest()[:8], 16)
        return (user_hash % 100) < self.rollout_percentage


class SearchMetrics(models.Model):
    """
    Métriques de recherche pour monitoring
    GIGA ROADMAP S0: capturer métriques v1 pour comparaison
    """
    
    ENGINE_CHOICES = [
        ('v1', 'Recherche V1 (actuelle)'),
        ('v2', 'Recherche V2 (FTS + trigram)'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    engine_version = models.CharField(max_length=10, choices=ENGINE_CHOICES, default='v1')
    
    # Requête
    query_hash = models.CharField(max_length=64, help_text="Hash MD5 de la requête (pas de PII)")
    entity_type = models.CharField(max_length=50, help_text="Type d'entité recherchée")
    
    # Résultats
    result_count = models.PositiveIntegerField(help_text="Nombre de résultats")
    has_results = models.BooleanField(help_text="Au moins 1 résultat")
    
    # Performance
    elapsed_ms = models.PositiveIntegerField(help_text="Temps de réponse en ms")
    cache_hit = models.BooleanField(default=False, help_text="Résultat depuis le cache")
    
    # Contexte
    user_agent = models.CharField(max_length=200, blank=True)
    is_live_search = models.BooleanField(default=False, help_text="Recherche en temps réel")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Métrique de recherche"
        verbose_name_plural = "Métriques de recherche"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'engine_version', 'created_at']),
            models.Index(fields=['entity_type', 'has_results']),
            models.Index(fields=['elapsed_ms']),
        ]
    
    def __str__(self):
        return f"{self.entity_type} ({self.engine_version}) - {self.elapsed_ms}ms"

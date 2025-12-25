"""
Modèles core pour Mon Chai - TimelineEvent et documents génériques
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import Organization
from apps.core.tenancy import TenantManager


class TimelineEvent(models.Model):
    """
    Modèle générique pour tracer les événements sur n'importe quel objet métier.
    Permet d'avoir une timeline unifiée pour parcelles, lots, clients, etc.
    
    Sécurité multi-tenant : filtré par organization.
    """
    
    EVENT_TYPES = [
        ('operation', 'Opération'),
        ('document', 'Document'),
        ('status', 'Changement de statut'),
        ('note', 'Note'),
        ('system', 'Système'),
        ('link', 'Liaison'),
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('alert', 'Alerte'),
        ('analysis', 'Analyse'),
        ('movement', 'Mouvement'),
    ]
    
    IMPORTANCE_LEVELS = [
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Important'),
        ('critical', 'Critique'),
    ]
    
    # Multi-tenant
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        related_name='timeline_events',
        verbose_name="Organisation"
    )
    
    # Objet cible (parcelle, lot, client, etc.)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='timeline_events_as_target',
        verbose_name="Type d'objet cible"
    )
    target_object_id = models.CharField(max_length=50, verbose_name="ID objet cible")
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Objet source (optionnel) - ex: le traitement phyto qui a créé cet événement
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='timeline_events_as_source',
        verbose_name="Type d'objet source"
    )
    source_object_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID objet source")
    source = GenericForeignKey('source_content_type', 'source_object_id')
    
    # Métadonnées de l'événement
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default='system',
        db_index=True,
        verbose_name="Type d'événement"
    )
    importance = models.CharField(
        max_length=10,
        choices=IMPORTANCE_LEVELS,
        default='normal',
        verbose_name="Importance"
    )
    
    # Contenu
    title = models.CharField(max_length=255, verbose_name="Titre")
    summary = models.TextField(blank=True, verbose_name="Résumé")
    payload = models.JSONField(
        default=dict, blank=True,
        verbose_name="Données additionnelles",
        help_text="Données JSON libres pour stocker des infos supplémentaires"
    )
    
    # Audit
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Date")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_timeline_events',
        verbose_name="Créé par"
    )
    
    # Gestion
    is_pinned = models.BooleanField(default=False, verbose_name="Épinglé")
    is_visible = models.BooleanField(default=True, verbose_name="Visible")
    
    objects = TenantManager()
    
    class Meta:
        verbose_name = "Événement timeline"
        verbose_name_plural = "Événements timeline"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'target_content_type', 'target_object_id']),
            models.Index(fields=['organization', 'event_type', 'created_at']),
            models.Index(fields=['target_content_type', 'target_object_id', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"
    
    @classmethod
    def create_for_object(cls, obj, event_type, title, summary='', source=None, user=None, **kwargs):
        """
        Crée un événement pour un objet donné.
        
        Usage:
            TimelineEvent.create_for_object(
                parcelle, 'operation', 'Traitement phyto appliqué',
                summary='Bouillie bordelaise 2kg/ha',
                source=traitement_phyto,
                user=request.user
            )
        """
        # Récupérer l'organisation depuis l'objet
        org = getattr(obj, 'organization', None) or getattr(obj, 'org', None)
        if not org:
            raise ValueError(f"L'objet {obj} n'a pas d'organisation associée")
        
        target_ct = ContentType.objects.get_for_model(obj)
        
        event = cls(
            organization=org,
            target_content_type=target_ct,
            target_object_id=str(obj.pk),
            event_type=event_type,
            title=title,
            summary=summary,
            created_by=user,
            **kwargs
        )
        
        if source:
            source_ct = ContentType.objects.get_for_model(source)
            event.source_content_type = source_ct
            event.source_object_id = str(source.pk)
        
        event.save()
        return event
    
    def get_source_url(self):
        """Retourne l'URL de l'objet source si disponible"""
        if self.source:
            try:
                return self.source.get_absolute_url()
            except AttributeError:
                pass
        return None
    
    def get_target_url(self):
        """Retourne l'URL de l'objet cible si disponible"""
        if self.target:
            try:
                return self.target.get_absolute_url()
            except AttributeError:
                pass
        return None


class Document(models.Model):
    """
    Document attaché à n'importe quel objet métier via GenericForeignKey.
    """
    
    DOC_TYPES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('spreadsheet', 'Tableur'),
        ('text', 'Texte'),
        ('archive', 'Archive'),
        ('other', 'Autre'),
    ]
    
    CATEGORIES = [
        ('contract', 'Contrat'),
        ('invoice', 'Facture'),
        ('analysis', 'Analyse'),
        ('certificate', 'Certificat'),
        ('photo', 'Photo'),
        ('report', 'Rapport'),
        ('regulatory', 'Réglementaire'),
        ('other', 'Autre'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Organisation"
    )
    
    # Objet lié
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Type d'objet"
    )
    object_id = models.CharField(max_length=50, verbose_name="ID objet")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Fichier
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name="Fichier")
    filename = models.CharField(max_length=255, verbose_name="Nom du fichier")
    file_type = models.CharField(max_length=20, choices=DOC_TYPES, default='other', verbose_name="Type")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (octets)")
    
    # Métadonnées
    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    category = models.CharField(max_length=20, choices=CATEGORIES, default='other', verbose_name="Catégorie")
    tags = models.JSONField(default=list, blank=True, verbose_name="Tags")
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Créé par"
    )
    
    objects = TenantManager()
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'content_type', 'object_id']),
        ]
    
    def __str__(self):
        return self.title or self.filename


class RelationConfig(models.Model):
    """
    Configuration des relations pour un modèle donné.
    Permet de définir dynamiquement les relations à afficher dans la vue Relations.
    """
    
    # Modèle source
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='relation_configs',
        verbose_name="Modèle source"
    )
    
    # Configuration
    name = models.CharField(max_length=50, verbose_name="Nom technique")
    label = models.CharField(max_length=100, verbose_name="Libellé affiché")
    icon = models.CharField(max_length=50, default='bi-link', verbose_name="Icône Bootstrap")
    
    # Relation
    related_model = models.CharField(max_length=100, verbose_name="Modèle lié (app.Model)")
    lookup_field = models.CharField(max_length=100, verbose_name="Champ de liaison")
    
    # Affichage
    list_fields = models.JSONField(default=list, verbose_name="Champs à afficher")
    search_fields = models.JSONField(default=list, verbose_name="Champs recherchables")
    default_ordering = models.CharField(max_length=50, default='-created_at', verbose_name="Tri par défaut")
    
    # Actions
    can_create = models.BooleanField(default=False, verbose_name="Peut créer")
    create_url_name = models.CharField(max_length=100, blank=True, verbose_name="URL de création")
    can_link = models.BooleanField(default=False, verbose_name="Peut lier")
    
    # Ordre d'affichage
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Configuration relation"
        verbose_name_plural = "Configurations relations"
        ordering = ['source_content_type', 'order']
        unique_together = ['source_content_type', 'name']
    
    def __str__(self):
        return f"{self.source_content_type} -> {self.label}"

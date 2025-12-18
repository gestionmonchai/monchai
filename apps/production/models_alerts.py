"""
Alert/Reminder system for Production module.
Allows users to create configurable alerts on any production object.
"""
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import uuid

from apps.accounts.models import Organization
from apps.core.tenancy import TenantManager


class Alert(models.Model):
    """
    Generic alert/reminder that can be attached to any production object.
    
    Usage:
    - Brouillons à finaliser (vendanges, lots, assemblages)
    - Rappels d'opérations à effectuer
    - Alertes sur seuils (SO2, température, etc.)
    - Tâches planifiées
    """
    
    # id auto-généré par Django (BigAutoField)
    
    # Link to any model (GenericForeignKey)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Type d'objet lié (Vendange, Lot, etc.)"
    )
    object_id = models.CharField(max_length=64, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Alert details
    PRIORITY_CHOICES = (
        ('low', 'Basse'),
        ('medium', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    )
    
    TYPE_CHOICES = (
        ('draft', 'Brouillon à finaliser'),
        ('reminder', 'Rappel'),
        ('action', 'Action à effectuer'),
        ('threshold', 'Seuil dépassé'),
        ('deadline', 'Échéance'),
        ('custom', 'Personnalisé'),
    )
    
    CATEGORY_CHOICES = (
        ('vendange', 'Vendanges'),
        ('lot', 'Lots techniques'),
        ('assemblage', 'Assemblages'),
        ('analyse', 'Analyses'),
        ('contenant', 'Contenants'),
        ('mise', 'Mises en bouteille'),
        ('parcelle', 'Parcelles'),
        ('general', 'Général'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    alert_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='reminder')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Scheduling
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance")
    due_time = models.TimeField(null=True, blank=True, verbose_name="Heure")
    
    # Status
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('snoozed', 'Reportée'),
        ('completed', 'Terminée'),
        ('dismissed', 'Ignorée'),
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')
    completed_at = models.DateTimeField(null=True, blank=True)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    
    # Recurrence (optional)
    is_recurring = models.BooleanField(default=False)
    RECURRENCE_CHOICES = (
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    )
    recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='created_alerts'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_alerts'
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tenancy
    TENANT_ORG_LOOKUPS = ('organization',)
    objects = TenantManager()
    
    class Meta:
        ordering = ['-priority', 'due_date', '-created_at']
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
    
    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"
    
    @property
    def is_overdue(self):
        """Check if alert is past due date."""
        if self.due_date and self.status == 'active':
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def is_due_today(self):
        """Check if alert is due today."""
        if self.due_date:
            return self.due_date == timezone.now().date()
        return False
    
    @property
    def priority_color(self):
        """Bootstrap color for priority."""
        colors = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        return colors.get(self.priority, 'secondary')
    
    @property
    def type_icon(self):
        """Bootstrap icon for alert type."""
        icons = {
            'draft': 'bi-file-earmark-text',
            'reminder': 'bi-bell',
            'action': 'bi-lightning',
            'threshold': 'bi-exclamation-triangle',
            'deadline': 'bi-calendar-event',
            'custom': 'bi-flag',
        }
        return icons.get(self.alert_type, 'bi-bell')
    
    def mark_completed(self):
        """Mark alert as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def snooze(self, hours=24):
        """Snooze alert for specified hours."""
        self.status = 'snoozed'
        self.snoozed_until = timezone.now() + timezone.timedelta(hours=hours)
        self.save()
    
    def dismiss(self):
        """Dismiss alert without completing."""
        self.status = 'dismissed'
        self.save()
    
    @classmethod
    def create_draft_alert(cls, obj, organization, created_by=None):
        """
        Helper to create a draft alert for any object.
        """
        content_type = ContentType.objects.get_for_model(obj)
        model_name = content_type.model
        
        category_map = {
            'vendangereception': 'vendange',
            'lottechnique': 'lot',
            'assemblage': 'assemblage',
            'analyse': 'analyse',
            'contenant': 'contenant',
        }
        
        return cls.objects.create(
            content_type=content_type,
            object_id=str(obj.pk),
            title=f"Brouillon à finaliser: {obj}",
            alert_type='draft',
            category=category_map.get(model_name, 'general'),
            priority='medium',
            organization=organization,
            created_by=created_by,
        )

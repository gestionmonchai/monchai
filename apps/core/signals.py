"""
Signals pour auto-création de TimelineEvents
=============================================

Permet de créer automatiquement des événements timeline
lorsque certains modèles sont créés/modifiés.

Usage:
    # Dans le modèle ou l'app concernée
    from apps.core.signals import register_timeline_signal
    
    register_timeline_signal(
        TraitementPhyto,
        event_type='operation',
        title_template='Traitement phyto: {obj.produit}',
        summary_template='Application de {obj.dose} sur parcelle {obj.parcelle}',
        target_field='parcelle',  # FK vers l'objet cible de la timeline
    )
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

# Registry des signaux configurés
_timeline_signal_registry = {}


def register_timeline_signal(model, event_type='system', title_template='{obj}', 
                              summary_template='', target_field=None, 
                              on_create=True, on_update=False, on_delete=False):
    """
    Enregistre un signal pour créer automatiquement des TimelineEvents.
    
    Args:
        model: Le modèle Django à surveiller
        event_type: Type d'événement (operation, document, status, etc.)
        title_template: Template pour le titre (peut utiliser {obj}, {obj.field})
        summary_template: Template pour le résumé
        target_field: Nom du champ FK vers l'objet cible (si None, c'est l'objet lui-même)
        on_create: Créer un event lors de la création
        on_update: Créer un event lors de la modification
        on_delete: Créer un event lors de la suppression
    """
    key = f"{model._meta.app_label}.{model._meta.model_name}"
    
    _timeline_signal_registry[key] = {
        'model': model,
        'event_type': event_type,
        'title_template': title_template,
        'summary_template': summary_template,
        'target_field': target_field,
        'on_create': on_create,
        'on_update': on_update,
        'on_delete': on_delete,
    }
    
    # Connecter le signal
    if on_create or on_update:
        post_save.connect(
            _timeline_post_save_handler,
            sender=model,
            dispatch_uid=f"timeline_save_{key}"
        )
    
    if on_delete:
        post_delete.connect(
            _timeline_post_delete_handler,
            sender=model,
            dispatch_uid=f"timeline_delete_{key}"
        )


def _format_template(template, obj):
    """Formate un template avec les attributs de l'objet."""
    import re
    
    def replace_match(match):
        path = match.group(1)
        value = obj
        for part in path.split('.'):
            if part == 'obj':
                continue
            value = getattr(value, part, '')
            if callable(value):
                value = value()
        return str(value) if value else ''
    
    return re.sub(r'\{(obj(?:\.[a-zA-Z_]+)*)\}', replace_match, template)


def _timeline_post_save_handler(sender, instance, created, **kwargs):
    """Handler pour post_save."""
    from apps.core.models import TimelineEvent
    
    key = f"{sender._meta.app_label}.{sender._meta.model_name}"
    config = _timeline_signal_registry.get(key)
    
    if not config:
        return
    
    # Vérifier si on doit créer l'event
    if created and not config['on_create']:
        return
    if not created and not config['on_update']:
        return
    
    # Déterminer l'objet cible
    target = instance
    if config['target_field']:
        target = getattr(instance, config['target_field'], None)
        if not target:
            return
    
    # Récupérer l'organisation
    org = getattr(target, 'organization', None) or getattr(target, 'org', None)
    if not org:
        org = getattr(instance, 'organization', None) or getattr(instance, 'org', None)
    
    if not org:
        return
    
    # Créer l'événement
    event_type = config['event_type']
    if created:
        event_type = 'creation' if event_type == 'system' else event_type
    
    title = _format_template(config['title_template'], instance)
    summary = _format_template(config['summary_template'], instance)
    
    TimelineEvent.create_for_object(
        target,
        event_type=event_type,
        title=title,
        summary=summary,
        source=instance if config['target_field'] else None,
    )


def _timeline_post_delete_handler(sender, instance, **kwargs):
    """Handler pour post_delete."""
    from apps.core.models import TimelineEvent
    
    key = f"{sender._meta.app_label}.{sender._meta.model_name}"
    config = _timeline_signal_registry.get(key)
    
    if not config or not config['on_delete']:
        return
    
    # Déterminer l'objet cible
    target = instance
    if config['target_field']:
        target = getattr(instance, config['target_field'], None)
        if not target:
            return
    
    # Récupérer l'organisation
    org = getattr(target, 'organization', None) or getattr(target, 'org', None)
    if not org:
        return
    
    title = f"Suppression: {_format_template(config['title_template'], instance)}"
    
    TimelineEvent.create_for_object(
        target,
        event_type='system',
        title=title,
        summary=f"L'élément a été supprimé",
    )


# =====================================================
# EXEMPLE D'UTILISATION POUR TRAITEMENT PHYTO
# =====================================================
# 
# Dans apps/production/apps.py ou apps/production/signals.py :
#
# from apps.core.signals import register_timeline_signal
# from apps.production.models import TraitementPhyto
# 
# register_timeline_signal(
#     TraitementPhyto,
#     event_type='operation',
#     title_template='Traitement: {obj.produit}',
#     summary_template='Application de {obj.dose} {obj.unite} sur {obj.surface} ha',
#     target_field='parcelle',
#     on_create=True,
#     on_update=False,
# )

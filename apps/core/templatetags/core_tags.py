"""
Template tags et filtres pour le module core
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def getattr(obj, attr):
    """
    Récupère un attribut d'un objet dynamiquement.
    
    Usage: {{ object|getattr:"field_name" }}
    """
    if obj is None:
        return None
    
    # Support des attributs imbriqués (ex: "user.email")
    for part in attr.split('.'):
        if obj is None:
            return None
        if hasattr(obj, part):
            obj = getattr(obj, part, None)
            if callable(obj):
                obj = obj()
        elif hasattr(obj, '__getitem__'):
            try:
                obj = obj[part]
            except (KeyError, TypeError):
                return None
        else:
            return None
    
    return obj


@register.filter
def get_item(dictionary, key):
    """
    Récupère une valeur d'un dictionnaire.
    
    Usage: {{ dict|get_item:"key" }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.simple_tag
def meta_mode_url(object, mode):
    """
    Génère l'URL pour un mode de vue meta.
    
    Usage: {% meta_mode_url object "timeline" %}
    """
    try:
        base_url = object.get_absolute_url()
        return f"{base_url}?mode={mode}"
    except AttributeError:
        return f"?mode={mode}"


@register.inclusion_tag('core/meta/partials/_mode_switch.html', takes_context=True)
def render_mode_switch(context, modes, current_mode):
    """
    Affiche le switch de modes.
    
    Usage: {% render_mode_switch modes current_mode %}
    """
    return {
        'modes': modes,
        'current_mode': current_mode,
        'request': context.get('request'),
    }


@register.filter
def event_icon(event_type):
    """
    Retourne l'icône Bootstrap pour un type d'événement.
    
    Usage: {{ event.event_type|event_icon }}
    """
    icons = {
        'operation': 'bi-gear',
        'document': 'bi-file-earmark',
        'status': 'bi-arrow-repeat',
        'note': 'bi-sticky',
        'system': 'bi-cpu',
        'link': 'bi-link-45deg',
        'creation': 'bi-plus-circle',
        'modification': 'bi-pencil',
        'alert': 'bi-exclamation-triangle',
        'analysis': 'bi-clipboard-pulse',
        'movement': 'bi-arrow-left-right',
    }
    return icons.get(event_type, 'bi-circle')


@register.filter
def event_color(event_type):
    """
    Retourne la couleur CSS pour un type d'événement.
    
    Usage: {{ event.event_type|event_color }}
    """
    colors = {
        'operation': '#3b82f6',
        'document': '#8b5cf6',
        'status': '#f59e0b',
        'note': '#10b981',
        'system': '#6b7280',
        'link': '#ec4899',
        'creation': '#22c55e',
        'modification': '#eab308',
        'alert': '#ef4444',
        'analysis': '#06b6d4',
        'movement': '#f97316',
    }
    return colors.get(event_type, '#6b7280')

"""
Template tags pour les suggestions intelligentes MonChai.
"""

from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.inclusion_tag('ai/partials/_nudge.html')
def render_nudge(nudge):
    """Affiche un nudge individuel"""
    if hasattr(nudge, 'to_dict'):
        nudge = nudge.to_dict()
    return {'nudge': nudge}


@register.inclusion_tag('ai/partials/_nudges_list.html')
def render_nudges(nudges, max_display=3):
    """Affiche une liste de nudges"""
    nudge_list = []
    for n in nudges[:max_display]:
        if hasattr(n, 'to_dict'):
            nudge_list.append(n.to_dict())
        else:
            nudge_list.append(n)
    return {
        'nudges': nudge_list,
        'total': len(nudges),
        'hidden': max(0, len(nudges) - max_display),
    }


@register.inclusion_tag('ai/partials/_weather_widget.html')
def render_weather(forecasts, parcelle_name=""):
    """Affiche le widget météo"""
    forecast_list = []
    for f in forecasts[:3]:
        if hasattr(f, '__dict__'):
            forecast_list.append({
                'date': f.date.strftime('%a %d') if hasattr(f.date, 'strftime') else str(f.date),
                'temp_min': f.temp_min,
                'temp_max': f.temp_max,
                'precipitation_mm': f.precipitation_mm,
                'precipitation_prob': f.precipitation_prob,
                'description': f.description,
                'icon': f.icon,
            })
        else:
            forecast_list.append(f)
    return {
        'forecasts': forecast_list,
        'parcelle_name': parcelle_name,
    }


@register.inclusion_tag('ai/partials/_cuve_suggestions.html')
def render_cuve_suggestions(suggestions, volume_source=0):
    """Affiche les suggestions de cuves pour soutirage/assemblage"""
    suggestion_list = []
    for s in suggestions:
        if hasattr(s, 'contenant'):
            suggestion_list.append({
                'id': s.contenant.id,
                'code': s.contenant.code,
                'type': s.contenant.get_type_display(),
                'capacite_l': float(s.contenant.capacite_l),
                'free_capacity_l': float(s.contenant.free_capacity_l()),
                'occupancy_pct': float(s.contenant.occupancy_pct),
                'fit_score': s.fit_score,
                'reason': s.reason,
                'highlight': s.highlight,
            })
    return {
        'suggestions': suggestion_list,
        'volume_source': volume_source,
        'perfect_count': sum(1 for s in suggestion_list if s['highlight'] == 'perfect'),
        'good_count': sum(1 for s in suggestion_list if s['highlight'] == 'good'),
    }


@register.inclusion_tag('ai/partials/_intrant_suggestions.html')
def render_intrant_suggestions(suggestions, operation_type=""):
    """Affiche les suggestions d'intrants basées sur l'historique"""
    return {
        'suggestions': suggestions[:5],
        'operation_type': operation_type,
    }


@register.inclusion_tag('ai/partials/_drm_reminder.html')
def render_drm_reminder(drm_status):
    """Affiche le rappel DRM dans le header"""
    return {'drm': drm_status}


@register.simple_tag
def nudge_json(nudges):
    """Retourne les nudges en JSON pour utilisation JS"""
    nudge_list = []
    for n in nudges:
        if hasattr(n, 'to_dict'):
            nudge_list.append(n.to_dict())
        else:
            nudge_list.append(n)
    return mark_safe(json.dumps(nudge_list))


@register.filter
def nudge_color(nudge_type):
    """Retourne la classe de couleur pour un type de nudge"""
    colors = {
        'info': 'text-primary',
        'suggest': 'text-success',
        'warning': 'text-warning',
        'alert': 'text-danger',
        'sparkle': 'text-warning',
    }
    return colors.get(nudge_type, 'text-secondary')


@register.filter
def nudge_bg(nudge_type):
    """Retourne la classe de background pour un type de nudge"""
    colors = {
        'info': 'bg-primary-subtle',
        'suggest': 'bg-success-subtle',
        'warning': 'bg-warning-subtle',
        'alert': 'bg-danger-subtle',
        'sparkle': 'bg-warning-subtle border-warning',
    }
    return colors.get(nudge_type, 'bg-secondary-subtle')


@register.filter
def highlight_class(highlight):
    """Retourne les classes CSS pour le highlight de cuve"""
    classes = {
        'perfect': 'border-success bg-success-subtle glow-success',
        'good': 'border-primary bg-primary-subtle',
        'possible': 'border-secondary',
        'disabled': 'border-secondary bg-secondary-subtle opacity-50',
    }
    return classes.get(highlight, '')

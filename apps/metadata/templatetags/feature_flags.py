"""
Template tags pour les feature flags
GIGA ROADMAP S2
"""

from django import template
from apps.metadata.feature_flags import FeatureFlagService

register = template.Library()


@register.filter
def search_v2_enabled(user):
    """Template filter: recherche V2 activée pour cet utilisateur"""
    if not user or not user.is_authenticated:
        return False
    return FeatureFlagService.is_enabled('search_v2_read', user=user)


@register.filter
def inline_edit_enabled(user):
    """Template filter: édition inline activée pour cet utilisateur"""
    if not user or not user.is_authenticated:
        return False
    return FeatureFlagService.is_enabled('inline_edit_v2_enabled', user=user)


@register.simple_tag
def feature_flag(flag_name, user=None, organization=None):
    """Template tag: vérifier un feature flag"""
    return FeatureFlagService.is_enabled(flag_name, user=user, organization=organization)


@register.inclusion_tag('metadata/feature_flags_debug.html')
def debug_feature_flags(user):
    """Template tag: afficher les flags de debug (dev only)"""
    if not user or not user.is_staff:
        return {'flags': []}
    
    flags = FeatureFlagService.get_enabled_flags_for_user(user)
    return {'flags': flags}

"""
Template tags pour le profil utilisateur - Roadmap 10
"""

from django import template

register = template.Library()


@register.filter
def display_name(user):
    """
    Template filter pour obtenir le nom d'affichage d'un utilisateur
    Usage: {{ user|display_name }}
    """
    try:
        # Logique de fallback directement dans le template tag
        if hasattr(user, 'profile') and user.profile.display_name:
            return user.profile.display_name
        if user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        if user.first_name:
            return user.first_name
        return user.email
    except:
        return user.email


@register.simple_tag
def user_avatar_url(user):
    """
    Template tag pour obtenir l'URL de l'avatar d'un utilisateur
    Usage: {% user_avatar_url user %}
    """
    try:
        profile = user.profile
        return profile.get_avatar_url()
    except:
        return None



"""
Service de gestion des Feature Flags
GIGA ROADMAP S0: search_v2_read, search_v2_write, inline_edit_v2_enabled
"""

from django.core.cache import cache
from .models import FeatureFlag


class FeatureFlagService:
    """Service centralisé pour les feature flags avec cache"""
    
    CACHE_PREFIX = "feature_flag"
    CACHE_TTL = 300  # 5 minutes
    
    # Flags définis dans la GIGA ROADMAP
    SEARCH_V2_READ = "search_v2_read"
    SEARCH_V2_WRITE = "search_v2_write" 
    INLINE_EDIT_V2 = "inline_edit_v2_enabled"
    
    @classmethod
    def is_enabled(cls, flag_name, user=None, organization=None):
        """
        Vérifie si un flag est activé pour un utilisateur/organisation
        Avec cache pour performance
        """
        # Clé de cache incluant user/org pour éviter les collisions
        cache_key = f"{cls.CACHE_PREFIX}:{flag_name}"
        if user:
            cache_key += f":user:{user.id}"
        if organization:
            cache_key += f":org:{organization.id}"
        
        # Vérifier le cache d'abord
        result = cache.get(cache_key)
        if result is not None:
            return result
        
        # Récupérer depuis la DB
        try:
            flag = FeatureFlag.objects.get(name=flag_name)
            
            if user:
                enabled = flag.is_enabled_for_user(user)
            elif organization:
                enabled = flag.is_enabled_for_organization(organization)
            else:
                enabled = flag.is_enabled
            
            # Mettre en cache
            cache.set(cache_key, enabled, cls.CACHE_TTL)
            return enabled
            
        except FeatureFlag.DoesNotExist:
            # Flag inexistant = désactivé par défaut
            cache.set(cache_key, False, cls.CACHE_TTL)
            return False
    
    @classmethod
    def clear_cache(cls, flag_name=None):
        """Vide le cache des flags (après modification)"""
        if flag_name:
            # Vider toutes les variantes de ce flag
            pattern = f"{cls.CACHE_PREFIX}:{flag_name}*"
            # Note: Django cache ne supporte pas les patterns, 
            # on devrait utiliser Redis directement pour ça
            pass
        else:
            # Vider tout le cache des flags
            pass
    
    @classmethod
    def get_enabled_flags_for_user(cls, user):
        """Retourne tous les flags activés pour un utilisateur"""
        flags = {}
        
        # Liste des flags à vérifier
        flag_names = [
            cls.SEARCH_V2_READ,
            cls.SEARCH_V2_WRITE,
            cls.INLINE_EDIT_V2,
        ]
        
        for flag_name in flag_names:
            flags[flag_name] = cls.is_enabled(flag_name, user=user)
        
        return flags


# Fonctions helper pour les templates et vues
def search_v2_enabled(user):
    """Helper: recherche V2 activée pour cet utilisateur"""
    return FeatureFlagService.is_enabled(
        FeatureFlagService.SEARCH_V2_READ, 
        user=user
    )

def inline_edit_enabled(user):
    """Helper: édition inline activée pour cet utilisateur"""
    return FeatureFlagService.is_enabled(
        FeatureFlagService.INLINE_EDIT_V2, 
        user=user
    )

def should_write_v2(user):
    """Helper: écrire en V2 (double-write phase)"""
    return FeatureFlagService.is_enabled(
        FeatureFlagService.SEARCH_V2_WRITE, 
        user=user
    )

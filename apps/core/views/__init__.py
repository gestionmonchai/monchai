"""
Core views - MetaDetailView et mixins réutilisables
"""

from .meta_views import (
    MetaDetailView,
    MetaDetailMixin,
    get_timeline_for_object,
    get_relations_for_object,
)

__all__ = [
    'MetaDetailView',
    'MetaDetailMixin',
    'get_timeline_for_object',
    'get_relations_for_object',
]

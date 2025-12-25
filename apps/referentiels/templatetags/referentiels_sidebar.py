from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


register = template.Library()


def _safe_url(name, *args, **kwargs):
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except Exception:
        return '#'


def _action(label, icon, href, tone='primary'):
    return {'label': label, 'icon': icon, 'href': href, 'tone': tone}


ENTITY_SWITCHER = [
    {'key': 'clients', 'label': _('Clients & contacts'), 'href': '/referentiels/clients/'},
    {'key': 'parcelles', 'label': _('Parcelles'), 'href': '/referentiels/parcelles/'},
    {'key': 'cepages', 'label': _('Cépages'), 'href': _safe_url('referentiels:cepage_list')},
    {'key': 'unites', 'label': _('Unités'), 'href': _safe_url('referentiels:unite_list')},
    {'key': 'produits', 'label': _('Produits'), 'href': _safe_url('referentiels:produit_list')},
    {'key': 'cuvees', 'label': _('Cuvées (modèles & millésimes)'), 'href': _safe_url('referentiels:cuvee_list')},
]


ENTITY_CONFIG = {
    'clients': {
        'label': _('Clients & contacts'),
        'primary': {'label': _('Nouveau client'), 'href': _safe_url('clients:customer_create'), 'icon': 'bi-person-plus-fill'},
        'quick_actions': [
            _action(_('Nouveau contact'), 'bi-person-plus', _safe_url('clients:customer_create') + '#contact'),
            _action(_('Import CSV'), 'bi-upload', '/referentiels/clients/import/', tone='warning'),
            _action(_('Exporter (CSV/Excel)'), 'bi-download', _safe_url('clients:customers_export')),
            _action(_('Segments & tags'), 'bi-tags', '/referentiels/clients/tags/', tone='secondary'),
            _action(_('Détecter doublons'), 'bi-shuffle', '/referentiels/clients/duplicates/', tone='danger'),
            _action(_('Champs personnalisés'), 'bi-sliders', '/referentiels/clients/custom-fields/', tone='secondary'),
        ],
        'used_in': [
            {'label': _('Ventes / Clients'), 'href': '/ventes/clients/'},
            {'label': _('Production / Parcelles'), 'href': '/production/parcelles/'},
            {'label': _('Compta / Tiers'), 'href': '/compta/ventes/'},
        ],
    },
    'parcelles': {
        'label': _('Parcelles'),
        'primary': {'label': _('Nouvelle parcelle'), 'href': '/production/parcelles/nouveau/', 'icon': 'bi-geo-alt-fill'},
        'quick_actions': [
            _action(_('Associer / éditer géométrie'), 'bi-bounding-box-circles', '/production/parcelles/carte/'),
            _action(_('Import parcelles (CSV)'), 'bi-upload', '/production/parcelles/import/'),
            _action(_('Gérer encépagement'), 'bi-diagram-3', '/production/parcelles/?tab=encepagement'),
            _action(_('Contrôles qualité'), 'bi-clipboard-check', '/production/parcelles/?tab=controles', tone='success'),
            _action(_('Export plan + CSV'), 'bi-download', '/production/parcelles/export/'),
            _action(_('Champs personnalisés'), 'bi-sliders', '/production/parcelles/custom-fields/'),
        ],
        'used_in': [
            {'label': _('Production / Parcelles'), 'href': '/production/parcelles/'},
            {'label': _('Vigne / Journal cultural'), 'href': '/production/journal-cultural/'},
            {'label': _('Vendanges / Réceptions'), 'href': '/production/vendanges/'},
        ],
    },
    'cepages': {
        'label': _('Cépages'),
        'primary': {'label': _('Nouveau cépage'), 'href': _safe_url('referentiels:cepage_create'), 'icon': 'bi-flower1'},
        'quick_actions': [
            _action(_('Importer depuis référentiel'), 'bi-book', _safe_url('referentiels:cepage_import_reference')),
            _action(_('Alias / synonymes'), 'bi-shuffle', '/referentiels/cepages/alias/'),
            _action(_('Associer couleurs'), 'bi-palette', '/referentiels/cepages/couleurs/'),
            _action(_('Contrôles usage'), 'bi-clipboard-check', '/referentiels/cepages/controles/', tone='success'),
            _action(_('Exporter cépages'), 'bi-download', _safe_url('referentiels:export_cepages')),
            _action(_('Champs personnalisés'), 'bi-sliders', '/referentiels/cepages/custom-fields/'),
        ],
        'used_in': [
            {'label': _('Parcelles / Encépagement'), 'href': '/production/parcelles/'},
            {'label': _('Chai / Lots techniques'), 'href': '/production/lots-techniques/'},
        ],
    },
    'unites': {
        'label': _('Unités'),
        'primary': {'label': _('Nouvelle unité'), 'href': _safe_url('referentiels:unite_create'), 'icon': 'bi-rulers'},
        'quick_actions': [
            _action(_('Sets d’unités par défaut'), 'bi-hdd-network', '/referentiels/unites/templates/'),
            _action(_('Conversions'), 'bi-arrow-left-right', '/referentiels/unites/conversions/'),
            _action(_('Verrouiller unités système'), 'bi-lock', '/referentiels/unites/lock/'),
            _action(_('Contrôles usage'), 'bi-clipboard-check', '/referentiels/unites/controles/', tone='success'),
            _action(_('Exporter unités'), 'bi-download', _safe_url('referentiels:export_unites')),
            _action(_('Champs personnalisés'), 'bi-sliders', '/referentiels/unites/custom-fields/'),
        ],
        'used_in': [
            {'label': _('Stocks & Inventaires'), 'href': '/production	inventaire/'},
            {'label': _('Achats & Ventes'), 'href': '/achats/dashboard/'},
            {'label': _('Analyses & DRM'), 'href': '/drm/'},
        ],
    },
    'produits': {
        'label': _('Produits'),
        'primary': {'label': _('Nouveau produit'), 'href': _safe_url('referentiels:produit_create'), 'icon': 'bi-box-seam'},
        'quick_actions': [
            _action(_('Catégories & familles'), 'bi-diagram-3', '/referentiels/produits/categories/'),
            _action(_('Gestion prix / grilles'), 'bi-cash-coin', _safe_url('ventes:pricelist_list')),
            _action(_('Stock & logistique'), 'bi-boxes', '/stocks/'),
            _action(_('Import catalogue'), 'bi-upload', '/referentiels/produits/import/'),
            _action(_('Export catalogue'), 'bi-download', '/referentiels/produits/export/'),
            _action(_('Contrôles qualité'), 'bi-clipboard-check', '/referentiels/produits/controles/', tone='success'),
        ],
        'used_in': [
            {'label': _('Ventes / Devis & commandes'), 'href': '/ventes/commandes/'},
            {'label': _('Achats / Commandes fourn.'), 'href': '/achats/commandes/'},
            {'label': _('Stock / Inventaire'), 'href': '/production/inventaire/'},
        ],
    },
    'cuvees': {
        'label': _('Référentiel cuvées'),
        'primary': {'label': _('Nouveau modèle de cuvée'), 'href': _safe_url('referentiels:cuvee_create'), 'icon': 'bi-droplet-half'},
        'quick_actions': [
            _action(_('Décliner en millésime'), 'bi-layers', '/referentiels/cuvees/millesimes/new/'),
            _action(_('Recette / assemblage cible'), 'bi-receipt', '/referentiels/cuvees/recette/'),
            _action(_('Gammes / segments'), 'bi-tags', '/referentiels/cuvees/gammes/'),
            _action(_('Importer historique'), 'bi-upload', '/referentiels/cuvees/import/'),
            _action(_('Exporter cuvées'), 'bi-download', '/referentiels/cuvees/export/'),
            _action(_('Contrôles cohérence'), 'bi-clipboard-check', '/referentiels/cuvees/controles/', tone='success'),
        ],
        'used_in': [
            {'label': _('Chai / Lots techniques'), 'href': '/production/lots-techniques/'},
            {'label': _('Ventes / Catalogue vins'), 'href': '/ventes/articles/'},
            {'label': _('Douanes / Registres'), 'href': '/drm/'},
        ],
    },
}


@register.simple_tag(takes_context=True)
def referentiel_sidebar_config(context, entity_key):
    entity = entity_key if entity_key in ENTITY_CONFIG else 'clients'
    cfg = ENTITY_CONFIG[entity].copy()
    cfg['entity_key'] = entity
    cfg['switcher'] = ENTITY_SWITCHER
    cfg['recent'] = (context.get('recent_items') or [])[:5]
    cfg['pinned'] = (context.get('pinned_items') or [])[:5]
    cfg['search_action'] = '/referentiels/search/'
    return cfg

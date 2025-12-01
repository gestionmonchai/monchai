from django import template
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def sort_url(request, field):
    """
    Génère une URL de tri intelligent pour une colonne
    - Premier clic : ordre par défaut (alphabétique pour texte, décroissant pour nombres)
    - Clic suivant : inverse l'ordre
    """
    # Configuration des ordres par défaut selon le type de champ
    default_orders = {
        # Champs texte : ordre alphabétique
        'nom': 'asc',
        'couleur': 'asc', 
        'classification': 'asc',
        'appellation': 'asc',
        'cuvee': 'asc',
        'entrepot': 'asc',
        'statut': 'asc',
        'numero_lot': 'asc',
        
        # Champs numériques : ordre décroissant (plus grand en premier)
        'degre_alcool': 'desc',
        'volume_initial': 'desc',
        'volume_actuel': 'desc',
        'millesime': 'desc',
        
        # Champs dates : plus récent en premier
        'created_at': 'desc',
        'updated_at': 'desc',
        'date_creation': 'desc',
    }
    
    current_sort = request.GET.get('sort', '')
    current_order = request.GET.get('order', '')
    
    # Déterminer le nouvel ordre
    if current_sort == field and current_order:
        # Inverser l'ordre actuel
        new_order = 'desc' if current_order == 'asc' else 'asc'
    else:
        # Premier clic : utiliser l'ordre par défaut
        new_order = default_orders.get(field, 'asc')
    
    # Construire l'URL avec tous les paramètres existants
    params = request.GET.copy()
    params['sort'] = field
    params['order'] = new_order
    
    return f"?{params.urlencode()}"

@register.simple_tag
def sort_icon(request, field):
    """
    Retourne l'icône de tri appropriée pour une colonne
    """
    current_sort = request.GET.get('sort', '')
    current_order = request.GET.get('order', '')
    
    if current_sort == field:
        if current_order == 'asc':
            return '<i class="bi bi-arrow-up text-primary"></i>'
        elif current_order == 'desc':
            return '<i class="bi bi-arrow-down text-primary"></i>'
    
    return '<i class="bi bi-arrow-down-up text-muted opacity-50"></i>'

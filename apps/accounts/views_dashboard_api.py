"""
API pour la configuration du dashboard personnalisable
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import UserDashboardConfig, DashboardWidget


@login_required
@require_http_methods(["POST"])
def save_dashboard_config(request):
    """
    Sauvegarde la configuration du dashboard (API unifiée pour toutes les actions)
    Actions supportées: add, remove, reorder, update
    """
    try:
        data = json.loads(request.body)
        organization = request.current_org
        
        config, created = UserDashboardConfig.objects.get_or_create(
            user=request.user,
            organization=organization
        )
        
        action = data.get('action')
        
        # Action: Ajouter un widget
        if action == 'add':
            widget_code = data.get('widget_code')
            if not widget_code:
                return JsonResponse({
                    'success': False,
                    'error': 'Code widget manquant'
                }, status=400)
            
            try:
                widget = DashboardWidget.objects.get(code=widget_code, is_active=True)
                if widget_code not in config.active_widgets:
                    config.active_widgets.append(widget_code)
                    config.save()
                    return JsonResponse({
                        'success': True,
                        'message': f'Widget "{widget.name}" ajouté'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Widget déjà présent'
                    }, status=400)
            except DashboardWidget.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Widget introuvable'
                }, status=404)
        
        # Action: Supprimer un widget
        elif action == 'remove':
            widget_code = data.get('widget_code')
            if not widget_code:
                return JsonResponse({
                    'success': False,
                    'error': 'Code widget manquant'
                }, status=400)
            
            if widget_code in config.active_widgets:
                config.active_widgets.remove(widget_code)
                config.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Widget supprimé'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Widget non trouvé dans la configuration'
                }, status=404)
        
        # Action: Réordonner les widgets
        elif action == 'reorder':
            new_order = data.get('order', [])
            valid_order = []
            for widget_code in new_order:
                if DashboardWidget.objects.filter(code=widget_code, is_active=True).exists():
                    valid_order.append(widget_code)
            
            config.active_widgets = valid_order
            config.save()
            return JsonResponse({
                'success': True,
                'message': 'Ordre des widgets mis à jour'
            })
        
        # Action: Mise à jour globale (ancienne API)
        else:
            # Mise à jour des widgets actifs
            if 'active_widgets' in data:
                valid_widgets = []
                for widget_code in data['active_widgets']:
                    if DashboardWidget.objects.filter(code=widget_code, is_active=True).exists():
                        valid_widgets.append(widget_code)
                
                config.active_widgets = valid_widgets
            
            # Mise à jour du layout
            if 'layout' in data:
                if data['layout'] in ['grid', 'list']:
                    config.layout = data['layout']
            
            # Mise à jour du nombre de colonnes
            if 'columns' in data:
                columns = int(data['columns'])
                if 1 <= columns <= 4:
                    config.columns = columns
            
            # Mise à jour des raccourcis personnalisés
            if 'custom_shortcuts' in data:
                config.custom_shortcuts = data['custom_shortcuts']
            
            config.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration sauvegardée avec succès'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_widget(request):
    """
    Ajoute un widget à la configuration
    """
    try:
        data = json.loads(request.body)
        widget_code = data.get('widget_code')
        
        if not widget_code:
            return JsonResponse({
                'success': False,
                'error': 'Code widget manquant'
            }, status=400)
        
        # Vérifier que le widget existe
        try:
            widget = DashboardWidget.objects.get(code=widget_code, is_active=True)
        except DashboardWidget.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Widget introuvable'
            }, status=404)
        
        organization = request.current_org
        config, created = UserDashboardConfig.objects.get_or_create(
            user=request.user,
            organization=organization
        )
        
        # Ajouter le widget s'il n'est pas déjà présent
        if widget_code not in config.active_widgets:
            config.active_widgets.append(widget_code)
            config.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Widget "{widget.name}" ajouté'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_widget(request):
    """
    Retire un widget de la configuration
    """
    try:
        data = json.loads(request.body)
        widget_code = data.get('widget_code')
        
        if not widget_code:
            return JsonResponse({
                'success': False,
                'error': 'Code widget manquant'
            }, status=400)
        
        organization = request.current_org
        config = UserDashboardConfig.objects.get(
            user=request.user,
            organization=organization
        )
        
        # Retirer le widget
        if widget_code in config.active_widgets:
            config.active_widgets.remove(widget_code)
            config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Widget retiré'
        })
        
    except UserDashboardConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Configuration introuvable'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reorder_widgets(request):
    """
    Réordonne les widgets
    """
    try:
        data = json.loads(request.body)
        new_order = data.get('order', [])
        
        organization = request.current_org
        config = UserDashboardConfig.objects.get(
            user=request.user,
            organization=organization
        )
        
        # Valider et appliquer le nouvel ordre
        valid_order = []
        for widget_code in new_order:
            if DashboardWidget.objects.filter(code=widget_code, is_active=True).exists():
                valid_order.append(widget_code)
        
        config.active_widgets = valid_order
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Ordre des widgets mis à jour'
        })
        
    except UserDashboardConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Configuration introuvable'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def reset_dashboard(request):
    """
    Réinitialise le dashboard à la configuration par défaut
    """
    try:
        organization = request.current_org
        
        UserDashboardConfig.objects.filter(
            user=request.user,
            organization=organization
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Dashboard réinitialisé'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

"""
API Views pour la gestion des stocks et transferts - Roadmap 32
"""

import json
import uuid
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.decorators import require_membership
from apps.viticulture.models import Lot, Warehouse
from .models import StockTransfer
from .services import StockService


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def transferts_api(request):
    """
    API pour récupérer la liste des transferts avec filtres
    GET /api/stocks/transferts?lot=&warehouse=&limit=
    """
    organization = request.current_org
    
    try:
        # Paramètres de requête
        lot_id = request.GET.get('lot')
        warehouse_id = request.GET.get('warehouse')
        limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100
        
        lot = None
        warehouse = None
        
        if lot_id:
            try:
                lot = Lot.objects.get(id=lot_id, organization=organization)
            except (Lot.DoesNotExist, ValueError):
                return JsonResponse({'error': 'Lot non trouvé'}, status=404)
        
        if warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, organization=organization)
            except (Warehouse.DoesNotExist, ValueError):
                return JsonResponse({'error': 'Entrepôt non trouvé'}, status=404)
        
        # Récupération des transferts
        transfers = StockService.get_transfer_history(
            organization=organization,
            lot=lot,
            warehouse=warehouse,
            limit=limit
        )
        
        # Sérialisation
        transfers_data = []
        for transfer in transfers:
            transfers_data.append({
                'id': str(transfer.id),
                'lot': {
                    'id': str(transfer.lot.id),
                    'code': transfer.lot.code,
                    'cuvee_name': transfer.lot.cuvee.name if hasattr(transfer.lot, 'cuvee') else None
                },
                'from_warehouse': {
                    'id': str(transfer.from_warehouse.id),
                    'name': transfer.from_warehouse.name
                },
                'to_warehouse': {
                    'id': str(transfer.to_warehouse.id),
                    'name': transfer.to_warehouse.name
                },
                'volume_l': float(transfer.volume_l),
                'notes': transfer.notes,
                'created_by': {
                    'id': transfer.created_by.id,
                    'name': transfer.created_by.get_full_name() or transfer.created_by.username
                },
                'created_at': transfer.created_at.isoformat()
            })
        
        return JsonResponse({
            'transfers': transfers_data,
            'count': len(transfers_data),
            'filters': {
                'lot': str(lot.id) if lot else None,
                'warehouse': str(warehouse.id) if warehouse else None,
                'limit': limit
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@csrf_exempt
@require_http_methods(["POST"])
def transfert_create_api(request):
    """
    API pour créer un transfert - Roadmap 32
    POST /api/stocks/transferts/create/
    Body: {
        "lot_id": "uuid",
        "from_warehouse_id": "uuid", 
        "to_warehouse_id": "uuid",
        "volume_l": 100.5,
        "client_token": "optional",
        "notes": "optional"
    }
    """
    organization = request.current_org
    
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        
        # Validation des champs requis
        required_fields = ['lot_id', 'from_warehouse_id', 'to_warehouse_id', 'volume_l']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'error': 'Champs requis manquants',
                'missing_fields': missing_fields
            }, status=400)
        
        # Récupération des objets
        try:
            lot = get_object_or_404(Lot, id=data['lot_id'], organization=organization)
            from_warehouse = get_object_or_404(Warehouse, id=data['from_warehouse_id'], organization=organization)
            to_warehouse = get_object_or_404(Warehouse, id=data['to_warehouse_id'], organization=organization)
        except Exception:
            return JsonResponse({'error': 'Lot ou entrepôt non trouvé'}, status=404)
        
        # Validation du volume
        try:
            volume_l = Decimal(str(data['volume_l']))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Volume invalide'}, status=400)
        
        # Validation métier
        validation_errors = StockService.validate_transfer_request(
            organization, lot, from_warehouse, to_warehouse, volume_l
        )
        
        if validation_errors:
            return JsonResponse({
                'error': 'Erreurs de validation',
                'validation_errors': validation_errors
            }, status=422)
        
        # Token client pour idempotence
        client_token = data.get('client_token')
        if not client_token:
            client_token = f"api_{request.user.id}_{uuid.uuid4().hex[:8]}"
        
        notes = data.get('notes', '')
        
        # Création du transfert
        with transaction.atomic():
            transfer, created = StockTransfer.create_transfer(
                organization=organization,
                lot=lot,
                from_warehouse=from_warehouse,
                to_warehouse=to_warehouse,
                volume_l=volume_l,
                user=request.user,
                client_token=client_token,
                notes=notes
            )
        
        # Réponse
        response_data = {
            'transfer': {
                'id': str(transfer.id),
                'lot': {
                    'id': str(transfer.lot.id),
                    'code': transfer.lot.code
                },
                'from_warehouse': {
                    'id': str(transfer.from_warehouse.id),
                    'name': transfer.from_warehouse.name
                },
                'to_warehouse': {
                    'id': str(transfer.to_warehouse.id),
                    'name': transfer.to_warehouse.name
                },
                'volume_l': float(transfer.volume_l),
                'notes': transfer.notes,
                'client_token': transfer.client_token,
                'created_at': transfer.created_at.isoformat()
            },
            'created': created,
            'message': 'Transfert créé avec succès' if created else 'Transfert déjà existant'
        }
        
        status_code = 201 if created else 200
        return JsonResponse(response_data, status=status_code)
        
    except ValidationError as e:
        return JsonResponse({
            'error': 'Erreur de validation',
            'details': str(e)
        }, status=422)
    
    except Exception as e:
        return JsonResponse({
            'error': 'Erreur serveur',
            'details': str(e)
        }, status=500)


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def stock_balances_api(request):
    """
    API pour récupérer les soldes de stock
    GET /api/stocks/balances?lot=&warehouse=
    """
    organization = request.current_org
    
    try:
        lot_id = request.GET.get('lot')
        warehouse_id = request.GET.get('warehouse')
        
        if lot_id:
            # Soldes d'un lot spécifique
            try:
                lot = Lot.objects.get(id=lot_id, organization=organization)
            except (Lot.DoesNotExist, ValueError):
                return JsonResponse({'error': 'Lot non trouvé'}, status=404)
            
            balances = StockService.get_lot_balances_by_warehouse(organization, lot)
            
            balances_data = []
            for warehouse, volume in balances.items():
                balances_data.append({
                    'warehouse': {
                        'id': str(warehouse.id),
                        'name': warehouse.name
                    },
                    'volume_l': float(volume)
                })
            
            return JsonResponse({
                'lot': {
                    'id': str(lot.id),
                    'code': lot.code
                },
                'balances': balances_data,
                'total_volume_l': float(sum(balances.values()))
            })
        
        elif warehouse_id:
            # Résumé d'un entrepôt spécifique
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, organization=organization)
            except (Warehouse.DoesNotExist, ValueError):
                return JsonResponse({'error': 'Entrepôt non trouvé'}, status=404)
            
            summary = StockService.get_warehouse_stock_summary(organization, warehouse)
            
            balances_data = []
            for balance in summary['balances']:
                balances_data.append({
                    'lot': {
                        'id': str(balance.lot.id),
                        'code': balance.lot.code,
                        'cuvee_name': balance.lot.cuvee.name if hasattr(balance.lot, 'cuvee') else None
                    },
                    'volume_l': float(balance.qty_l)
                })
            
            return JsonResponse({
                'warehouse': {
                    'id': str(warehouse.id),
                    'name': warehouse.name
                },
                'balances': balances_data,
                'total_volume_l': float(summary['total_volume_l']),
                'lot_count': summary['lot_count']
            })
        
        else:
            # Résumé global organisation
            summary = StockService.get_organization_stock_summary(organization)
            
            warehouses_data = []
            for warehouse_summary in summary['warehouse_summaries']:
                warehouses_data.append({
                    'warehouse': {
                        'id': str(warehouse_summary['warehouse'].id),
                        'name': warehouse_summary['warehouse'].name
                    },
                    'total_volume_l': float(warehouse_summary['total_volume_l']),
                    'lot_count': warehouse_summary['lot_count']
                })
            
            return JsonResponse({
                'organization': {
                    'id': str(organization.id),
                    'name': organization.name
                },
                'total_volume_l': float(summary['total_volume_l']),
                'warehouses': warehouses_data
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def inventaire_api(request):
    """
    API pour récupérer l'inventaire par lot ou par entrepôt - Roadmap 33
    GET /api/stocks/inventaire?mode=lot|warehouse&filters...
    """
    organization = request.current_org
    
    try:
        mode = request.GET.get('mode', 'lot')
        
        # Paramètres de filtrage
        filters = {}
        if request.GET.get('cuvee_id'):
            filters['cuvee_id'] = request.GET.get('cuvee_id')
        if request.GET.get('warehouse_id'):
            filters['warehouse_id'] = request.GET.get('warehouse_id')
        if request.GET.get('vintage_id'):
            filters['vintage_id'] = request.GET.get('vintage_id')
        if request.GET.get('status'):
            filters['status'] = request.GET.get('status')
        if request.GET.get('volume_min'):
            filters['volume_min'] = float(request.GET.get('volume_min'))
        if request.GET.get('volume_max'):
            filters['volume_max'] = float(request.GET.get('volume_max'))
        if request.GET.get('q'):
            filters['q'] = request.GET.get('q')
        
        if mode == 'warehouse':
            # Vue par entrepôt
            inventory_data = StockService.get_inventory_by_warehouse(organization, filters)
            
            warehouses_data = []
            for item in inventory_data:
                lots_data = []
                for lot_balance in item['lots_detail']:
                    lots_data.append({
                        'lot': {
                            'id': str(lot_balance.lot.id),
                            'code': lot_balance.lot.code,
                            'cuvee_name': lot_balance.lot.cuvee.name
                        },
                        'volume_l': float(lot_balance.qty_l)
                    })
                
                warehouses_data.append({
                    'warehouse': item['warehouse'],
                    'total_volume_l': float(item['total_volume_l']),
                    'lot_count': item['lot_count'],
                    'lots': lots_data
                })
            
            return JsonResponse({
                'mode': 'warehouse',
                'warehouses': warehouses_data,
                'total_warehouses': len(warehouses_data)
            })
        
        else:
            # Vue par lot (défaut)
            sort_by = request.GET.get('sort', 'volume_desc')
            limit = min(int(request.GET.get('limit', 50)), 100)
            
            inventory_data = StockService.get_inventory_by_lot(
                organization, filters, sort_by, limit
            )
            
            lots_data = []
            for balance in inventory_data:
                lots_data.append({
                    'lot': {
                        'id': str(balance.lot.id),
                        'code': balance.lot.code,
                        'cuvee': {
                            'id': str(balance.lot.cuvee.id),
                            'name': balance.lot.cuvee.name,
                            'vintage': balance.lot.cuvee.vintage.year if balance.lot.cuvee.vintage else None,
                            'appellation': balance.lot.cuvee.appellation.name if balance.lot.cuvee.appellation else None
                        },
                        'status': balance.lot_status
                    },
                    'warehouse': {
                        'id': str(balance.warehouse.id),
                        'name': balance.warehouse.name
                    },
                    'volume_l': float(balance.qty_l),
                    'last_move_date': balance.last_move_date.isoformat() if balance.last_move_date else None
                })
            
            return JsonResponse({
                'mode': 'lot',
                'lots': lots_data,
                'count': len(lots_data),
                'filters': filters,
                'sort': sort_by
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@require_http_methods(["GET"])
def inventaire_counting_api(request, warehouse_id):
    """
    API pour récupérer les lots d'un entrepôt pour comptage - Roadmap 33
    GET /api/stocks/inventaire/counting/<warehouse_id>/
    """
    organization = request.current_org
    
    try:
        lots_for_counting = StockService.get_inventory_for_counting(
            organization, warehouse_id
        )
        
        lots_data = []
        for balance in lots_for_counting:
            lots_data.append({
                'lot': {
                    'id': str(balance.lot.id),
                    'code': balance.lot.code,
                    'cuvee': {
                        'id': str(balance.lot.cuvee.id),
                        'name': balance.lot.cuvee.name,
                        'vintage': balance.lot.cuvee.vintage.year if balance.lot.cuvee.vintage else None
                    }
                },
                'current_balance': float(balance.qty_l),
                'counted_volume': 0.0  # À remplir par l'utilisateur
            })
        
        return JsonResponse({
            'warehouse_id': warehouse_id,
            'lots': lots_data,
            'total_lots': len(lots_data)
        })
    
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@csrf_exempt
@require_http_methods(["POST"])
def inventaire_calculate_adjustments_api(request):
    """
    API pour calculer les ajustements d'inventaire - Roadmap 33
    POST /api/stocks/inventaire/calculate-adjustments/
    Body: {
        "warehouse_id": "uuid",
        "counted_data": {"lot_id": volume_l, ...}
    }
    """
    organization = request.current_org
    
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        
        warehouse_id = data.get('warehouse_id')
        counted_data = data.get('counted_data', {})
        
        if not warehouse_id:
            return JsonResponse({'error': 'warehouse_id requis'}, status=400)
        
        if not counted_data:
            return JsonResponse({'error': 'counted_data requis'}, status=400)
        
        # Calculer les ajustements
        adjustments = StockService.calculate_inventory_adjustments(
            organization, warehouse_id, counted_data
        )
        
        adjustments_data = []
        for adj in adjustments:
            adjustments_data.append({
                'lot': {
                    'id': str(adj['lot'].id),
                    'code': adj['lot'].code,
                    'cuvee_name': adj['lot'].cuvee.name
                },
                'warehouse': {
                    'id': str(adj['warehouse'].id),
                    'name': adj['warehouse'].name
                },
                'current_balance': float(adj['current_balance']),
                'counted_volume': float(adj['counted_volume']),
                'adjustment': float(adj['adjustment']),
                'adjustment_type': adj['adjustment_type']
            })
        
        return JsonResponse({
            'adjustments': adjustments_data,
            'total_adjustments': len(adjustments_data),
            'warehouse_id': warehouse_id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@csrf_exempt
@require_http_methods(["POST"])
def inventaire_apply_adjustments_api(request):
    """
    API pour appliquer les ajustements d'inventaire - Roadmap 33
    POST /api/stocks/inventaire/apply-adjustments/
    Body: {
        "warehouse_id": "uuid",
        "counted_data": {"lot_id": volume_l, ...},
        "session_notes": "Notes de la session"
    }
    """
    organization = request.current_org
    
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        
        warehouse_id = data.get('warehouse_id')
        counted_data = data.get('counted_data', {})
        session_notes = data.get('session_notes', '')
        
        if not warehouse_id:
            return JsonResponse({'error': 'warehouse_id requis'}, status=400)
        
        if not counted_data:
            return JsonResponse({'error': 'counted_data requis'}, status=400)
        
        # Calculer les ajustements
        adjustments = StockService.calculate_inventory_adjustments(
            organization, warehouse_id, counted_data
        )
        
        if not adjustments:
            return JsonResponse({
                'message': 'Aucun ajustement nécessaire',
                'success_count': 0,
                'errors': []
            })
        
        # Appliquer les ajustements
        results = StockService.apply_inventory_adjustments(
            organization, adjustments, request.user, session_notes
        )
        
        moves_data = []
        for move in results['moves_created']:
            moves_data.append({
                'id': str(move.id),
                'lot_code': move.lot.code,
                'move_type': move.move_type,
                'qty_l': float(move.qty_l),
                'created_at': move.created_at.isoformat()
            })
        
        return JsonResponse({
            'message': f'{results["success_count"]} ajustements appliqués avec succès',
            'success_count': results['success_count'],
            'errors': results['errors'],
            'moves_created': moves_data
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def alertes_api(request):
    """
    API pour récupérer les alertes de stock - Roadmap 34
    GET /api/stocks/alertes?status=active&sort=criticality&filters...
    """
    organization = request.current_org
    
    try:
        from .services import StockAlertService
        
        # Paramètres de filtrage
        filters = {}
        if request.GET.get('status'):
            filters['status'] = request.GET.get('status')
        if request.GET.get('cuvee_id'):
            filters['cuvee_id'] = request.GET.get('cuvee_id')
        if request.GET.get('warehouse_id'):
            filters['warehouse_id'] = request.GET.get('warehouse_id')
        if request.GET.get('criticality'):
            filters['criticality'] = request.GET.get('criticality')
        
        # Tri
        sort_by = request.GET.get('sort', 'criticality')
        
        # Récupérer les alertes
        alerts = StockAlertService.get_alerts_list(organization, filters, sort_by)
        
        # Limiter le nombre de résultats
        limit = min(int(request.GET.get('limit', 50)), 100)
        alerts = alerts[:limit]
        
        # Sérialiser les données
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': str(alert.id),
                'lot': {
                    'id': str(alert.lot.id),
                    'code': alert.lot.code,
                    'cuvee': {
                        'id': str(alert.lot.cuvee.id),
                        'name': alert.lot.cuvee.name
                    }
                },
                'warehouse': {
                    'id': str(alert.warehouse.id),
                    'name': alert.warehouse.name
                },
                'balance_l': float(alert.balance_l),
                'threshold_l': float(alert.threshold_l),
                'threshold_source': alert.threshold_source,
                'criticality_ratio': alert.criticality_ratio,
                'days_since_first_seen': alert.days_since_first_seen,
                'first_seen_at': alert.first_seen_at.isoformat(),
                'is_active': alert.is_active,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'acknowledged_by': alert.acknowledged_by.get_full_name() if alert.acknowledged_by else None,
                'auto_resolved_at': alert.auto_resolved_at.isoformat() if alert.auto_resolved_at else None
            })
        
        # Statistiques
        active_count = StockAlertService.get_active_alerts_count(organization)
        
        return JsonResponse({
            'alerts': alerts_data,
            'count': len(alerts_data),
            'active_count': active_count,
            'filters': filters,
            'sort': sort_by
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='editor')
@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_alert_api(request):
    """
    API pour acquitter une ou plusieurs alertes - Roadmap 34
    POST /api/stocks/alertes/acknowledge/
    Body: {"alert_ids": ["uuid1", "uuid2", ...]}
    """
    organization = request.current_org
    
    try:
        from .services import StockAlertService
        
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        
        alert_ids = data.get('alert_ids', [])
        
        if not alert_ids:
            return JsonResponse({'error': 'alert_ids requis'}, status=400)
        
        if not isinstance(alert_ids, list):
            return JsonResponse({'error': 'alert_ids doit être une liste'}, status=400)
        
        # Acquitter les alertes
        count = StockAlertService.acknowledge_multiple_alerts(
            alert_ids, request.user, organization
        )
        
        return JsonResponse({
            'message': f'{count} alerte(s) acquittée(s) avec succès',
            'acknowledged_count': count
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='admin')
@csrf_exempt
@require_http_methods(["POST"])
def create_threshold_api(request):
    """
    API pour créer un seuil de stock - Roadmap 34
    POST /api/stocks/seuils/create/
    Body: {"scope": "global|cuvee|lot|warehouse", "ref_id": "uuid?", "threshold_l": 100.0, "notes": "..."}
    """
    organization = request.current_org
    
    try:
        from .models import StockThreshold
        
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        
        scope = data.get('scope')
        ref_id = data.get('ref_id')
        threshold_l = data.get('threshold_l')
        notes = data.get('notes', '')
        
        # Validation
        if not scope:
            return JsonResponse({'error': 'scope requis'}, status=400)
        
        if scope not in ['global', 'cuvee', 'lot', 'warehouse']:
            return JsonResponse({'error': 'scope invalide'}, status=400)
        
        if not threshold_l:
            return JsonResponse({'error': 'threshold_l requis'}, status=400)
        
        try:
            threshold_l = float(threshold_l)
            if threshold_l <= 0:
                return JsonResponse({'error': 'threshold_l doit être positif'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'threshold_l doit être un nombre'}, status=400)
        
        # Créer le seuil
        threshold = StockThreshold(
            organization=organization,
            scope=scope,
            ref_id=ref_id,
            threshold_l=threshold_l,
            created_by=request.user,
            notes=notes
        )
        
        # Validation métier
        threshold.full_clean()
        threshold.save()
        
        return JsonResponse({
            'message': 'Seuil créé avec succès',
            'threshold': {
                'id': str(threshold.id),
                'scope': threshold.scope,
                'ref_id': str(threshold.ref_id) if threshold.ref_id else None,
                'threshold_l': float(threshold.threshold_l),
                'notes': threshold.notes
            }
        })
    
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='admin')
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_threshold_api(request, threshold_id):
    """
    API pour supprimer un seuil de stock - Roadmap 34
    DELETE /api/stocks/seuils/<threshold_id>/
    """
    organization = request.current_org
    
    try:
        from .models import StockThreshold
        
        threshold = get_object_or_404(
            StockThreshold,
            id=threshold_id,
            organization=organization
        )
        
        threshold.delete()
        
        return JsonResponse({
            'message': 'Seuil supprimé avec succès'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_membership(role_min='read_only')
@require_http_methods(["GET"])
def alerts_badge_count_api(request):
    """
    API pour récupérer le nombre d'alertes actives pour le badge - Roadmap 34
    GET /api/stocks/alertes/badge-count/
    """
    organization = request.current_org
    
    try:
        from .services import StockAlertService
        
        count = StockAlertService.get_active_alerts_count(organization)
        
        return JsonResponse({
            'count': count
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

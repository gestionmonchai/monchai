"""
Vues UI pour l'interface utilisateur (templates Django + HTMX)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Parcelle, Vendange, Cuve, Lot, Mouvement, BouteilleLot
from .services import MouvementService, MiseEnBouteilleService


def dashboard(request):
    """Dashboard principal avec statistiques et actions rapides"""
    # Pour la démo, utiliser le premier domaine disponible
    from monchai.apps.accounts.models import Domaine
    try:
        if hasattr(request.user, 'profile') and request.user.profile.domaine:
            domaine = request.user.profile.domaine
        else:
            # Fallback pour la démo - utiliser le premier domaine
            domaine = Domaine.objects.first()
            if not domaine:
                messages.error(request, "Aucun domaine trouvé")
                return redirect('admin:index')
    except:
        domaine = Domaine.objects.first()
        if not domaine:
            messages.error(request, "Aucun domaine trouvé")
            return redirect('admin:index')
    
    # Calcul des statistiques
    stats = {}
    
    # Stock bouteilles total
    bouteille_lots = BouteilleLot.objects.filter(domaine=domaine)
    stats['stock_bouteilles'] = sum(bl.nb_bouteilles for bl in bouteille_lots)
    
    # Volume total en cuves
    lots = Lot.objects.filter(domaine=domaine)
    stats['volume_cuves'] = lots.aggregate(total=Sum('volume_disponible_hl'))['total'] or 0
    
    # Vendanges ce mois
    debut_mois = timezone.now().replace(day=1)
    vendanges_mois = Vendange.objects.filter(
        parcelle__domaine=domaine,
        date__gte=debut_mois
    )
    stats['vendanges_mois'] = vendanges_mois.aggregate(total=Sum('volume_hl'))['total'] or 0
    
    # Mouvements en attente
    stats['mouvements_draft'] = Mouvement.objects.filter(
        domaine=domaine,
        status='draft'
    ).count()
    
    # Activité récente (10 derniers mouvements)
    recent_mouvements = Mouvement.objects.filter(domaine=domaine).order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_mouvements': recent_mouvements,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def vendange_wizard(request):
    """Wizard pour créer une nouvelle vendange"""
    domaine = request.user.profile.domaine
    
    if request.method == 'POST':
        try:
            # Créer la vendange
            parcelle_id = request.POST.get('parcelle_id')
            parcelle = get_object_or_404(Parcelle, id=parcelle_id, domaine=domaine)
            
            vendange = Vendange.objects.create(
                parcelle=parcelle,
                date=request.POST.get('date'),
                volume_hl=Decimal(request.POST.get('volume_hl')),
                dechets_hl=Decimal(request.POST.get('dechets_hl', 0)),
                commentaire=request.POST.get('commentaire', '')
            )
            
            # Si une cuve est sélectionnée, créer le mouvement
            cuve_id = request.POST.get('cuve_id')
            if cuve_id:
                mouvement = MouvementService.create_vendange_vers_cuve(
                    vendange_id=vendange.id,
                    destination_cuve_id=cuve_id,
                    date=vendange.date
                )
                # Auto-valider le mouvement
                MouvementService.valider_mouvement(mouvement.id)
                messages.success(request, f"Vendange créée et mouvement vers cuve validé ({mouvement.volume_hl} hl)")
            else:
                messages.success(request, "Vendange créée avec succès")
            
            return JsonResponse({'success': True, 'redirect': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET - Afficher le formulaire
    parcelles = Parcelle.objects.filter(domaine=domaine)
    cuves = Cuve.objects.filter(domaine=domaine)
    
    context = {
        'parcelles': parcelles,
        'cuves': cuves,
    }
    
    return render(request, 'core/vendange_wizard.html', context)


@login_required
def mouvement_inter_cuves(request):
    """Formulaire pour mouvement inter-cuves"""
    domaine = request.user.profile.domaine
    
    if request.method == 'POST':
        try:
            mouvement = MouvementService.create_inter_cuves(
                source_lot_id=request.POST.get('source_lot_id'),
                destination_cuve_id=request.POST.get('destination_cuve_id'),
                volume_hl=Decimal(request.POST.get('volume_hl')),
                date=request.POST.get('date'),
                commentaire=request.POST.get('commentaire', ''),
                domaine=domaine
            )
            
            # Auto-valider si demandé
            if request.POST.get('auto_valider'):
                MouvementService.valider_mouvement(mouvement.id)
                messages.success(request, f"Mouvement inter-cuves créé et validé ({mouvement.volume_hl} hl)")
            else:
                messages.success(request, f"Mouvement inter-cuves créé en brouillon ({mouvement.volume_hl} hl)")
            
            return JsonResponse({'success': True, 'redirect': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET - Afficher le formulaire
    lots = Lot.objects.filter(domaine=domaine, volume_disponible_hl__gt=0).select_related('cuve')
    cuves = Cuve.objects.filter(domaine=domaine)
    
    context = {
        'lots': lots,
        'cuves': cuves,
    }
    
    return render(request, 'core/mouvement_inter_cuves.html', context)


@login_required
def mise_en_bouteille_form(request):
    """Formulaire pour mise en bouteille"""
    domaine = request.user.profile.domaine
    
    if request.method == 'POST':
        try:
            mouvement, bouteille_lot = MiseEnBouteilleService.executer_mise_en_bouteille(
                source_lot_id=request.POST.get('source_lot_id'),
                nb_bouteilles=int(request.POST.get('nb_bouteilles')),
                contenance_ml=int(request.POST.get('contenance_ml')),
                taux_perte_hl=Decimal(request.POST.get('taux_perte_hl', 0)),
                date=request.POST.get('date'),
                domaine=domaine
            )
            
            messages.success(request, 
                f"Mise en bouteille réalisée : {bouteille_lot.nb_bouteilles} bouteilles de {bouteille_lot.contenance_ml}ml")
            
            return JsonResponse({'success': True, 'redirect': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET - Afficher le formulaire
    lots = Lot.objects.filter(domaine=domaine, volume_disponible_hl__gt=0).select_related('cuve')
    
    context = {
        'lots': lots,
    }
    
    return render(request, 'core/mise_en_bouteille_form.html', context)


@login_required
def parcelles_list(request):
    """Liste des parcelles"""
    domaine = request.user.profile.domaine
    parcelles = Parcelle.objects.filter(domaine=domaine)
    
    context = {
        'parcelles': parcelles,
    }
    
    return render(request, 'core/parcelles_list.html', context)


@login_required
def vendanges_list(request):
    """Liste des vendanges"""
    domaine = request.user.profile.domaine
    vendanges = Vendange.objects.filter(parcelle__domaine=domaine).select_related('parcelle').order_by('-date')
    
    context = {
        'vendanges': vendanges,
    }
    
    return render(request, 'core/vendanges_list.html', context)


@login_required
def cuves_list(request):
    """Liste des cuves avec leurs lots"""
    domaine = request.user.profile.domaine
    cuves = Cuve.objects.filter(domaine=domaine).prefetch_related('lots')
    
    context = {
        'cuves': cuves,
    }
    
    return render(request, 'core/cuves_list.html', context)


@login_required
def mouvements_list(request):
    """Liste des mouvements"""
    domaine = request.user.profile.domaine
    mouvements = Mouvement.objects.filter(domaine=domaine).select_related(
        'source_lot__cuve', 'destination_cuve'
    ).order_by('-created_at')
    
    context = {
        'mouvements': mouvements,
    }
    
    return render(request, 'core/mouvements_list.html', context)


@login_required
def valider_mouvement(request, mouvement_id):
    """Valider un mouvement via HTMX"""
    if request.method == 'POST':
        try:
            mouvement = get_object_or_404(Mouvement, id=mouvement_id, domaine=request.user.profile.domaine)
            mouvement_valide = MouvementService.valider_mouvement(mouvement.id)
            
            return JsonResponse({
                'success': True, 
                'message': f'Mouvement validé ({mouvement_valide.volume_hl} hl)',
                'new_status': mouvement_valide.status
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

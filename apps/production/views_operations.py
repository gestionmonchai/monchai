"""
Vues pour la gestion des opérations de cave (vinification, élevage, etc.)
Formulaires spécialisés par type d'opération avec création d'alertes intégrée.
"""
from __future__ import annotations
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from datetime import timedelta
from decimal import Decimal
import json

from apps.production.models import LotTechnique
from apps.viticulture.models import Lot as VitiLot, Warehouse, Cuvee as VitiCuvee, UnitOfMeasure
from apps.viticulture.models_extended import LotIntervention, LotMeasurement
from apps.production.models_alerts import Alert


# Mapping des icônes par type d'opération
OPERATION_ICONS = {
    'pressurage': '🍇',
    'debourbage': '🧊',
    'enzymage': '🧪',
    'sulfitage_preferm': '⚗️',
    'inoculation_levures': '🦠',
    'debut_fa': '▶️',
    'chaptalisation': '🍬',
    'remontage': '🔄',
    'pigeage': '👊',
    'delestage': '⬇️',
    'controle_densite_temp': '🌡️',
    'fin_fa': '⏹️',
    'ecoulage': '🚿',
    'pressurage_marc': '🍷',
    'inoculation_bacteries': '🦠',
    'debut_fml': '▶️',
    'fin_fml': '⏹️',
    'soutirage': '↕️',
    'ouillage': '💧',
    'batonnage': '🥄',
    'so2': '⚗️',
    'collage': '🧹',
    'filtration': '🔬',
    'stabilisation_tartrique': '❄️',
    'correction_acidite': '⚖️',
    'analyse_labo': '🔬',
    'degustation': '🍷',
    'autre': '📝',
}


def _ensure_viti_lot_for_lottech(lottech: LotTechnique) -> VitiLot:
    """Garantit un Lot (viticulture) lié à un LotTechnique."""
    if lottech.external_lot_id:
        try:
            return VitiLot.objects.get(id=lottech.external_lot_id)
        except VitiLot.DoesNotExist:
            pass
    
    org = lottech.cuvee.organization if lottech.cuvee_id else None
    wh = Warehouse.objects.filter(organization=org).order_by('name').first()
    if not wh:
        wh = Warehouse.objects.create(organization=org, name='Principal')
    
    # Trouver ou créer la cuvée viticulture correspondante
    # lottech.cuvee est une referentiels.Cuvee, on cherche une viticulture.Cuvee équivalente
    viti_cuvee = None
    if lottech.cuvee_id:
        ref_cuvee = lottech.cuvee
        # Chercher par nom dans la même organisation
        viti_cuvee = VitiCuvee.objects.filter(
            organization=org,
            name=ref_cuvee.nom
        ).first()
        if not viti_cuvee:
            # Créer une cuvée viticulture correspondante
            default_uom = UnitOfMeasure.objects.filter(organization=org).first()
            if not default_uom:
                default_uom = UnitOfMeasure.objects.create(
                    organization=org,
                    name='Litre',
                    code='L',
                    unit_type='volume'
                )
            viti_cuvee = VitiCuvee.objects.create(
                organization=org,
                name=ref_cuvee.nom,
                code=getattr(ref_cuvee, 'code', '') or '',
                default_uom=default_uom
            )
    
    if not viti_cuvee:
        raise ValueError("Impossible de créer le lot: aucune cuvée associée au lot technique.")
    
    vlot = VitiLot.objects.create(
        organization=org,
        code=lottech.code,
        cuvee=viti_cuvee,
        warehouse=wh,
        volume_l=lottech.volume_l or 0,
        status='elevage',
    )
    lottech.external_lot_id = vlot.id
    lottech.save(update_fields=['external_lot_id'])
    return vlot


@method_decorator(login_required, name='dispatch')
class OperationListView(ListView):
    """Liste des opérations avec filtres."""
    template_name = 'production/vinification_home.html'
    context_object_name = 'operations'
    paginate_by = 50
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        if not org:
            return LotIntervention.objects.none()
        
        qs = LotIntervention.objects.filter(
            organization=org
        ).select_related('lot', 'lot__cuvee').order_by('-date', '-created_at')
        
        # Filtres
        type_filter = self.request.GET.get('type')
        if type_filter:
            qs = qs.filter(type=type_filter)
        
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                models.Q(lot__code__icontains=q) |
                models.Q(notes__icontains=q)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Journal des opérations'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Journal opérations', 'url': None},
        ]
        
        # Lots pour le formulaire
        if org:
            ctx['lots'] = LotTechnique.objects.filter(
                cuvee__organization=org
            ).select_related('cuvee').order_by('-created_at')
        
        # Statistiques
        if org:
            total = LotIntervention.objects.filter(organization=org).count()
            this_month = LotIntervention.objects.filter(
                organization=org,
                date__gte=timezone.now().date().replace(day=1)
            ).count()
            ctx['stats'] = {
                'total': total,
                'this_month': this_month,
            }
        
        return ctx


@method_decorator(login_required, name='dispatch')
class OperationCreateView(View):
    """Création d'une nouvelle opération avec formulaire spécialisé."""
    template_name = 'production/operation_form.html'
    
    def get(self, request):
        org = getattr(request, 'current_org', None)
        
        lots = LotTechnique.objects.filter(
            cuvee__organization=org
        ).select_related('cuvee').order_by('-created_at') if org else []
        
        # Pré-sélection du lot si passé en paramètre
        selected_lot = request.GET.get('lot')
        
        return render(request, self.template_name, {
            'lots': lots,
            'selected_lot': selected_lot,
            'today': timezone.now().date().isoformat(),
            'page_title': 'Nouvelle opération',
        })
    
    def post(self, request):
        org = getattr(request, 'current_org', None)
        if not org:
            messages.error(request, "Organisation non trouvée.")
            return redirect('production:vinification_home')
        
        # Récupérer les données
        lot_id = request.POST.get('lot_id')
        op_type = request.POST.get('type')
        op_date = request.POST.get('date')
        notes = request.POST.get('notes', '')
        
        if not lot_id or not op_type or not op_date:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect('production:operation_create')
        
        # Récupérer le lot technique et créer/obtenir le lot viticulture
        try:
            lottech = LotTechnique.objects.get(id=lot_id)
            viti_lot = _ensure_viti_lot_for_lottech(lottech)
        except LotTechnique.DoesNotExist:
            messages.error(request, "Lot introuvable.")
            return redirect('production:operation_create')
        
        # Construire les notes avec les paramètres spécifiques
        details = self._collect_specific_fields(request, op_type)
        if details:
            notes_parts = [notes] if notes else []
            for key, value in details.items():
                if value:
                    notes_parts.append(f"{key}: {value}")
            notes = " | ".join(notes_parts)
        
        # Créer l'intervention
        intervention = LotIntervention.objects.create(
            lot=viti_lot,
            type=op_type,
            date=op_date,
            notes=notes,
            organization=org
        )
        
        # Créer une alerte si demandé
        if request.POST.get('create_alert'):
            alert_delay = int(request.POST.get('alert_delay', 3))
            alert_message = request.POST.get('alert_message', f"Suivi {intervention.get_type_display()}")
            
            Alert.objects.create(
                organization=org,
                title=alert_message,
                description=f"Suite à l'opération de {intervention.get_type_display()} du {op_date} sur lot {viti_lot.code}",
                alert_type='reminder',
                category='vinification',
                priority='medium',
                due_date=timezone.now().date() + timedelta(days=alert_delay),
                created_by=request.user,
            )
            messages.success(request, f"Opération créée avec alerte programmée dans {alert_delay} jours.")
        else:
            messages.success(request, f"Opération '{intervention.get_type_display()}' créée avec succès.")
        
        return redirect('production:vinification_home')
    
    def _collect_specific_fields(self, request, op_type):
        """Collecte les champs spécifiques selon le type d'opération."""
        details = {}
        
        if op_type == 'debourbage':
            if request.POST.get('duree_h'):
                details['Durée'] = f"{request.POST.get('duree_h')}h"
            if request.POST.get('temperature'):
                details['Température'] = f"{request.POST.get('temperature')}°C"
            if request.POST.get('methode_debourbage'):
                details['Méthode'] = request.POST.get('methode_debourbage')
        
        elif op_type == 'inoculation_levures':
            if request.POST.get('souche_levure'):
                details['Souche'] = request.POST.get('souche_levure')
            if request.POST.get('dose_levure'):
                details['Dose'] = f"{request.POST.get('dose_levure')} g/hL"
            if request.POST.get('fournisseur_levure'):
                details['Fournisseur'] = request.POST.get('fournisseur_levure')
        
        elif op_type == 'chaptalisation':
            if request.POST.get('qte_sucre_kg'):
                details['Sucre'] = f"{request.POST.get('qte_sucre_kg')} kg"
            if request.POST.get('type_sucre'):
                details['Type'] = request.POST.get('type_sucre')
            if request.POST.get('gain_alcool'):
                details['Gain alcool'] = f"+{request.POST.get('gain_alcool')}% vol"
        
        elif op_type in ['remontage', 'pigeage', 'delestage']:
            if request.POST.get('duree_min'):
                details['Durée'] = f"{request.POST.get('duree_min')} min"
            if request.POST.get('nb_cycles'):
                details['Cycles'] = request.POST.get('nb_cycles')
            if request.POST.get('aeration'):
                details['Aération'] = request.POST.get('aeration')
        
        elif op_type in ['controle_densite_temp', 'debut_fa', 'fin_fa']:
            if request.POST.get('densite'):
                details['Densité'] = request.POST.get('densite')
            if request.POST.get('temperature'):
                details['T°'] = f"{request.POST.get('temperature')}°C"
            if request.POST.get('sucres_residuels'):
                details['SR'] = f"{request.POST.get('sucres_residuels')} g/L"
        
        elif op_type in ['so2', 'sulfitage_preferm']:
            if request.POST.get('dose_so2'):
                details['Dose SO₂'] = f"{request.POST.get('dose_so2')} g/hL"
            if request.POST.get('forme_so2'):
                details['Forme'] = request.POST.get('forme_so2')
            if request.POST.get('so2_libre_vise'):
                details['SO₂ libre visé'] = f"{request.POST.get('so2_libre_vise')} mg/L"
        
        elif op_type in ['inoculation_bacteries', 'debut_fml', 'fin_fml']:
            if request.POST.get('souche_bacteries'):
                details['Souche'] = request.POST.get('souche_bacteries')
            if request.POST.get('acide_malique'):
                details['Ac. malique'] = f"{request.POST.get('acide_malique')} g/L"
            if request.POST.get('acide_lactique'):
                details['Ac. lactique'] = f"{request.POST.get('acide_lactique')} g/L"
        
        elif op_type == 'collage':
            if request.POST.get('produit_collage'):
                details['Produit'] = request.POST.get('produit_collage')
            if request.POST.get('dose_collage'):
                details['Dose'] = f"{request.POST.get('dose_collage')} g/hL"
            if request.POST.get('duree_collage'):
                details['Durée'] = f"{request.POST.get('duree_collage')} jours"
        
        elif op_type == 'filtration':
            if request.POST.get('type_filtration'):
                details['Type'] = request.POST.get('type_filtration')
            if request.POST.get('porosite'):
                details['Porosité'] = f"{request.POST.get('porosite')} µm"
        
        elif op_type == 'ouillage':
            if request.POST.get('volume_ouillage'):
                details['Volume ajouté'] = f"{request.POST.get('volume_ouillage')} L"
        
        return details


@method_decorator(login_required, name='dispatch')
class OperationDetailView(View):
    """Détail d'une opération."""
    template_name = 'production/operation_detail.html'
    
    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        
        operation = get_object_or_404(
            LotIntervention.objects.select_related('lot', 'lot__cuvee'),
            id=pk,
            organization=org
        )
        
        # Ajouter l'icône
        operation.type_icon = OPERATION_ICONS.get(operation.type, '📝')
        
        # Historique récent du lot (5 dernières opérations)
        recent_operations = LotIntervention.objects.filter(
            lot=operation.lot
        ).order_by('-date')[:6]
        
        return render(request, self.template_name, {
            'operation': operation,
            'recent_operations': recent_operations,
            'page_title': f"{operation.get_type_display()} - {operation.lot.code}",
        })


@method_decorator(login_required, name='dispatch')
class OperationEditView(View):
    """Modification d'une opération."""
    template_name = 'production/operation_form.html'
    
    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        
        operation = get_object_or_404(
            LotIntervention,
            id=pk,
            organization=org
        )
        
        lots = LotTechnique.objects.filter(
            cuvee__organization=org
        ).select_related('cuvee').order_by('-created_at') if org else []
        
        return render(request, self.template_name, {
            'operation': operation,
            'lots': lots,
            'today': timezone.now().date().isoformat(),
            'page_title': f"Modifier {operation.get_type_display()}",
        })
    
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        
        operation = get_object_or_404(
            LotIntervention,
            id=pk,
            organization=org
        )
        
        # Mise à jour
        operation.type = request.POST.get('type', operation.type)
        operation.date = request.POST.get('date', operation.date)
        operation.notes = request.POST.get('notes', operation.notes)
        operation.save()
        
        messages.success(request, "Opération mise à jour.")
        return redirect('production:operation_detail', pk=operation.id)


@method_decorator(login_required, name='dispatch')
class OperationDeleteView(View):
    """Suppression d'une opération."""
    
    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        
        operation = get_object_or_404(
            LotIntervention,
            id=pk,
            organization=org
        )
        
        operation.delete()
        messages.success(request, "Opération supprimée.")
        return redirect('production:vinification_home')


@method_decorator(login_required, name='dispatch')
class AlertFromOperationView(View):
    """Créer une alerte à partir d'une opération."""
    
    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        
        operation = get_object_or_404(
            LotIntervention,
            id=pk,
            organization=org
        )
        
        title = request.POST.get('title', f"Suivi {operation.get_type_display()}")
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date')
        
        alert = Alert.objects.create(
            organization=org,
            title=title,
            description=description,
            alert_type='reminder',
            category='vinification',
            priority=priority,
            due_date=due_date,
            created_by=request.user,
        )
        
        messages.success(request, f"Alerte '{title}' créée avec succès.")
        return redirect('production:operation_detail', pk=pk)

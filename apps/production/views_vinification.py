from __future__ import annotations
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal

from apps.production.models import LotTechnique
from apps.viticulture.models import Lot as VitiLot, Warehouse
from apps.viticulture.models_extended import LotIntervention, LotMeasurement
from .forms_vinification import VinificationOperationForm

# Mapping des icônes par type d'opération
OPERATION_ICONS = {
    'pressurage': '🍇', 'debourbage': '🧊', 'enzymage': '🧪', 'sulfitage_preferm': '⚗️',
    'inoculation_levures': '🦠', 'debut_fa': '▶️', 'chaptalisation': '🍬',
    'remontage': '🔄', 'pigeage': '👊', 'delestage': '⬇️', 'controle_densite_temp': '🌡️',
    'fin_fa': '⏹️', 'ecoulage': '🚿', 'pressurage_marc': '🍷',
    'inoculation_bacteries': '🦠', 'debut_fml': '▶️', 'fin_fml': '⏹️',
    'soutirage': '↕️', 'ouillage': '💧', 'batonnage': '🥄', 'so2': '⚗️',
    'collage': '🧹', 'filtration': '🔬', 'stabilisation_tartrique': '❄️',
    'correction_acidite': '⚖️', 'analyse_labo': '🔬', 'degustation': '🍷', 'autre': '📝',
}

def _ensure_viti_lot_for_lottech(lottech: LotTechnique) -> VitiLot:
    """Garantit un Lot (viticulture) lié à un LotTechnique via external_lot_id.
    Crée le Lot si nécessaire en copiant code/cuvée/volume, et en choisissant un entrepôt.
    """
    if lottech.external_lot_id:
        try:
            return VitiLot.objects.get(id=lottech.external_lot_id)
        except VitiLot.DoesNotExist:
            pass
    org = lottech.cuvee.organization if lottech.cuvee_id else None
    wh = Warehouse.objects.filter(organization=org).order_by('name').first()
    if not wh:
        wh = Warehouse.objects.create(organization=org, name='Principal')
    vlot = VitiLot.objects.create(
        organization=org,
        code=lottech.code,
        cuvee=lottech.cuvee,
        warehouse=wh,
        volume_l=lottech.volume_l,
        status='elevage',
    )
    lottech.external_lot_id = vlot.id
    lottech.save(update_fields=['external_lot_id'])
    return vlot

@method_decorator(login_required, name='dispatch')
class VinificationHomeView(TemplateView):
    template_name = 'production/vinification_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Vinification'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Vinification', 'url': None},
        ]
        
        if not org:
            return ctx

        # Initialiser le formulaire
        form = VinificationOperationForm(organization=org)
        ctx['form'] = form

        # Récupérer TOUTES les opérations de cave
        # (tous types : vinification, élevage, stabilisation)
        interventions = LotIntervention.objects.filter(
            organization=org
        ).select_related('lot', 'lot__cuvee').order_by('-date')

        # Mesures pertinentes
        meas_types = ['densite', 'temperature']
        measurements = LotMeasurement.objects.filter(
            lot__organization=org,
            type__in=meas_types
        ).select_related('lot')

        # Fusionner et trier
        operations = []
        for i in interventions:
            operations.append({
                'date': i.date,
                'lot': i.lot,
                'type_display': i.get_type_display(),
                'type_code': i.type,
                'type_icon': OPERATION_ICONS.get(i.type, '📝'),
                'valeur': i.volume_in_l or i.volume_out_l or '',
                'notes': i.notes,
                'source': 'intervention',
                'obj': i
            })
        
        for m in measurements:
            d = m.date.date() if hasattr(m.date, 'date') else m.date
            operations.append({
                'date': d,
                'lot': m.lot,
                'type_display': m.get_type_display(),
                'type_code': m.type,
                'type_icon': '🌡️' if m.type == 'temperature' else '📊',
                'valeur': f"{m.value} {m.unit}",
                'notes': m.notes,
                'source': 'measurement',
                'obj': m
            })

        # Trier par date décroissante
        operations.sort(key=lambda x: x['date'], reverse=True)
        
        # Mapper VitiLot -> LotTechnique code si possible (via external_lot_id inverse ? ou juste afficher le code du VitiLot qui est le même)
        # Le VitiLot.code est copié du LotTechnique.code, donc ça va.
        
        ctx['operations'] = operations
        return ctx

@method_decorator(login_required, name='dispatch')
class VinificationOperationCreateView(View):
    def post(self, request):
        org = getattr(request, 'current_org', None)
        if not org:
            return redirect('production:vinification_home')
            
        form = VinificationOperationForm(request.POST, organization=org)
        if form.is_valid():
            data = form.cleaned_data
            lot_tech = data['lot_id']
            date = data['date']
            type_op = data['type']
            notes = data['comment'] or ''
            
            # Assurer le lot viti
            vlot = _ensure_viti_lot_for_lottech(lot_tech)
            
            # Traitement des champs conditionnels pour construire les notes enrichies
            extra_info = []
            
            if data.get('volume_concerne'):
                extra_info.append(f"Vol: {data['volume_concerne']}L")
            
            if data.get('duree_heures'):
                extra_info.append(f"Durée: {data['duree_heures']}h")
                
            if data.get('temperature'):
                # Si c'est une mesure de température seule
                if type_op == 'controle_densite_temp' and not data.get('densite'):
                     # On créera une mesure, pas une intervention
                     pass
                else:
                    extra_info.append(f"T°: {data['temperature']}°C")
            
            if data.get('produit'):
                extra_info.append(f"Produit: {data['produit']}")
            if data.get('dose'):
                extra_info.append(f"Dose: {data['dose']}")
                
            if data.get('quantite_sucre'):
                extra_info.append(f"Sucre: {data['quantite_sucre']}kg")
                
            if data.get('correction_type'):
                extra_info.append(f"Type: {data['correction_type']}")
                
            if data.get('action_mecanique'):
                extra_info.append(f"Action: {data['action_mecanique']}")
            if data.get('nb_cycles'):
                extra_info.append(f"Cycles: {data['nb_cycles']}")
                
            full_notes = (notes + " " + " | ".join(extra_info)).strip()
            
            # Création de l'objet
            if type_op == 'controle_densite_temp':
                # Créer des mesures
                created = False
                if data.get('densite'):
                    LotMeasurement.objects.create(
                        lot=vlot,
                        organization=org,
                        date=timezone.now(), # On utilise now() car measurement est datetime, mais on pourrait utiliser data['date'] combiné
                        type='densite',
                        value=data['densite'],
                        unit='',
                        notes=full_notes
                    )
                    created = True
                if data.get('temperature'):
                    LotMeasurement.objects.create(
                        lot=vlot,
                        organization=org,
                        date=timezone.now(),
                        type='temperature',
                        value=data['temperature'],
                        unit='°C',
                        notes=full_notes
                    )
                    created = True
                if created:
                    messages.success(request, "Mesures enregistrées")
            else:
                # Créer une intervention
                # Mapping du type form -> type model si différent (ici ils correspondent ou presque)
                # correction_acidite -> correction (ou acidification/desacidification si on voulait être précis, mais 'correction' est générique)
                # Si correction_type est spécifié, on peut affiner le type model ?
                model_type = type_op
                if type_op == 'correction_acidite':
                    if data.get('correction_type') == 'acidification':
                        model_type = 'acidification'
                    elif data.get('correction_type') == 'desacidification':
                        model_type = 'correction' # Pas de desacidification explicite dans choices, use correction
                    else:
                        model_type = 'correction'
                
                LotIntervention.objects.create(
                    lot=vlot,
                    organization=org,
                    date=date,
                    type=model_type,
                    notes=full_notes,
                    volume_in_l=data.get('volume_concerne')
                )
                messages.success(request, f"Opération {type_op} enregistrée")
        else:
            for field, err in form.errors.items():
                messages.error(request, f"{field}: {err}")
        
        return redirect('production:vinification_home')

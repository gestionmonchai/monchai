from __future__ import annotations
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from apps.production.models import LotTechnique, Operation, MouvementLot, LotLineage
from .forms_soutirage import SoutirageForm
from .services_stock import move_vrac

def get_soutirages_list(org, params=None):
    ops = Operation.objects.filter(
        organization=org,
        kind='soutirage'
    ).order_by('-date')

    # Basic SQL filtering where possible (e.g. date range if added later)
    # params = params or {}
    # ...

    soutirages_list = []
    for op in ops:
        # Récupérer les détails depuis meta ou lineage
        lot_src_id = op.meta.get('lot_source_id')
        lot_dst_id = op.meta.get('lot_dest_id')
        
        lot_src = None
        lot_dst = None
        if lot_src_id:
            lot_src = LotTechnique.objects.filter(pk=lot_src_id).first()
        if lot_dst_id:
            lot_dst = LotTechnique.objects.filter(pk=lot_dst_id).first()
        
        # Si lineage existe
        if not lot_src or not lot_dst:
            lineage = op.lineages.first()
            if lineage:
                lot_src = lineage.parent_lot
                lot_dst = lineage.child_lot

        soutirages_list.append({
            'date': op.date,
            'lot_source': lot_src,
            'lot_dest': lot_dst,
            'contenant_dep': op.meta.get('contenant_depart', ''),
            'contenant_arr': op.meta.get('contenant_arrivee', ''),
            'volume': op.meta.get('volume_soutire', 0),
            'motif': op.meta.get('motif_display', op.meta.get('motif', '-')),
            'perte': op.meta.get('perte_estimee', 0),
            'notes': op.meta.get('notes', '')
        })

    # Python-side filtering for JSON/Related fields
    if params:
        q = (params.get('q') or '').strip().lower()
        if q:
            filtered = []
            for item in soutirages_list:
                # Match against: lot_source.code, lot_dest.code, notes, motif
                match = False
                if item['lot_source'] and q in item['lot_source'].code.lower(): match = True
                elif item['lot_dest'] and q in item['lot_dest'].code.lower(): match = True
                elif q in str(item['notes']).lower(): match = True
                elif q in str(item['motif']).lower(): match = True
                
                if match:
                    filtered.append(item)
            soutirages_list = filtered

    return soutirages_list

@method_decorator(login_required, name='dispatch')
class SoutirageHomeView(TemplateView):
    template_name = 'production/soutirages_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Soutirages'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Soutirages', 'url': None},
        ]
        
        if not org:
            return ctx

        # Formulaire pour modal
        ctx['form'] = SoutirageForm(organization=org)

        # Liste des opérations de soutirage (initial load)
        ctx['soutirages'] = get_soutirages_list(org)
        return ctx

@method_decorator(login_required, name='dispatch')
class SoutirageTableView(TemplateView):
    template_name = 'production/_soutirages_table.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        params = self.request.GET.copy()
        if org:
            ctx['soutirages'] = get_soutirages_list(org, params=params)
        return ctx

@method_decorator(login_required, name='dispatch')
class SoutirageCreateView(View):
    @transaction.atomic
    def post(self, request):
        org = getattr(request, 'current_org', None)
        if not org:
            return redirect('production:soutirages_list')
            
        form = SoutirageForm(request.POST, organization=org)
        if form.is_valid():
            data = form.cleaned_data
            lot_src = data['lot_id']
            date = data['date']
            cont_arr = data['contenant_arrivee']
            vol = data['volume_soutire']
            motif = data['motif']
            perte = data['perte_estimee'] or Decimal('0')
            notes = data['comment'] or ''
            
            # Logique : Soutirage "simple" (même lot ou transfert vers lui-même mais changement de contenant)
            # Pour la V1, on considère que le soutirage met à jour le lot source (contenant, volume - perte)
            # Ou bien on crée un nouveau lot ?
            # "Lot destination (ou même lot, mais autre contenant)"
            # Si on garde le même lot, on change juste son contenant et on réduit le volume de la perte.
            
            # On va simplifier : On garde le même lot ID, on met à jour le contenant et on enregistre la perte.
            # Si l'utilisateur voulait scinder, il utiliserait assemblage/transfert ou on complexifierait.
            # Ici : update lot in place.
            
            contenant_dep = lot_src.contenant
            
            # Enregistrer l'opération
            op = Operation.objects.create(
                organization=org,
                kind='soutirage',
                date=date,
                meta={
                    'lot_source_id': str(lot_src.id),
                    'lot_dest_id': str(lot_src.id), # Même lot
                    'contenant_depart': contenant_dep,
                    'contenant_arrivee': cont_arr,
                    'volume_soutire': str(vol),
                    'perte_estimee': str(perte),
                    'motif': motif,
                    'motif_display': dict(form.fields['motif'].choices).get(motif, motif),
                    'notes': notes
                }
            )
            
            # Mouvement de perte si > 0
            if perte > 0:
                MouvementLot.objects.create(
                    lot=lot_src,
                    type='PERTE', # ou SOUTIRAGE avec perte ?
                    volume_l=perte,
                    date=date,
                    meta={'operation_id': str(op.id), 'motif': 'Perte soutirage'},
                    author=request.user
                )
                try:
                    move_vrac(lottech=lot_src, delta_l=-perte, reason='PERTE_SOUTIRAGE', user=request.user)
                except: pass
                
                lot_src.volume_l = (lot_src.volume_l or Decimal('0')) - perte
            
            # Mise à jour du contenant
            lot_src.contenant = cont_arr
            lot_src.save()
            
            # Création d'un lineage "reflexif" pour tracer l'opération ? Pas forcément nécessaire si même lot.
            # Mais pour la "Vue BDD" qui demande Lot Source / Lot Destination, c'est mieux d'avoir la trace.
            
            messages.success(request, "Soutirage enregistré avec succès.")
        else:
            for field, err in form.errors.items():
                messages.error(request, f"{field}: {err}")
        
        return redirect('production:soutirages_list')

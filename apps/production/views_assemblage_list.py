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

from apps.production.models import LotTechnique, Assemblage, AssemblageLigne, Operation

def get_assemblages_list(org, params=None):
    asms = Assemblage.objects.filter(
        result_lot__cuvee__organization=org
    ).select_related('result_lot').prefetch_related('lignes', 'lignes__lot_source').order_by('-date')

    assemblages_list = []
    for a in asms:
        # Construire la liste des lots sources
        sources = []
        total_vol = Decimal('0')
        for line in a.lignes.all():
            sources.append(f"{line.lot_source.code} ({line.volume_l}L)")
            total_vol += line.volume_l
        
        assemblages_list.append({
            'id': a.id,
            'date': a.date,
            'code': a.code,
            'lot_dest': a.result_lot,
            'sources_str': ", ".join(sources),
            'volume_total': total_vol, # ou a.result_lot.volume_l si c'est ça qu'on veut
            'contenant': a.result_lot.contenant if a.result_lot else '-',
            'notes': a.notes,
            'obj': a
        })

    # Python-side filtering
    if params:
        q = (params.get('q') or '').strip().lower()
        if q:
            filtered = []
            for item in assemblages_list:
                # Match against: code, lot_dest.code, sources_str, notes
                match = False
                if q in item['code'].lower(): match = True
                elif item['lot_dest'] and q in item['lot_dest'].code.lower(): match = True
                elif q in item['sources_str'].lower(): match = True
                elif q in str(item['notes']).lower(): match = True
                
                if match:
                    filtered.append(item)
            assemblages_list = filtered

    return assemblages_list

@method_decorator(login_required, name='dispatch')
class AssemblageListView(TemplateView):
    template_name = 'production/assemblages_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        
        ctx['page_title'] = 'Assemblages'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Assemblages', 'url': None},
        ]
        
        if not org:
            return ctx

        # Liste des assemblages
        ctx['assemblages'] = get_assemblages_list(org)
        return ctx

@method_decorator(login_required, name='dispatch')
class AssemblageTableView(TemplateView):
    template_name = 'production/_assemblages_table.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        params = self.request.GET.copy()
        if org:
            ctx['assemblages'] = get_assemblages_list(org, params=params)
        return ctx

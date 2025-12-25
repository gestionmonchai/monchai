from __future__ import annotations
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db import models
from datetime import datetime
from .models import DRMLine
from .services import select_inao_codes
from decimal import Decimal
import csv


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        # Counters by type and current campaign
        y = timezone.now().year
        campagne = f"{y}-{y+1}"
        lines = DRMLine.objects.filter(campagne=campagne)
        counters = {
            'mise': lines.filter(type='mise').count(),
            'entree': lines.filter(type='entree').count(),
            'sortie': lines.filter(type='sortie').count(),
            'perte': lines.filter(type='perte').count(),
            'vrac': lines.filter(type='vrac').count(),
        }
        total_l = sum(l.volume_l for l in lines)
        return render(request, 'drm/dashboard.html', {
            'counters': counters,
            'campagne': campagne,
            'total_l': total_l,
            'page_title': 'DRM - Tableau de bord',
            'breadcrumb_items': [
                {'name': 'DRM', 'url': '/drm/'},
                {'name': 'Tableau de bord', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class BrouillonView(View):
    def get(self, request, period=None):
        # period can come from path or query string (YYYY-MM)
        period = period or request.GET.get('period')
        if not period:
            period = timezone.now().strftime('%Y-%m')
        try:
            dt = datetime.strptime(period, '%Y-%m')
        except ValueError:
            dt = timezone.now()
        lines = DRMLine.objects.filter(date__year=dt.year, date__month=dt.month).order_by('date')
        return render(request, 'drm/brouillon.html', {
            'period': period,
            'lines': lines,
            'page_title': f'DRM - Brouillon {period}',
            'breadcrumb_items': [
                {'name': 'DRM', 'url': '/drm/'},
                {'name': f'Brouillon {period}', 'url': None},
            ]
        })


@method_decorator(login_required, name='dispatch')
class ExportView(View):
    def get(self, request, period=None):
        # period can come from path or query string (YYYY-MM)
        period = period or request.GET.get('period')
        if not period:
            period = timezone.now().strftime('%Y-%m')
        try:
            dt = datetime.strptime(period, '%Y-%m')
        except ValueError:
            dt = timezone.now()
        lines = DRMLine.objects.filter(date__year=dt.year, date__month=dt.month).order_by('date')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="drm_{period}.csv"'
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['date', 'type', 'volume_l', 'ref_kind', 'ref_id', 'campagne'])
        for l in lines:
            writer.writerow([l.date.isoformat(), l.type, l.volume_l, l.ref_kind, l.ref_id, l.campagne])
        return response


@method_decorator(login_required, name='dispatch')
class INAOCodeSearchApiView(View):
    def get(self, request):
        q = request.GET.get('q')
        appellation = request.GET.get('appellation')
        color = request.GET.get('color')
        vol_l = request.GET.get('volume_l') or request.GET.get('vol_l')
        vol_ml = request.GET.get('volume_ml') or request.GET.get('format_ml')
        abv = request.GET.get('abv_pct') or request.GET.get('abv')
        volume_l = None
        try:
            if vol_l:
                volume_l = Decimal(str(vol_l).replace(',', '.'))
            elif vol_ml:
                volume_l = (Decimal(int(vol_ml)) / Decimal(1000)).quantize(Decimal('0.001'))
        except Exception:
            volume_l = None
        abv_pct = None
        try:
            if abv:
                abv_pct = Decimal(str(abv).replace(',', '.'))
        except Exception:
            abv_pct = None
        qs = select_inao_codes(appellation=appellation, color=color, volume_l=volume_l, abv_pct=abv_pct, q=q, limit=100)
        data = [
            {
                'code_inao': r.code_inao,
                'code_nc': r.code_nc,
                'appellation_label': r.appellation_label,
                'color': r.color,
                'packaging_min_l': str(r.packaging_min_l) if r.packaging_min_l is not None else None,
                'packaging_max_l': str(r.packaging_max_l) if r.packaging_max_l is not None else None,
                'abv_min_pct': str(r.abv_min_pct) if r.abv_min_pct is not None else None,
                'abv_max_pct': str(r.abv_max_pct) if r.abv_max_pct is not None else None,
                'condition_text': r.condition_text,
            }
            for r in qs
        ]
        return JsonResponse({'results': data})


@method_decorator(login_required, name='dispatch')
class INAOListView(View):
    def get(self, request):
        from .models import INAOCode
        
        q = request.GET.get('q', '').strip()
        appellation = request.GET.get('appellation', '').strip()
        categorie = request.GET.get('categorie', '').strip()
        region = request.GET.get('region', '').strip()
        
        # Construire le queryset
        qs = INAOCode.objects.filter(active=True)
        
        if q:
            qs = qs.filter(
                models.Q(appellation_label__icontains=q) |
                models.Q(code_inao__icontains=q) |
                models.Q(code_nc__icontains=q) |
                models.Q(categorie__icontains=q)
            )
        if appellation:
            qs = qs.filter(appellation_label__icontains=appellation)
        if categorie:
            qs = qs.filter(categorie_code=categorie)
        if region:
            qs = qs.filter(region__icontains=region)
        
        any_filter = any([q, appellation, categorie, region])
        limit = 500 if any_filter else 100
        results = list(qs[:limit])
        limited = (not any_filter) and len(results) >= limit
        total_count = INAOCode.objects.filter(active=True).count()
        
        # Listes pour les filtres
        categories = INAOCode.CATEGORIE_CHOICES
        regions = INAOCode.objects.filter(active=True).exclude(region='').values_list('region', flat=True).distinct().order_by('region')

        return render(request, 'drm/inao_list.html', {
            'results': results,
            'limited': limited,
            'total_count': total_count,
            'page_title': 'Codes INAO (Douanes)',
            'breadcrumb_items': [
                {'name': 'DRM', 'url': '/drm/'},
                {'name': 'Codes INAO', 'url': None},
            ],
            'filters': {
                'q': q,
                'appellation': appellation,
                'categorie': categorie,
                'region': region,
            },
            'categories': categories,
            'regions': regions,
            'douanes_url': 'https://www.douane.gouv.fr/la-douane/opendata?f%5B0%5D=categorie_opendata_facet%3ADonn%C3%A9es%20fiscales',
        })

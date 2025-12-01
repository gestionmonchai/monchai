from __future__ import annotations
from decimal import Decimal
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse

from .models_ms import MSItem, MSEmplacement, MSFamily
from .services_ms import ms_receive, ms_transfer, ms_adjust


class MSReceiveModal(LoginRequiredMixin, View):
    def get(self, request):
        org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
        emplacements = MSEmplacement.objects.filter(organization=org) if org else []
        context = {
            'emplacements': emplacements,
            'item_id': request.GET.get('item_id') or '',
        }
        return render(request, 'production/modal_ms_entree.html', context)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
            if not org:
                return HttpResponseBadRequest('Organisation inconnue')
            item_id = request.POST.get('item_id')
            location_id = request.POST.get('location_id')
            qty = Decimal(request.POST.get('qty'))
            unit_price = Decimal(request.POST.get('unit_price_eur') or '0')
            item = MSItem.objects.get(pk=item_id, organization=org)
            location = MSEmplacement.objects.get(pk=location_id, organization=org)
            ms_receive(org, item, location, qty, unit_price, ref='Inventaire/Entrée')
            # Return empty response and trigger reload of MS pane
            resp = HttpResponse('')
            resp['HX-Trigger'] = 'reload-ms'
            return resp
        except Exception as e:
            return HttpResponseBadRequest(str(e))


class MSItemCreateModal(LoginRequiredMixin, View):
    def get(self, request):
        # If accessed directly (not HTMX), redirect to Inventory with MS tab
        try:
            if request.headers.get('HX-Request') != 'true':
                return redirect(reverse('production:inventaire') + '?tab=ms')
        except Exception:
            pass
        org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
        suggestions = []
        seen = set()
        for value, label in MSFamily.choices:
            key = (label or '').strip().lower()
            if key and key not in seen:
                seen.add(key)
                suggestions.append(label)
        try:
            qs = MSItem.objects.all()
            if org:
                qs = qs.filter(organization=org)
            for fam in qs.values_list('family', flat=True):
                s = (fam or '').strip()
                k = s.lower()
                if s and k not in seen:
                    seen.add(k)
                    suggestions.append(s)
        except Exception:
            pass
        # Emplacements for optional initial entry
        emplacements = MSEmplacement.objects.filter(organization=org) if org else []
        context = {
            'family_suggestions': suggestions,
            'emplacements': emplacements,
        }
        return render(request, 'production/modal_ms_item_create.html', context)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
            if not org:
                return HttpResponseBadRequest('Organisation inconnue')
            code = (request.POST.get('code') or '').strip()
            name = (request.POST.get('name') or '').strip()
            raw_family = (request.POST.get('family') or '').strip()
            uom = (request.POST.get('uom') or 'u').strip()
            pack_qty = Decimal(request.POST.get('pack_qty') or '1')
            stock_min = Decimal(request.POST.get('stock_min') or '0')
            # Optional initial entry
            location_id = (request.POST.get('location_id') or '').strip()
            qty_str = (request.POST.get('qty') or '').strip()
            unit_price_str = (request.POST.get('unit_price_eur') or '').strip()
            if not code or not name:
                return HttpResponseBadRequest('Code et nom requis')
            raw_family = raw_family[:30]
            # Map input to known enum values if it matches (by value or label), else keep free text
            fam_map_by_value = {str(v).strip().lower(): v for v, lbl in MSFamily.choices}
            fam_map_by_label = {str(lbl).strip().lower(): v for v, lbl in MSFamily.choices}
            key = raw_family.strip().lower()
            if key in fam_map_by_value:
                family_value = fam_map_by_value[key]
            elif key in fam_map_by_label:
                family_value = fam_map_by_label[key]
            else:
                family_value = raw_family
            item = MSItem.objects.create(
                organization=org,
                code=code,
                name=name,
                family=family_value,
                uom=uom,
                pack_qty=pack_qty,
                stock_min=stock_min,
                is_active=True,
            )
            # If initial entry provided, perform receive
            if location_id and qty_str:
                try:
                    qty = Decimal(qty_str)
                    unit_price = Decimal(unit_price_str or '0')
                    location = MSEmplacement.objects.get(pk=location_id, organization=org)
                    ms_receive(org, item, location, qty, unit_price, ref='Inventaire/Création + Entrée')
                except Exception as e:
                    # Return explicit error while keeping item created
                    return HttpResponseBadRequest(f'Créé, mais échec entrée initiale: {e}')
            resp = HttpResponse('')
            resp['HX-Trigger'] = 'reload-ms'
            return resp
        except Exception as e:
            return HttpResponseBadRequest(str(e))


class MSTransferModal(LoginRequiredMixin, View):
    def get(self, request):
        org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
        emplacements = MSEmplacement.objects.filter(organization=org) if org else []
        context = {
            'emplacements': emplacements,
            'item_id': request.GET.get('item_id') or '',
        }
        return render(request, 'production/modal_ms_transfert.html', context)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
            if not org:
                return HttpResponseBadRequest('Organisation inconnue')
            item_id = request.POST.get('item_id')
            from_id = request.POST.get('from_location_id')
            to_id = request.POST.get('to_location_id')
            qty = Decimal(request.POST.get('qty'))
            item = MSItem.objects.get(pk=item_id, organization=org)
            from_loc = MSEmplacement.objects.get(pk=from_id, organization=org)
            to_loc = MSEmplacement.objects.get(pk=to_id, organization=org)
            ms_transfer(org, item, from_loc, to_loc, qty, ref='Inventaire/Transfert')
            resp = HttpResponse('')
            resp['HX-Trigger'] = 'reload-ms'
            return resp
        except Exception as e:
            return HttpResponseBadRequest(str(e))


class MSAdjustModal(LoginRequiredMixin, View):
    def get(self, request):
        org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
        emplacements = MSEmplacement.objects.filter(organization=org) if org else []
        context = {
            'emplacements': emplacements,
            'item_id': request.GET.get('item_id') or '',
        }
        return render(request, 'production/modal_ms_ajustement.html', context)

    def post(self, request):
        try:
            org = getattr(request, 'current_org', None) or getattr(request.user, 'organization', None)
            if not org:
                return HttpResponseBadRequest('Organisation inconnue')
            item_id = request.POST.get('item_id')
            location_id = request.POST.get('location_id')
            delta = Decimal(request.POST.get('delta_qty'))
            reason = (request.POST.get('reason') or '').strip()
            item = MSItem.objects.get(pk=item_id, organization=org)
            location = MSEmplacement.objects.get(pk=location_id, organization=org)
            ms_adjust(org, item, location, delta, reason)
            resp = HttpResponse('')
            resp['HX-Trigger'] = 'reload-ms'
            return resp
        except Exception as e:
            return HttpResponseBadRequest(str(e))

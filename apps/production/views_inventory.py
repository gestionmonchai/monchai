from __future__ import annotations
from decimal import Decimal
from datetime import date, timedelta

from django.db.models import Sum, Q
from django.utils import timezone
from django.views.generic import TemplateView, ListView, RedirectView
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from .models import LotTechnique
from .models_ms import MSItem
from apps.production.models import CostEntry
from apps.referentiels.models import Cuvee
from apps.stock.models import SKU, StockSKUBalance
from apps.sales.models import StockReservation
from apps.produits.models import LotCommercial


class PermissionMixin:
    """Mixin pour verifier les permissions granulaires."""
    permission_module = 'stocks'
    permission_action = 'view'
    
    def dispatch(self, request, *args, **kwargs):
        membership = getattr(request, 'membership', None)
        if membership and not membership.has_permission(self.permission_module, self.permission_action):
            messages.error(request, f"Acces refuse. Vous n'avez pas la permission sur {self.permission_module}.")
            return redirect('auth:dashboard')
        return super().dispatch(request, *args, **kwargs)


def _get_org(request):
    # Try request.current_org first (pattern used elsewhere), fallback to user.organization
    org = getattr(request, 'current_org', None)
    if org:
        return org
    return getattr(request.user, 'organization', None)


class InventoryHomeView(LoginRequiredMixin, PermissionMixin, TemplateView):
    template_name = 'production/inventaire_home.html'
    permission_module = 'stocks'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = _get_org(self.request)

        # KPIs vrac: actifs = en_cours | stabilise | pret_mise
        vrac_qs = LotTechnique.objects.select_related('cuvee')
        if org:
            vrac_qs = vrac_qs.filter(cuvee__organization=org)
        actifs_qs = vrac_qs.filter(statut__in=['en_cours', 'stabilise', 'pret_mise'])
        total_l = actifs_qs.aggregate(s=Sum('volume_l'))['s'] or Decimal('0')
        ctx['kpi_vrac_hl'] = (total_l / Decimal('100')) if total_l else Decimal('0')
        ctx['kpi_lots_actifs'] = actifs_qs.count()
        ctx['kpi_pret_mise'] = vrac_qs.filter(statut='pret_mise').count()

        # Pertes M-1 (€/L) depuis CostEntry (entity_type=lottech, nature=vrac_loss)
        try:
            today = timezone.now().date()
            first_this = today.replace(day=1)
            last_prev = first_this - timedelta(days=1)
            start_prev = last_prev.replace(day=1)
            ce = CostEntry.objects.filter(entity_type='lottech', nature='vrac_loss')
            if org:
                ce = ce.filter(organization=org)
            ce = ce.filter(date__date__gte=start_prev, date__date__lte=last_prev)
            ctx['kpi_pertes_m1_eur'] = ce.aggregate(s=Sum('amount_eur'))['s'] or Decimal('0')
            ctx['kpi_pertes_m1_l'] = ce.aggregate(s=Sum('qty'))['s'] or Decimal('0')
        except Exception:
            ctx['kpi_pertes_m1_eur'] = Decimal('0')
            ctx['kpi_pertes_m1_l'] = Decimal('0')

        # Filtres cuvées
        cuvees = Cuvee.objects.all()
        if org:
            cuvees = cuvees.filter(organization=org)
        ctx['cuvees'] = cuvees.order_by('nom')[:500]

        ctx['page_title'] = 'Inventaire'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Inventaire', 'url': None},
        ]
        # Feature flags
        ctx['feature_ms'] = getattr(settings, 'FEATURE_MS', False)
        return ctx


class InventoryVracTable(ListView):
    template_name = 'production/_inventaire_vrac_table.html'
    paginate_by = 25
    model = LotTechnique

    def get_queryset(self):
        request = self.request
        org = _get_org(request)
        qs = (
            LotTechnique.objects.select_related('cuvee')
            .only('id', 'code', 'volume_l', 'statut', 'campagne', 'contenant', 'cuvee__nom')
        )
        if org:
            qs = qs.filter(cuvee__organization=org)
        # Filters
        q = (request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(cuvee__nom__icontains=q))
        status = (request.GET.get('status') or '').strip()
        if status:
            qs = qs.filter(statut=status)
        camp = (request.GET.get('campagne') or '').strip()
        if camp:
            qs = qs.filter(campagne=camp)
        cuvee = (request.GET.get('cuvee') or '').strip()
        if cuvee:
            qs = qs.filter(cuvee_id=cuvee)
        return qs.order_by('-created_at', '-id')


class InventoryFinishedTable(ListView):
    template_name = 'production/_inventaire_produits_table.html'
    paginate_by = 25
    model = SKU

    def get_queryset(self):
        request = self.request
        org = _get_org(request)
        qs = (
            SKU.objects.select_related('cuvee', 'cuvee__vintage', 'uom')
        )
        if org:
            qs = qs.filter(organization=org)
        q = (request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(label__icontains=q) | Q(cuvee__nom__icontains=q))
        cuvee = (request.GET.get('cuvee') or '').strip()
        if cuvee:
            qs = qs.filter(cuvee_id=cuvee)
        fmt = (request.GET.get('format') or '').strip()
        if fmt:
            qs = qs.filter(uom__code__iexact=fmt)
        # Aggregate stock dispo by SKU from balances
        balances = StockSKUBalance.objects
        if org:
            balances = balances.filter(organization=org)
        agg = balances.values('sku_id').annotate(total=Sum('qty_units'))
        totals_by_sku = {row['sku_id']: row['total'] or 0 for row in agg}
        # Aggregate reserved units per SKU
        reservations = StockReservation.objects
        if org:
            reservations = reservations.filter(organization=org)
        ragg = reservations.values('sku_id').annotate(total=Sum('qty_units'))
        reserved_by_sku = {row['sku_id']: row['total'] or 0 for row in ragg}
        # Attach totals on objects for template
        for obj in qs:
            total = int(totals_by_sku.get(obj.id, 0) or 0)
            reserved = int(reserved_by_sku.get(obj.id, 0) or 0)
            obj.total_stock = total
            obj.total_reserved = reserved
            obj.total_dispo = max(total - reserved, 0)
        dispo_only = (request.GET.get('dispo_gt0') or '').strip()
        if dispo_only in ['1', 'true', 'True']:
            qs = [o for o in qs if (getattr(o, 'total_dispo', 0) or 0) > 0]
        return qs


class InventoryMSTable(TemplateView):
    template_name = 'production/_inventaire_ms_table.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = _get_org(self.request)
        feature_ms = getattr(settings, 'FEATURE_MS', False)
        ctx['feature_ms_enabled'] = feature_ms
        items = []
        if feature_ms:
            qs = MSItem.objects.filter(is_active=True)
            if org:
                qs = qs.filter(organization=org)
            items = qs.only('id', 'code', 'name', 'family', 'cmp_eur_u', 'stock_min')
        ctx['items'] = items
        return ctx


class InventoryLotsCommerciaux(ListView):
    """Vue des lots commerciaux (bouteilles issues de mises)."""
    template_name = 'production/_inventaire_lots_commerciaux_table.html'
    paginate_by = 25
    model = LotCommercial

    def get_queryset(self):
        request = self.request
        org = _get_org(request)
        qs = LotCommercial.objects.select_related('cuvee', 'mise')
        if org:
            qs = qs.filter(organization=org)
        # Filters
        q = (request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(code_lot__icontains=q) | Q(cuvee__name__icontains=q))
        etiq = (request.GET.get('etiquetage') or '').strip()
        if etiq:
            qs = qs.filter(etiquetage=etiq)
        fmt = (request.GET.get('format') or '').strip()
        if fmt:
            try:
                qs = qs.filter(format_ml=int(fmt))
            except ValueError:
                pass
        dispo_only = (request.GET.get('dispo_gt0') or '').strip()
        if dispo_only in ['1', 'true', 'True']:
            qs = qs.filter(stock_disponible__gt=0)
        return qs.order_by('-date_mise', '-created_at')


class InventoryRedirectView(RedirectView):
    """Redirect legacy/alias "Stock (vrac)" to Inventory tab=vrac."""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse('production:inventaire') + '?tab=vrac'

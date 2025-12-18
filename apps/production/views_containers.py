from __future__ import annotations
from decimal import Decimal
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .models_containers import Contenant
from .models import LotTechnique, MouvementLot


@method_decorator(login_required, name='dispatch')
class ContenantListView(ListView):
    template_name = "production/contenants_list.html"
    model = Contenant
    context_object_name = 'contenants'
    paginate_by = 50

    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        qs = Contenant.objects.all()
        if org:
            qs = qs.filter(organization=org)
        qs = qs.filter(is_active=True)
        q = (self.request.GET.get('q') or '').strip()
        typ = (self.request.GET.get('type') or '').strip()
        statut = (self.request.GET.get('statut') or '').strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(label__icontains=q) | Q(localisation__icontains=q))
        if typ:
            qs = qs.filter(type=typ)
        if statut:
            qs = qs.filter(statut=statut)
        return qs.select_related('lot_courant').order_by('code')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # KPI rapides
        qs = self.get_queryset()
        try:
            total = qs.count()
        except Exception:
            total = 0
        try:
            cap_utile = qs.aggregate(s=Sum('capacite_utile_l'))['s'] or Decimal('0')
        except Exception:
            cap_utile = Decimal('0')
        try:
            occ = qs.aggregate(s=Sum('volume_occupe_l'))['s'] or Decimal('0')
        except Exception:
            occ = Decimal('0')
        # Calcul du % d'occupation
        if cap_utile and cap_utile > 0:
            occupation_pct = round(float(occ / cap_utile * 100), 1)
        else:
            occupation_pct = 0
        # Comptage cuves occupées vs libres
        try:
            cuves_occupees = qs.filter(volume_occupe_l__gt=0).count()
        except Exception:
            cuves_occupees = 0
        # Volume libre
        libre = cap_utile - occ if cap_utile else Decimal('0')
        # Conversion L vers HL pour affichage
        cap_utile_hl = cap_utile / 100 if cap_utile else Decimal('0')
        occ_hl = occ / 100 if occ else Decimal('0')
        libre_hl = libre / 100 if libre else Decimal('0')
        ctx.update({
            'kpi': {
                'count': total,
                'cap_utile': cap_utile_hl,
                'occ': occ_hl,
                'libre': libre_hl,
                'occupation_pct': occupation_pct,
                'cuves_occupees': cuves_occupees,
                'cuves_libres': total - cuves_occupees,
            },
            'types': Contenant.TYPE_CHOICES,
            'statuts': Contenant.STATUT_CHOICES,
            'page_title': 'Cuves & barriques',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Cuves & barriques', 'url': None},
            ],
        })
        return ctx


@method_decorator(login_required, name='dispatch')
class ContenantDetailView(DetailView):
    template_name = "production/contenants_detail.html"
    model = Contenant
    context_object_name = 'contenant'

    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        qs = Contenant.objects.all()
        if org:
            qs = qs.filter(organization=org)
        return qs.select_related('lot_courant')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c: Contenant = self.object
        mouvements = []
        if c.lot_courant_id:
            mouvements = MouvementLot.objects.filter(lot=c.lot_courant_id).order_by('-date', '-created_at')[:200]
        # Occupancy percent based on useful capacity
        try:
            cap = Decimal(str(c.capacite_utile_effective_l or 0))
            occ = Decimal(str(c.volume_occupe_l or 0))
            pct = float((occ / cap * 100) if cap and cap > 0 else 0)
        except Exception:
            pct = 0.0
        # Next maintenance dates
        from datetime import timedelta
        next_nettoyage = None
        next_ouillage = None
        try:
            if c.date_dernier_nettoyage and c.cycle_nettoyage_j:
                next_nettoyage = c.date_dernier_nettoyage + timedelta(days=int(c.cycle_nettoyage_j))
        except Exception:
            next_nettoyage = None
        try:
            if c.date_dernier_ouillage and c.cycle_ouillage_j:
                next_ouillage = c.date_dernier_ouillage + timedelta(days=int(c.cycle_ouillage_j))
        except Exception:
            next_ouillage = None
        # Lots list for affectation (simple filter)
        org = getattr(self.request, 'current_org', None)
        lots_qs = LotTechnique.objects.all()
        if org:
            # LotTechnique.organization is property via cuvée; fallback to no filter
            try:
                lots_qs = lots_qs.filter(cuvee__organization=org)
            except Exception:
                pass
        lots = lots_qs.order_by('-created_at')[:200]
        ctx.update({
            'mouvements': mouvements,
            'free_capacity_l': c.free_capacity_l(),
            'occupancy_pct': pct,
            'next_nettoyage': next_nettoyage,
            'next_ouillage': next_ouillage,
            'lots': lots,
            'page_title': 'Fiche cuve / barrique',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Cuves & barriques', 'url': '/production/contenants/'},
                {'name': c.code, 'url': None},
            ],
        })
        return ctx


@method_decorator(login_required, name='dispatch')
class ContenantCreateView(CreateView):
    template_name = "production/contenants_form.html"
    model = Contenant
    fields = [
        # Bloc Essentiel
        "code", "label", "type", "capacite_l", "capacite_utile_l", "localisation",
        # Spécifiques cuves
        "thermo_regule", "type_thermoregulation", "temperature_min", "temperature_max",
        "temperature_cible", "forme",
        # Spécifiques barriques/foudres
        "origine_bois", "grain_bois", "type_chauffe", "tonnelier",
        "statut_barrique", "annee_mise_service",
        # Sanitaire & maintenance
        "cycle_nettoyage_j", "cycle_ouillage_j", "note_sanitaire"
    ]

    def form_valid(self, form):
        form.instance.organization = getattr(self.request, 'current_org', None)
        form.instance.created_by = getattr(self.request, 'user', None)
        messages.success(self.request, "Contenant créé")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("production:contenants_detail", args=[self.object.pk])


@method_decorator(login_required, name='dispatch')
class ContenantUpdateView(UpdateView):
    template_name = "production/contenants_form.html"
    model = Contenant
    fields = [
        # Bloc Essentiel
        "label", "type", "capacite_l", "capacite_utile_l", "localisation",
        # Spécifiques cuves
        "thermo_regule", "type_thermoregulation", "temperature_min", "temperature_max",
        "temperature_cible", "forme",
        # Spécifiques barriques/foudres
        "origine_bois", "grain_bois", "type_chauffe", "tonnelier",
        "statut_barrique", "annee_mise_service",
        # Sanitaire & maintenance
        "cycle_nettoyage_j", "cycle_ouillage_j", "note_sanitaire",
        # Statut opérationnel
        "statut", "is_active"
    ]

    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        qs = Contenant.objects.all()
        if org:
            qs = qs.filter(organization=org)
        return qs

    def form_valid(self, form):
        messages.success(self.request, "Contenant mis à jour")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("production:contenants_detail", args=[self.object.pk])


# Actions
@login_required
@transaction.atomic
def contenant_recalc_occupancy(request, pk):
    org = getattr(request, 'current_org', None)
    c = get_object_or_404(Contenant, pk=pk)
    if org and c.organization_id != getattr(org, 'id', None):
        messages.error(request, "Contenant hors organisation")
        return redirect("production:contenants_detail", pk=pk)
    if c.lot_courant_id:
        from django.db.models import Sum
        movs = MouvementLot.objects.filter(lot=c.lot_courant_id)
        in_sum = movs.filter(type__in=['ENTREE_INITIALE','ASSEMBLAGE_IN','TRANSFERT_IN']).aggregate(s=Sum('volume_l'))['s'] or Decimal('0')
        out_sum = movs.filter(type__in=['ASSEMBLAGE_OUT','TRANSFERT_OUT','SOUTIRAGE','MISE_OUT']).aggregate(s=Sum('volume_l'))['s'] or Decimal('0')
        loss_sum = movs.filter(type='PERTE').aggregate(s=Sum('volume_l'))['s'] or Decimal('0')
        net = in_sum - out_sum - loss_sum
        c.volume_occupe_l = net if net > 0 else Decimal('0')
        c.statut = 'occupe' if net > 0 else 'disponible'
        c.save(update_fields=['volume_occupe_l','statut'])
        messages.success(request, "Occupation recalculée.")
    else:
        c.volume_occupe_l = Decimal('0')
        c.statut = 'disponible'
        c.save(update_fields=['volume_occupe_l','statut'])
        messages.info(request, "Contenant sans lot courant: mis à zéro.")
    return redirect("production:contenants_detail", pk=pk)


@method_decorator(login_required, name='dispatch')
class ContenantAffecterLotView(View):
    def post(self, request, pk):
        c = get_object_or_404(Contenant, pk=pk)
        org = getattr(request, 'current_org', None)
        if org and c.organization_id != getattr(org, 'id', None):
            messages.error(request, "Contenant hors organisation")
            return redirect("production:contenants_detail", pk=pk)
        lot_id = request.POST.get('lot_id')
        volume_l = Decimal(request.POST.get('volume_l') or '0')
        lot = get_object_or_404(
            LotTechnique.objects.select_related('cuvee').filter(Q(cuvee__organization=org) | Q(source__organization=org)),
            pk=lot_id,
        )
        if not c.can_receive(volume_l):
            messages.error(request, "Capacité insuffisante")
            return redirect("production:contenants_detail", pk=pk)
        c.lot_courant = lot
        c.volume_occupe_l = (c.volume_occupe_l or 0) + volume_l
        c.statut = 'occupe'
        c.save(update_fields=['lot_courant','volume_occupe_l','statut'])
        messages.success(request, "Lot affecté au contenant")
        return redirect("production:contenants_detail", pk=pk)


@method_decorator(login_required, name='dispatch')
class ContenantVidangeView(View):
    def post(self, request, pk):
        c = get_object_or_404(Contenant, pk=pk)
        org = getattr(request, 'current_org', None)
        if org and c.organization_id != getattr(org, 'id', None):
            messages.error(request, "Contenant hors organisation")
            return redirect("production:contenants_detail", pk=pk)
        c.volume_occupe_l = Decimal('0')
        c.lot_courant = None
        c.statut = 'disponible'
        c.save(update_fields=['volume_occupe_l','lot_courant','statut'])
        messages.success(request, "Contenant vidé")
        return redirect("production:contenants_detail", pk=pk)


@method_decorator(login_required, name='dispatch')
class ContenantNettoyageView(View):
    def post(self, request, pk):
        from datetime import date
        c = get_object_or_404(Contenant, pk=pk)
        org = getattr(request, 'current_org', None)
        if org and c.organization_id != getattr(org, 'id', None):
            messages.error(request, "Contenant hors organisation")
            return redirect("production:contenants_detail", pk=pk)
        c.date_dernier_nettoyage = date.today()
        c.statut = 'occupe' if c.lot_courant_id else 'disponible'
        c.save(update_fields=['date_dernier_nettoyage','statut'])
        messages.success(request, "Nettoyage enregistré")
        return redirect("production:contenants_detail", pk=pk)

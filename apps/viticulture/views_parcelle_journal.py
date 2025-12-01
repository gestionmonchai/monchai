from django.views.generic import DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.accounts.decorators import require_membership
from datetime import date as dt_date

from .models_parcelle_journal import ParcelleJournalEntry, ParcelleOperationType
from apps.referentiels.models import Parcelle


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='read_only'), name='dispatch')
class ParcelleJournalView(DetailView):
    template_name = "viticulture/parcelle_journal.html"
    model = Parcelle
    context_object_name = "parcelle"

    def get_queryset(self):
        return Parcelle.objects.filter(organization=self.request.current_org)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # En-tête : badges vendanges (référence uniquement, pas dans la timeline)
        vendanges = []
        try:
            vendanges = self.object.vendanges.order_by('-date')[:3]
        except Exception:
            vendanges = []
        ctx["vendanges"] = vendanges
        ctx["op_types"] = ParcelleOperationType.objects.all()
        # Liste d'années disponibles (ou fallback 5 dernières années)
        try:
            years_qs = (
                ParcelleJournalEntry.objects
                .filter(organization=self.request.current_org, parcelle=self.object)
                .values_list('date__year', flat=True)
                .distinct()
            )
            years = sorted([y for y in years_qs if y], reverse=True)
        except Exception:
            years = []
        if not years:
            cy = dt_date.today().year
            years = [cy - i for i in range(0, 5)]
        ctx["years"] = years
        ctx["page_title"] = f"Journal de parcelle — {self.object.nom}"
        ctx["organization"] = getattr(self.request, 'current_org', None)
        return ctx


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='read_only'), name='dispatch')
class ParcelleJournalPartial(TemplateView):
    template_name = "viticulture/_parcelle_journal_table.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        parcelle_id = self.kwargs["pk"]
        parcelle = get_object_or_404(Parcelle, pk=parcelle_id, organization=self.request.current_org)
        q = (self.request.GET.get("q") or "").strip()
        t = (self.request.GET.get("type") or "").strip()
        y = (self.request.GET.get("year") or "").strip()
        qs = ParcelleJournalEntry.objects.filter(organization=self.request.current_org, parcelle=parcelle)
        if t:
            qs = qs.filter(op_type__code=t)
        if y:
            try:
                qs = qs.filter(date__year=int(y))
            except Exception:
                pass
        if q:
            qs = qs.filter(Q(resume__icontains=q) | Q(notes__icontains=q))
        ctx["items"] = qs.select_related("op_type")[:500]
        ctx["parcelle"] = parcelle
        return ctx

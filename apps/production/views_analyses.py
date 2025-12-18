"""
Vues pour la gestion des analyses œnologiques.
"""

from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse

from .views import PermissionMixin
from .models_analyses import Analyse
from .models import LotTechnique
from .forms_analyses import AnalyseForm, AnalyseFilterForm


@method_decorator(login_required, name='dispatch')
class AnalysesOenoListView(PermissionMixin, TemplateView):
    """
    Vue liste des analyses œnologiques.
    Affiche toutes les analyses avec filtres et alertes.
    """
    template_name = 'production/analyses_oeno_list.html'
    permission_module = 'production'
    permission_action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)

        # Récupérer les campagnes disponibles
        campagnes = []
        if org:
            campagnes = list(
                LotTechnique.objects.filter(cuvee__organization=org)
                .values_list('campagne', flat=True)
                .distinct()
                .order_by('-campagne')
            )

        # Formulaire de filtres
        filter_form = AnalyseFilterForm(self.request.GET, campagnes=campagnes)

        # KPIs
        kpis = self._compute_kpis(org)

        context.update({
            'filter_form': filter_form,
            'campagnes': campagnes,
            'kpis': kpis,
        })
        return context

    def _compute_kpis(self, org):
        """Calcule les KPIs pour le header."""
        if not org:
            return {'total': 0, 'alertes': 0, 'en_attente': 0, 'validees': 0}

        qs = Analyse.objects.filter(organization=org)
        return {
            'total': qs.count(),
            'alertes': qs.filter(niveau_alerte='alerte').count(),
            'surveillance': qs.filter(niveau_alerte='surveillance').count(),
            'en_attente': qs.filter(statut__in=['planifiee', 'prelevement', 'attente_resultats']).count(),
            'validees': qs.filter(statut='validee').count(),
        }


@method_decorator(login_required, name='dispatch')
class AnalysesOenoTableView(PermissionMixin, View):
    """
    Vue partielle HTMX pour le tableau des analyses.
    """
    permission_module = 'production'
    permission_action = 'view'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        
        # Base queryset
        if org:
            qs = Analyse.objects.filter(organization=org).select_related('lot', 'lot__cuvee')
        else:
            qs = Analyse.objects.none()

        # Appliquer les filtres
        qs = self._apply_filters(qs, request.GET)

        # Tri
        sort = request.GET.get('sort', 'date_desc')
        if sort == 'date_asc':
            qs = qs.order_by('date', 'created_at')
        elif sort == 'type':
            qs = qs.order_by('type_analyse', '-date')
        elif sort == 'alerte':
            # Alertes en premier
            qs = qs.order_by('-niveau_alerte', '-date')
        else:
            qs = qs.order_by('-date', '-created_at')

        # Pagination simple
        page = int(request.GET.get('page', 1))
        per_page = 25
        total_count = qs.count()
        total_pages = (total_count + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        analyses = list(qs[start:end])

        return render(request, 'production/_analyses_oeno_table.html', {
            'analyses': analyses,
            'total_count': total_count,
            'page': page,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'previous_page': page - 1,
            'next_page': page + 1,
        })

    def _apply_filters(self, qs, params):
        """Applique les filtres de recherche."""
        # Recherche texte
        q = params.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(lot__code__icontains=q) |
                Q(lot__cuvee__nom__icontains=q) |
                Q(commentaires_internes__icontains=q) |
                Q(notes_degustation__icontains=q) |
                Q(alerte_description__icontains=q)
            )

        # Campagne
        campagne = params.get('campagne', '').strip()
        if campagne:
            qs = qs.filter(lot__campagne=campagne)

        # Type d'analyse
        type_analyse = params.get('type_analyse', '').strip()
        if type_analyse:
            qs = qs.filter(type_analyse=type_analyse)

        # Statut
        statut = params.get('statut', '').strip()
        if statut:
            qs = qs.filter(statut=statut)

        # Niveau d'alerte
        niveau_alerte = params.get('niveau_alerte', '').strip()
        if niveau_alerte:
            qs = qs.filter(niveau_alerte=niveau_alerte)

        # Alerte uniquement
        alerte_only = params.get('alerte_only', '').lower() in ('true', 'on', '1')
        if alerte_only:
            qs = qs.filter(niveau_alerte__in=['surveillance', 'alerte'])

        # Période
        date_start = params.get('date_start', '').strip()
        if date_start:
            qs = qs.filter(date__gte=date_start)

        date_end = params.get('date_end', '').strip()
        if date_end:
            qs = qs.filter(date__lte=date_end)

        return qs


@method_decorator(login_required, name='dispatch')
class AnalyseCreateView(PermissionMixin, View):
    """
    Vue de création d'une nouvelle analyse œnologique.
    """
    template_name = 'production/analyse_form.html'
    permission_module = 'production'
    permission_action = 'edit'

    def get(self, request):
        org = getattr(request, 'current_org', None)
        lot_prefill = None

        # Pré-remplissage depuis URL ?lot=<uuid>
        lot_id = request.GET.get('lot', '').strip()
        if lot_id:
            try:
                lot_prefill = LotTechnique.objects.get(pk=lot_id)
            except LotTechnique.DoesNotExist:
                pass

        form = AnalyseForm(organization=org, lot_prefill=lot_prefill)

        return render(request, self.template_name, {
            'form': form,
            'lot_prefill': lot_prefill,
            'is_edit': False,
            'page_title': 'Nouvelle analyse',
        })

    def post(self, request):
        org = getattr(request, 'current_org', None)
        lot_prefill = None

        lot_id = request.POST.get('lot', '').strip()
        if lot_id:
            try:
                lot_prefill = LotTechnique.objects.get(pk=lot_id)
            except LotTechnique.DoesNotExist:
                pass

        form = AnalyseForm(request.POST, organization=org, lot_prefill=lot_prefill)

        if form.is_valid():
            analyse = form.save(commit=False)
            analyse.organization = org
            analyse.save()

            messages.success(request, f"Analyse créée avec succès pour le lot {analyse.lot.code}.")

            # Redirection selon le bouton cliqué
            if 'save_and_new' in request.POST:
                return redirect('production:analyse_oeno_new')
            return redirect('production:analyses_oeno_list')

        return render(request, self.template_name, {
            'form': form,
            'lot_prefill': lot_prefill,
            'is_edit': False,
            'page_title': 'Nouvelle analyse',
        })


@method_decorator(login_required, name='dispatch')
class AnalyseUpdateView(PermissionMixin, View):
    """
    Vue de modification d'une analyse existante.
    """
    template_name = 'production/analyse_form.html'
    permission_module = 'production'
    permission_action = 'edit'

    def get(self, request, pk):
        org = getattr(request, 'current_org', None)
        analyse = get_object_or_404(Analyse, pk=pk)

        # Vérifier l'organisation
        if org and analyse.organization_id != org.id:
            messages.error(request, "Vous n'avez pas accès à cette analyse.")
            return redirect('production:analyses_oeno_list')

        form = AnalyseForm(instance=analyse, organization=org, lot_prefill=analyse.lot)

        return render(request, self.template_name, {
            'form': form,
            'analyse': analyse,
            'lot_prefill': analyse.lot,
            'is_edit': True,
            'page_title': f'Modifier analyse - {analyse.lot.code}',
        })

    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        analyse = get_object_or_404(Analyse, pk=pk)

        if org and analyse.organization_id != org.id:
            messages.error(request, "Vous n'avez pas accès à cette analyse.")
            return redirect('production:analyses_oeno_list')

        form = AnalyseForm(request.POST, instance=analyse, organization=org, lot_prefill=analyse.lot)

        if form.is_valid():
            form.save()
            messages.success(request, "Analyse mise à jour avec succès.")
            return redirect('production:analyses_oeno_list')

        return render(request, self.template_name, {
            'form': form,
            'analyse': analyse,
            'lot_prefill': analyse.lot,
            'is_edit': True,
            'page_title': f'Modifier analyse - {analyse.lot.code}',
        })


@method_decorator(login_required, name='dispatch')
class AnalyseDeleteView(PermissionMixin, View):
    """
    Vue de suppression d'une analyse.
    """
    permission_module = 'production'
    permission_action = 'edit'

    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        analyse = get_object_or_404(Analyse, pk=pk)

        if org and analyse.organization_id != org.id:
            messages.error(request, "Vous n'avez pas accès à cette analyse.")
            return redirect('production:analyses_oeno_list')

        lot_code = analyse.lot.code
        analyse.delete()
        messages.success(request, f"Analyse pour le lot {lot_code} supprimée.")

        # Retour HTMX ou redirection
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Redirect': '/production/lots-elevage/analyses/'})
        return redirect('production:analyses_oeno_list')


@method_decorator(login_required, name='dispatch')
class AnalyseDuplicateView(PermissionMixin, View):
    """
    Duplique une analyse existante.
    """
    permission_module = 'production'
    permission_action = 'edit'

    def post(self, request, pk):
        org = getattr(request, 'current_org', None)
        analyse = get_object_or_404(Analyse, pk=pk)

        if org and analyse.organization_id != org.id:
            messages.error(request, "Vous n'avez pas accès à cette analyse.")
            return redirect('production:analyses_oeno_list')

        # Créer une copie
        from django.utils import timezone
        analyse.pk = None
        analyse.id = None
        analyse.date = timezone.now().date()
        analyse.statut = 'planifiee'
        analyse.alerte_declenchee = False
        analyse.alerte_type = ''
        analyse.alerte_description = ''
        analyse.alerte_recommandation = ''
        analyse.niveau_alerte = 'ok'
        analyse.save()

        messages.success(request, f"Analyse dupliquée pour le lot {analyse.lot.code}.")

        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Redirect': '/production/lots-elevage/analyses/'})
        return redirect('production:analyses_oeno_list')

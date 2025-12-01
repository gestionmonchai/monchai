from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import LotTechnique

class VueCuveeView(LoginRequiredMixin, TemplateView):
    template_name = 'production/lots_vue_cuvee.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Lots Techniques'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Lots Techniques', 'url': None},
        ]
        ctx['statut_choices'] = LotTechnique.STATUT_CHOICES
        
        # Campagnes
        org = getattr(self.request, 'current_org', None)
        camps = LotTechnique.objects.filter(cuvee__organization=org).values_list('campagne', flat=True).distinct().order_by('-campagne') if org else []
        ctx['campagnes'] = [c for c in camps if c]
        
        ctx['selected'] = self.request.GET
        return ctx

class LotTechniqueVueCuveeStatsAPI(LoginRequiredMixin, View):
    """
    API pour l'agrégation par cuvée/campagne.
    GET /api/production/lots-techniques/vue-cuvee/?campagne=...&search=...&statuts=...
    """
    def get(self, request, *args, **kwargs):
        org = request.current_org
        qs = LotTechnique.objects.filter(
            cuvee__organization=org
        ).select_related('cuvee')

        # --- Filtres ---
        
        # 1. Campagne
        campagne = request.GET.get('campagne')
        if campagne and campagne != 'all':
            qs = qs.filter(campagne=campagne)

        # 2. Recherche (cuvée nom, lot code, contenant)
        search = request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(cuvee__nom__icontains=search) |
                Q(code__icontains=search) |
                Q(contenant__icontains=search)
            )

        # 3. Statuts (comma separated)
        statuts = request.GET.get('statuts')
        if statuts:
            statut_list = [s.strip() for s in statuts.split(',') if s.strip()]
            if statut_list:
                qs = qs.filter(statut__in=statut_list)

        # 4. Contenants (types) - MVP: filtrage textuel simple ou skip
        # Le modèle n'a pas de lien direct fiable vers le type de contenant pour l'instant.
        # On pourrait implémenter un filtrage heuristique ici si nécessaire.
        # Pour l'instant on ignore ce filtre côté serveur ou on le fait sur le texte 'contenant'.
        contenant_types = request.GET.get('contenant_types')
        if contenant_types:
            # Heuristique simple: "Barrique" -> contient "B-", "Cuve" -> "Cuve", etc.
            # À améliorer avec un vrai modèle Contenant lié.
            pass 

        # --- Agrégation Python ---
        # On récupère tout pour faire le pivot en Python (plus flexible pour les structures imbriquées)
        # Attention à la performance si > 10k lots. Pour un tenant viticole, c'est généralement OK.
        
        lots = qs.values(
            'id', 'cuvee__id', 'cuvee__nom', 'campagne', 
            'statut', 'contenant', 'volume_l', 'code'
        ).order_by('-campagne', 'cuvee__nom')

        grouped = {}

        for lot in lots:
            c_id = str(lot['cuvee__id'] or 'orphans')
            c_nom = lot['cuvee__nom'] or 'Sans cuvée'
            camp = lot['campagne']
            
            # Clé unique de regroupement
            key = (c_id, camp)
            
            if key not in grouped:
                grouped[key] = {
                    "cuvee_id": c_id if c_id != 'orphans' else None,
                    "cuvee_nom": c_nom,
                    "campagne": camp,
                    "nb_lots": 0,
                    "volume_total_l": 0.0,
                    "statuts_map": {},
                    "contenants_map": {}
                }
            
            g = grouped[key]
            g["nb_lots"] += 1
            vol = float(lot['volume_l'] or 0)
            g["volume_total_l"] += vol
            
            # Agrégation statuts
            st = lot['statut']
            if st not in g["statuts_map"]:
                g["statuts_map"][st] = {"statut": st, "nb_lots": 0, "volume_l": 0.0}
            g["statuts_map"][st]["nb_lots"] += 1
            g["statuts_map"][st]["volume_l"] += vol
            
            # Agrégation contenants
            cont_code = lot['contenant'] or 'Inconnu'
            # Type heuristique pour l'affichage
            cont_type = 'autre'
            if 'cuve' in cont_code.lower(): cont_type = 'cuve'
            elif 'barrique' in cont_code.lower() or cont_code.startswith('B-'): cont_type = 'barrique'
            elif 'ibc' in cont_code.lower(): cont_type = 'ibc'
            
            if cont_code not in g["contenants_map"]:
                g["contenants_map"][cont_code] = {
                    "contenant_code": cont_code,
                    "type": cont_type,
                    "nb_lots": 0,
                    "volume_l": 0.0
                }
            g["contenants_map"][cont_code]["nb_lots"] += 1
            g["contenants_map"][cont_code]["volume_l"] += vol

        # Formatage final liste
        results = []
        for key, g in grouped.items():
            # Transformer maps en listes
            g["repartition_statuts"] = list(g["statuts_map"].values())
            g["repartition_contenants"] = list(g["contenants_map"].values())
            del g["statuts_map"]
            del g["contenants_map"]
            results.append(g)

        # Tri final : Campagne DESC, Cuvée nom ASC
        results.sort(key=lambda x: (x['campagne'], x['cuvee_nom']), reverse=False) 
        # Note: reverse=False car on veut Campagne croissant ? Non, on veut 2025 puis 2024.
        # String sort: '2025-2026' > '2024-2025'. Donc reverse=True pour avoir les récents en premier.
        results.sort(key=lambda x: (x['campagne'], x['cuvee_nom']), reverse=True)

        return JsonResponse(results, safe=False)

class LotTechniqueVueCuveeDetailsAPI(LoginRequiredMixin, View):
    """
    API pour le détail des lots d'une cuvée/campagne.
    GET /api/production/lots-techniques/par-cuvee/?cuvee_id=...&campagne=...
    """
    def get(self, request, *args, **kwargs):
        org = request.current_org
        cuvee_id = request.GET.get('cuvee_id')
        campagne = request.GET.get('campagne')
        
        qs = LotTechnique.objects.filter(
            cuvee__organization=org
        )
        
        if cuvee_id:
            qs = qs.filter(cuvee_id=cuvee_id)
        else:
            qs = qs.filter(cuvee__isnull=True)
            
        if campagne:
            qs = qs.filter(campagne=campagne)

        # Appliquer aussi les filtres globaux si nécessaire (search, status) pour cohérence
        # (Optionnel selon l'UX : si on déplie, on veut voir tout ou juste ce qui matche ?)
        # Spec UX : "Reload des lots pour cette cuvée si ce n’est pas déjà fait"
        # Si le compteur dit "3 lots" (filtrés), on s'attend à voir 3 lots.
        
        search = request.GET.get('search', '').strip()
        if search:
             qs = qs.filter(
                Q(cuvee__nom__icontains=search) |
                Q(code__icontains=search) |
                Q(contenant__icontains=search)
            )
            
        statuts = request.GET.get('statuts')
        if statuts:
            statut_list = [s.strip() for s in statuts.split(',') if s.strip()]
            if statut_list:
                qs = qs.filter(statut__in=statut_list)

        lots_data = []
        for lot in qs.select_related('cuvee', 'source').order_by('code'):
            # Type contenant heuristique
            cont_type = 'autre'
            c_lower = lot.contenant.lower()
            if 'cuve' in c_lower: cont_type = 'cuve'
            elif 'barrique' in c_lower or lot.contenant.startswith('B-'): cont_type = 'barrique'
            
            # Dernier mouvement (naïf, à optimiser avec annotate/subquery si lent)
            last_move = lot.mouvements.order_by('-date').first()
            
            lots_data.append({
                "id": str(lot.id),
                "code": lot.code,
                "cuvee_id": str(lot.cuvee_id) if lot.cuvee_id else None,
                "cuvee_nom": lot.cuvee.nom if lot.cuvee else 'Sans cuvée',
                "campagne": lot.campagne,
                "contenant_code": lot.contenant,
                "contenant_type": cont_type,
                "volume_l": float(lot.volume_l),
                "statut": lot.statut,
                "statut_display": lot.get_statut_display(),
                "dernier_mouvement_date": last_move.date.strftime('%Y-%m-%d') if last_move else None,
                "dernier_mouvement_type": last_move.get_type_display() if last_move else None
            })

        return JsonResponse(lots_data, safe=False)

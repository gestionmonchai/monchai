"""
Vues pour l'onboarding
 - Checklist d'orga (roadmap 09 existante)
 - Parcours guidé métier (parcelles→ventes)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.accounts.decorators import require_membership
from apps.accounts.utils import checklist_service
from apps.onboarding.models import OnboardingState


@require_membership(role_min='read_only')
def checklist_view(request):
    organization = request.current_org
    checklist = checklist_service.get_or_create_checklist(organization)
    progress = checklist.get_progress()
    completed_count = checklist.get_completed_count()
    total_tasks = 4
    tasks = checklist.get_task_info()
    is_completed = checklist.is_completed()
    context = {
        'checklist': checklist,
        'tasks': tasks,
        'progress': progress,
        'completed_count': completed_count,
        'total_tasks': total_tasks,
        'is_completed': is_completed,
        'organization': organization,
    }
    return render(request, 'onboarding/checklist.html', context)


# ============================================================================
# Parcours guidé métier
# ============================================================================

def _sync_onboarding_from_data(org) -> OnboardingState:
    st, _ = OnboardingState.objects.get_or_create(organization=org)
    st.ensure_all_keys()
    try:
        from apps.referentiels.models import Parcelle as RefParcelle
        if RefParcelle.objects.filter(organization=org).exists():
            st.state['parcelles'] = 'done'
            st.last_step_completed = st.last_step_completed or 'parcelles'
    except Exception:
        pass
    try:
        from apps.production.models import VendangeReception, LotTechnique
        if VendangeReception.objects.filter(organization=org).exists():
            st.state['vendanges'] = 'done'
            st.last_step_completed = st.last_step_completed or 'vendanges'
        # lots + encuvages
        if LotTechnique.objects.filter(cuvee__organization=org).exists():
            st.state['lots'] = 'done'
            st.state['encuvages'] = 'done'
            st.last_step_completed = st.last_step_completed or 'encuvages'
    except Exception:
        pass
    try:
        from apps.viticulture.models_extended import LotIntervention, LotMeasurement
        if LotIntervention.objects.filter(organization=org, type='pressurage').exists():
            st.state['pressurages'] = 'done'
            st.last_step_completed = st.last_step_completed or 'pressurages'
        if LotIntervention.objects.filter(organization=org).exclude(type='pressurage').exists() or \
           LotMeasurement.objects.filter(organization=org).exists():
            st.state['elevage'] = 'done'
            st.last_step_completed = st.last_step_completed or 'elevage'
    except Exception:
        pass
    try:
        from apps.produits.models import Mise, LotCommercial
        if Mise.objects.filter().exists() or LotCommercial.objects.filter().exists():
            st.state['mises'] = 'done'
            st.last_step_completed = st.last_step_completed or 'mises'
    except Exception:
        pass
    try:
        from apps.stock.models import StockSKUBalance
        if StockSKUBalance.objects.filter(organization=org, qty_units__gt=0).exists():
            st.state['stocks'] = 'done'
            st.last_step_completed = st.last_step_completed or 'stocks'
    except Exception:
        pass
    try:
        from apps.sales.models import Order
        if Order.objects.filter(organization=org).exists():
            st.state['ventes'] = 'done'
            st.last_step_completed = st.last_step_completed or 'ventes'
    except Exception:
        pass
    st.save()
    return st


@require_membership(role_min='read_only')
def onboarding_flow(request):
    org = request.current_org
    st = _sync_onboarding_from_data(org)

    steps_def = [
        {
            'key': 'parcelles',
            'title': 'Parcelles',
            'desc': "Déclarez vos parcelles : nom, cépage, superficie et appellation. C’est la base de tout.",
            'create_url': '/referentiels/parcelles/nouvelle/',
        },
        {
            'key': 'vendanges',
            'title': 'Vendanges',
            'desc': "Enregistrez vos vendanges : dates, parcelles, quantités récoltées.",
            'create_url': '/production/vendanges/nouveau/',
        },
        {
            'key': 'pressurages',
            'title': 'Pressurage',
            'desc': "Déclarez la presse associée à la vendange (mode, volumes, rendements).",
            'create_url': '/production/lots-techniques/',
        },
        {
            'key': 'encuvages',
            'title': 'Encuvage',
            'desc': "Indiquez comment le jus entre en cuve : lots, volumes, cépages assemblés.",
            'create_url': '/production/vendanges/',
        },
        {
            'key': 'elevage',
            'title': 'Élevage / Analyses',
            'desc': "Suivez l’évolution de vos cuves : analyses, mouvements, soutirages.",
            'create_url': '/production/lots-elevage/analyses/',
        },
        {
            'key': 'mises',
            'title': 'Mises',
            'desc': "Créez vos opérations de mise en bouteille.",
            'create_url': '/production/mises/nouveau/',
        },
        {
            'key': 'lots',
            'title': 'Lots techniques',
            'desc': "Regroupez vos opérations en lots techniques traçables et cohérents.",
            'create_url': '/production/lots-techniques/nouveau/',
        },
        {
            'key': 'stocks',
            'title': 'Stock',
            'desc': "Calculez automatiquement vos stocks bouteilles.",
            'create_url': '/production/inventaire/',
        },
        {
            'key': 'ventes',
            'title': 'Ventes / Expéditions',
            'desc': "Enregistrez vos ventes pour finaliser la chaîne.",
            'create_url': '/ventes/commandes/nouvelle/',
        },
    ]
    steps = []
    for s in steps_def:
        status = st.state.get(s['key'], 'pending')
        skipped = bool((st.skipped or {}).get(s['key']))
        steps.append({**s, 'status': status, 'skipped': skipped})

    # Determine current step: first not-done and not-skipped; fallback to first pending
    current_index = None
    for idx, s in enumerate(steps):
        if s['status'] != 'done' and not s['skipped']:
            current_index = idx
            break
    if current_index is None:
        for idx, s in enumerate(steps):
            if s['status'] != 'done':
                current_index = idx
                break

    # Compute locked for display: steps after current and not done
    for idx, s in enumerate(steps):
        s['locked'] = (current_index is not None and idx > current_index and s['status'] != 'done')

    current_key = steps[current_index]['key'] if current_index is not None else None
    all_pending = all(x['status'] == 'pending' for x in steps)
    context = {
        'organization': org,
        'state': st,
        'steps': steps,
        'current_key': current_key,
        'current_index': current_index,
        'all_pending': all_pending,
    }
    return render(request, 'onboarding/flow.html', context)


@require_POST
@require_membership(role_min='read_only')
def onboarding_skip_step(request, step_key: str):
    st, _ = OnboardingState.objects.get_or_create(organization=request.current_org)
    st.mark_skipped(step_key)
    if request.headers.get('Hx-Request') == 'true':
        # Render partial content for HTMX swap
        org = request.current_org
        st = _sync_onboarding_from_data(org)
        # Rebuild steps context (same as onboarding_flow)
        steps_def = [
            {'key': 'parcelles', 'title': 'Parcelles', 'desc': "Déclarez vos parcelles : nom, cépage, superficie et appellation. C’est la base de tout.", 'create_url': '/referentiels/parcelles/nouvelle/'},
            {'key': 'vendanges', 'title': 'Vendanges', 'desc': "Enregistrez vos vendanges : dates, parcelles, quantités récoltées.", 'create_url': '/production/vendanges/nouveau/'},
            {'key': 'pressurages', 'title': 'Pressurage', 'desc': "Déclarez la presse associée à la vendange (mode, volumes, rendements).", 'create_url': '/production/lots-techniques/'},
            {'key': 'encuvages', 'title': 'Encuvage', 'desc': "Indiquez comment le jus entre en cuve : lots, volumes, cépages assemblés.", 'create_url': '/production/vendanges/'},
            {'key': 'elevage', 'title': 'Élevage / Analyses', 'desc': "Suivez l’évolution de vos cuves : analyses, mouvements, soutirages.", 'create_url': '/production/lots-elevage/analyses/'},
            {'key': 'mises', 'title': 'Mises', 'desc': "Créez vos opérations de mise en bouteille.", 'create_url': '/production/mises/nouveau/'},
            {'key': 'lots', 'title': 'Lots techniques', 'desc': "Regroupez vos opérations en lots techniques traçables et cohérents.", 'create_url': '/production/lots-techniques/nouveau/'},
            {'key': 'stocks', 'title': 'Stock', 'desc': "Calculez automatiquement vos stocks bouteilles.", 'create_url': '/production/inventaire/'},
            {'key': 'ventes', 'title': 'Ventes / Expéditions', 'desc': "Enregistrez vos ventes pour finaliser la chaîne.", 'create_url': '/ventes/commandes/nouveau/'},
        ]
        steps = []
        for s in steps_def:
            status = st.state.get(s['key'], 'pending')
            skipped = bool((st.skipped or {}).get(s['key']))
            steps.append({**s, 'status': status, 'skipped': skipped})
        current_index = None
        for idx, s in enumerate(steps):
            if s['status'] != 'done' and not s['skipped']:
                current_index = idx
                break
        if current_index is None:
            for idx, s in enumerate(steps):
                if s['status'] != 'done':
                    current_index = idx
                    break
        for idx, s in enumerate(steps):
            s['locked'] = (current_index is not None and idx > current_index and s['status'] != 'done')
        current_key = steps[current_index]['key'] if current_index is not None else None
        context = {'organization': org, 'state': st, 'steps': steps, 'current_key': current_key, 'current_index': current_index}
        from django.shortcuts import render
        return render(request, 'onboarding/_content.html', context)
    return redirect('/onboarding/')


@require_POST
@require_membership(role_min='read_only')
def onboarding_dismiss(request):
    st, _ = OnboardingState.objects.get_or_create(organization=request.current_org)
    st.dismissed = True
    st.save()
    if request.headers.get('Hx-Request') == 'true':
        return render(request, 'components/banner.html', {'type': 'info', 'message': "Onboarding masqué."})
    return redirect('/tableau-de-bord/')


@require_POST
@require_membership(role_min='admin')
def onboarding_reset(request):
    st, _ = OnboardingState.objects.get_or_create(organization=request.current_org)
    st.state = OnboardingState.default_state()
    st.skipped = {k: False for k, _ in OnboardingState.STEPS}
    st.last_step_completed = ''
    st.dismissed = False
    st.completed_at = None
    st.started_at = None
    st.save()
    return redirect('/onboarding/')

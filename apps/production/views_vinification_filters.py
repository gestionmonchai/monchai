from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Q
from apps.viticulture.models_extended import LotIntervention, LotMeasurement

def _vinif_filtered_queryset(request):
    org = getattr(request, 'current_org', None)
    # Filtrer les interventions et mesures de vinification
    vinif_types = [
        'chaptalisation', 'acidification', 'so2', 'batonnage', 
        'fml', 'correction', 'remontage', 'pigeage', 
        'debourbage', 'inoculation_levures', 'inoculation_bacteries',
        'delestage', 'debut_fa', 'fin_fa', 'debut_fml', 'fin_fml'
    ]
    meas_types = ['densite', 'temperature']
    
    # On doit merger deux querysets hétérogènes... ou alors on renvoie une liste d'objets standardisés
    # Pour le filtrage SQL efficace, c'est compliqué si on merge en Python.
    # Cependant, vu le volume, on peut peut-être filtrer séparément.
    
    # Paramètres
    params = request.POST if request.method == 'POST' else request.GET
    q = (params.get('q') or '').strip()
    type_op = (params.get('type') or '').strip()
    lot_code = (params.get('lot') or '').strip()
    date_start = (params.get('date_start') or '').strip()
    date_end = (params.get('date_end') or '').strip()
    
    # 1. Interventions
    qs_i = LotIntervention.objects.filter(organization=org, type__in=vinif_types).select_related('lot')
    if q:
        qs_i = qs_i.filter(Q(lot__code__icontains=q) | Q(notes__icontains=q))
    if lot_code:
        qs_i = qs_i.filter(lot__code__icontains=lot_code)
    if type_op:
        qs_i = qs_i.filter(type=type_op)
    if date_start:
        qs_i = qs_i.filter(date__gte=date_start)
    if date_end:
        qs_i = qs_i.filter(date__lte=date_end)
        
    # 2. Mesures
    qs_m = LotMeasurement.objects.filter(lot__organization=org, type__in=meas_types).select_related('lot')
    if q:
        qs_m = qs_m.filter(Q(lot__code__icontains=q) | Q(notes__icontains=q))
    if lot_code:
        qs_m = qs_m.filter(lot__code__icontains=lot_code)
    if type_op:
        qs_m = qs_m.filter(type=type_op)
    if date_start:
        qs_m = qs_m.filter(date__gte=date_start)
    if date_end:
        qs_m = qs_m.filter(date__lte=date_end)
        
    # Fusion
    operations = []
    for i in qs_i:
        operations.append({
            'date': i.date,
            'lot': i.lot,
            'type_display': i.get_type_display(),
            'type_code': i.type,
            'valeur': i.volume_in_l or i.volume_out_l,
            'notes': i.notes,
            'source': 'intervention',
            'obj': i
        })
    for m in qs_m:
        d = m.date.date() if hasattr(m.date, 'date') else m.date
        operations.append({
            'date': d,
            'lot': m.lot,
            'type_display': m.get_type_display(),
            'type_code': m.type,
            'valeur': f"{m.value} {m.unit}",
            'notes': m.notes,
            'source': 'measurement',
            'obj': m
        })
        
    # Sort
    operations.sort(key=lambda x: x['date'], reverse=True)
    return operations

@method_decorator(login_required, name='dispatch')
class VinificationTableView(TemplateView):
    template_name = 'production/_vinification_table.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ops = _vinif_filtered_queryset(self.request)
        # Pagination manuelle car liste d'objets
        from django.core.paginator import Paginator
        paginator = Paginator(ops, 25)
        page = self.request.GET.get('page', 1)
        ctx['operations'] = paginator.get_page(page)
        ctx['total_count'] = len(ops)
        try:
            qs = self.request.GET.copy()
            if 'page' in qs: qs.pop('page')
            ctx['querystring'] = qs.urlencode()
        except: ctx['querystring'] = ''
        return ctx

"""
Dashboard de monitoring GIGA ROADMAP S4
Métriques de performance et comparaison v1 vs v2
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.metadata.models import SearchMetrics, FeatureFlag


@staff_member_required
def monitoring_dashboard(request):
    """Dashboard de monitoring pour staff uniquement"""
    
    # Période d'analyse (7 derniers jours)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # Métriques globales
    metrics = SearchMetrics.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )
    
    # Comparaison V1 vs V2
    v1_metrics = metrics.filter(engine_version='v1')
    v2_metrics = metrics.filter(engine_version='v2')
    
    # Performance moyenne
    v1_avg_latency = v1_metrics.aggregate(avg=Avg('elapsed_ms'))['avg'] or 0
    v2_avg_latency = v2_metrics.aggregate(avg=Avg('elapsed_ms'))['avg'] or 0
    
    # Taux de succès (résultats > 0)
    v1_success_rate = calculate_success_rate(v1_metrics)
    v2_success_rate = calculate_success_rate(v2_metrics)
    
    # Cache hit rate
    v1_cache_rate = calculate_cache_rate(v1_metrics)
    v2_cache_rate = calculate_cache_rate(v2_metrics)
    
    # Feature flags status
    flags_status = []
    for flag in FeatureFlag.objects.all().order_by('name'):
        flags_status.append({
            'name': flag.name,
            'enabled': flag.is_enabled,
            'percentage': flag.rollout_percentage,
            'description': flag.description[:100] + '...' if len(flag.description) > 100 else flag.description,
        })
    
    # Top entités recherchées
    top_entities = (
        metrics.values('entity_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Recherches sans résultat (à optimiser)
    zero_results = metrics.filter(has_results=False).count()
    total_searches = metrics.count()
    zero_result_rate = (zero_results / total_searches * 100) if total_searches > 0 else 0
    
    context = {
        'period_days': 7,
        'total_searches': total_searches,
        'v1_count': v1_metrics.count(),
        'v2_count': v2_metrics.count(),
        'v1_avg_latency': round(v1_avg_latency, 1),
        'v2_avg_latency': round(v2_avg_latency, 1),
        'v1_success_rate': round(v1_success_rate, 1),
        'v2_success_rate': round(v2_success_rate, 1),
        'v1_cache_rate': round(v1_cache_rate, 1),
        'v2_cache_rate': round(v2_cache_rate, 1),
        'zero_result_rate': round(zero_result_rate, 1),
        'flags_status': flags_status,
        'top_entities': top_entities,
        'performance_improvement': calculate_improvement(v1_avg_latency, v2_avg_latency),
    }
    
    return render(request, 'metadata/monitoring_dashboard.html', context)


def calculate_success_rate(queryset):
    """Calcule le taux de succès (recherches avec résultats)"""
    total = queryset.count()
    if total == 0:
        return 0
    success = queryset.filter(has_results=True).count()
    return (success / total) * 100


def calculate_cache_rate(queryset):
    """Calcule le taux de cache hit"""
    total = queryset.count()
    if total == 0:
        return 0
    cache_hits = queryset.filter(cache_hit=True).count()
    return (cache_hits / total) * 100


def calculate_improvement(v1_value, v2_value):
    """Calcule l'amélioration en pourcentage"""
    if v1_value == 0:
        return 0
    return ((v1_value - v2_value) / v1_value) * 100


@staff_member_required
def feature_flags_admin(request):
    """Interface d'administration des feature flags"""
    
    if request.method == 'POST':
        flag_name = request.POST.get('flag_name')
        action = request.POST.get('action')
        percentage = int(request.POST.get('percentage', 0))
        
        try:
            flag = FeatureFlag.objects.get(name=flag_name)
            
            if action == 'enable':
                flag.is_enabled = True
                flag.rollout_percentage = percentage
            elif action == 'disable':
                flag.is_enabled = False
                flag.rollout_percentage = 0
            elif action == 'update_percentage':
                flag.rollout_percentage = percentage
            
            flag.save()
            
            # Message de succès (à implémenter avec Django messages)
            
        except FeatureFlag.DoesNotExist:
            pass
    
    flags = FeatureFlag.objects.all().order_by('name')
    
    context = {
        'flags': flags,
    }
    
    return render(request, 'metadata/feature_flags_admin.html', context)

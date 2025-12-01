# Check-list Sécurité - Mon Chai V1

## Date : 2025-09-24

## 🛡️ Stratégie de Sécurité

### Principe Fondamental
**"Refus par défaut"** - Aucune vue sensible n'est accessible sans authentification et autorisation explicites.

### Niveaux de Protection
1. **Authentification** - L'utilisateur est-il connecté ?
2. **Autorisation** - A-t-il le rôle requis ?
3. **Scopes** - A-t-il accès aux données demandées ?
4. **Organisation** - Les données appartiennent-elles à son organisation ?

---

## 🔐 Middleware de Sécurité

### 1. Middleware Organisation Courante

```python
# apps/core/middleware.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from apps.accounts.models import Organization

class OrganizationMiddleware:
    """Middleware pour gérer l'organisation courante de l'utilisateur"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            self.set_current_organization(request)
        
        response = self.get_response(request)
        return response
    
    def set_current_organization(self, request):
        """Définit l'organisation courante pour l'utilisateur"""
        # Vérifier si une organisation est déjà en session
        org_id = request.session.get('current_org_id')
        
        if org_id:
            try:
                org = Organization.objects.get(id=org_id)
                # Vérifier que l'utilisateur a toujours accès
                if request.user.memberships.filter(organization=org).exists():
                    request.current_org = org
                    return
            except Organization.DoesNotExist:
                pass
        
        # Sélectionner la première organisation disponible
        membership = request.user.memberships.first()
        if membership:
            request.current_org = membership.organization
            request.session['current_org_id'] = str(membership.organization.id)
        else:
            # Utilisateur sans organisation - rediriger vers onboarding
            request.current_org = None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Vérifications avant chaque vue"""
        # Ignorer les vues publiques
        if getattr(view_func, 'public_view', False):
            return None
        
        # Vérifier l'organisation pour les vues métier
        if (request.user.is_authenticated and 
            hasattr(request, 'current_org') and 
            request.current_org is None and
            not request.path.startswith('/auth/')):
            
            return redirect('auth:first_run')
        
        return None
```

### 2. Middleware de Vérification des Scopes

```python
# apps/core/middleware.py
from functools import wraps
from django.http import HttpResponseForbidden
from django.core.cache import cache

class ScopeMiddleware:
    """Middleware pour vérifier les scopes utilisateur"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_scopes = self.get_user_scopes(request.user, request.current_org)
        
        return self.get_response(request)
    
    def get_user_scopes(self, user, organization):
        """Récupère les scopes de l'utilisateur avec cache"""
        if not organization:
            return []
        
        cache_key = f"user_scopes:{user.id}:{organization.id}"
        scopes = cache.get(cache_key)
        
        if scopes is None:
            # Récupérer depuis la base de données
            scopes = list(
                user.organization_scopes
                .filter(organization=organization, is_active=True)
                .values_list('scope_domain', 'scope_level')
            )
            cache.set(cache_key, scopes, 300)  # 5 minutes
        
        return scopes
    
    def has_scope(self, user_scopes, required_scope):
        """Vérifie si l'utilisateur a le scope requis"""
        domain, level = required_scope.split(':')
        return (domain, level) in user_scopes
```

---

## 🔒 Décorateurs de Sécurité

### 1. Décorateur d'Authentification Renforcée

```python
# apps/core/decorators.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def require_organization(view_func):
    """Décorateur qui exige une organisation courante"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'current_org') or request.current_org is None:
            return redirect('auth:first_run')
        return view_func(request, *args, **kwargs)
    return wrapper

def require_scope(*required_scopes):
    """Décorateur qui exige des scopes spécifiques"""
    def decorator(view_func):
        @wraps(view_func)
        @require_organization
        def wrapper(request, *args, **kwargs):
            user_scopes = getattr(request, 'user_scopes', [])
            
            for scope in required_scopes:
                if not has_scope(user_scopes, scope):
                    return HttpResponseForbidden(
                        f"Accès refusé. Scope requis : {scope}"
                    )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_membership(*roles):
    """Décorateur qui exige des rôles spécifiques (existant, amélioré)"""
    def decorator(view_func):
        @wraps(view_func)
        @require_organization
        def wrapper(request, *args, **kwargs):
            membership = request.user.memberships.filter(
                organization=request.current_org
            ).first()
            
            if not membership or membership.role not in roles:
                return HttpResponseForbidden(
                    f"Accès refusé. Rôle requis : {', '.join(roles)}"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2. Décorateur de Validation Cross-Organisation

```python
def validate_same_organization(model_class, param_name='pk'):
    """Décorateur qui valide que l'objet appartient à l'organisation courante"""
    def decorator(view_func):
        @wraps(view_func)
        @require_organization
        def wrapper(request, *args, **kwargs):
            obj_id = kwargs.get(param_name)
            if obj_id:
                try:
                    obj = model_class.objects.get(pk=obj_id)
                    if obj.organization != request.current_org:
                        return HttpResponseForbidden(
                            "Accès refusé. Objet non accessible."
                        )
                except model_class.DoesNotExist:
                    return HttpResponseForbidden("Objet non trouvé.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## 📋 Check-list par Type de Vue

### 1. Vues de Liste (Index)

```python
# Exemple : apps/clients/views.py
@require_organization
@require_scope('clients:read')
def customers_list(request):
    """✅ SÉCURISÉ - Liste des clients"""
    # Filtrage automatique par organisation
    customers = Customer.objects.filter(organization=request.current_org)
    
    # Log d'accès pour audit
    logger.info("clients_list_accessed", 
        user_id=request.user.id,
        organization_id=request.current_org.id,
        count=customers.count()
    )
    
    return render(request, 'clients/list.html', {'customers': customers})
```

**Check-list Vues de Liste :**
- [ ] `@require_organization` présent
- [ ] `@require_scope('domain:read')` présent  
- [ ] Filtrage par `organization=request.current_org`
- [ ] Log d'accès pour audit
- [ ] Pagination sécurisée (pas de fuite d'infos)

### 2. Vues de Détail

```python
# Exemple : apps/clients/views.py
@require_organization
@require_scope('clients:read')
@validate_same_organization(Customer, 'customer_id')
def customer_detail(request, customer_id):
    """✅ SÉCURISÉ - Détail client"""
    customer = get_object_or_404(
        Customer, 
        pk=customer_id,
        organization=request.current_org
    )
    
    # Log d'accès pour audit
    logger.info("customer_detail_accessed",
        user_id=request.user.id,
        customer_id=customer_id,
        organization_id=request.current_org.id
    )
    
    return render(request, 'clients/detail.html', {'customer': customer})
```

**Check-list Vues de Détail :**
- [ ] `@require_organization` présent
- [ ] `@require_scope('domain:read')` présent
- [ ] `@validate_same_organization` présent
- [ ] `get_object_or_404` avec filtrage organisation
- [ ] Log d'accès avec ID objet

### 3. Vues de Création

```python
# Exemple : apps/clients/views.py
@require_organization
@require_scope('clients:write')
def customer_create(request):
    """✅ SÉCURISÉ - Création client"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.organization = request.current_org
            customer.created_by = request.user
            customer.save()
            
            # Log de création pour audit
            logger.info("customer_created",
                user_id=request.user.id,
                customer_id=customer.id,
                organization_id=request.current_org.id
            )
            
            return redirect('clients:detail', customer_id=customer.id)
    else:
        form = CustomerForm()
    
    return render(request, 'clients/form.html', {'form': form})
```

**Check-list Vues de Création :**
- [ ] `@require_organization` présent
- [ ] `@require_scope('domain:write')` présent
- [ ] `obj.organization = request.current_org` avant save
- [ ] `obj.created_by = request.user` pour audit
- [ ] Log de création avec ID généré

### 4. Vues de Modification

```python
# Exemple : apps/clients/views.py
@require_organization
@require_scope('clients:write')
@validate_same_organization(Customer, 'customer_id')
def customer_edit(request, customer_id):
    """✅ SÉCURISÉ - Modification client"""
    customer = get_object_or_404(
        Customer,
        pk=customer_id,
        organization=request.current_org
    )
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_by = request.user
            customer.save()
            
            # Log de modification pour audit
            logger.info("customer_updated",
                user_id=request.user.id,
                customer_id=customer.id,
                organization_id=request.current_org.id
            )
            
            return redirect('clients:detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'clients/form.html', {'form': form, 'customer': customer})
```

**Check-list Vues de Modification :**
- [ ] `@require_organization` présent
- [ ] `@require_scope('domain:write')` présent
- [ ] `@validate_same_organization` présent
- [ ] `get_object_or_404` avec filtrage organisation
- [ ] `obj.updated_by = request.user` avant save
- [ ] Log de modification avec changements

### 5. Vues de Suppression

```python
# Exemple : apps/clients/views.py
@require_organization
@require_scope('clients:delete')
@validate_same_organization(Customer, 'customer_id')
def customer_delete(request, customer_id):
    """✅ SÉCURISÉ - Suppression client"""
    customer = get_object_or_404(
        Customer,
        pk=customer_id,
        organization=request.current_org
    )
    
    if request.method == 'POST':
        # Suppression logique préférée
        customer.is_active = False
        customer.deleted_by = request.user
        customer.deleted_at = timezone.now()
        customer.save()
        
        # Log de suppression pour audit
        logger.warning("customer_deleted",
            user_id=request.user.id,
            customer_id=customer.id,
            customer_name=customer.name,
            organization_id=request.current_org.id
        )
        
        return redirect('clients:list')
    
    return render(request, 'clients/confirm_delete.html', {'customer': customer})
```

**Check-list Vues de Suppression :**
- [ ] `@require_organization` présent
- [ ] `@require_scope('domain:delete')` présent
- [ ] `@validate_same_organization` présent
- [ ] Suppression logique préférée (is_active=False)
- [ ] `obj.deleted_by = request.user` pour audit
- [ ] Log WARNING pour suppression
- [ ] Confirmation utilisateur obligatoire

---

## 🌐 Sécurité API

### 1. Décorateurs API

```python
# apps/api/decorators.py
from django.http import JsonResponse
from functools import wraps
import json

def api_require_scope(*required_scopes):
    """Décorateur pour API avec réponse JSON"""
    def decorator(view_func):
        @wraps(view_func)
        @require_organization
        def wrapper(request, *args, **kwargs):
            user_scopes = getattr(request, 'user_scopes', [])
            
            for scope in required_scopes:
                if not has_scope(user_scopes, scope):
                    return JsonResponse({
                        'error': 'Accès refusé',
                        'required_scope': scope,
                        'user_scopes': [f"{d}:{l}" for d, l in user_scopes]
                    }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def api_validate_json(view_func):
    """Décorateur pour valider le JSON en entrée"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                request.json = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'JSON invalide'
                }, status=400)
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 2. Exemple Vue API Sécurisée

```python
# apps/api/v1/clients.py
@api_require_scope('clients:read')
@api_validate_json
def clients_api(request):
    """✅ SÉCURISÉ - API clients"""
    if request.method == 'GET':
        clients = Customer.objects.filter(
            organization=request.current_org,
            is_active=True
        )
        
        # Sérialisation sécurisée (pas de données sensibles)
        data = [{
            'id': str(c.id),
            'name': c.name,
            'segment': c.segment,
            'created_at': c.created_at.isoformat(),
        } for c in clients]
        
        return JsonResponse({'clients': data})
    
    elif request.method == 'POST':
        # Vérifier scope écriture
        if not has_scope(request.user_scopes, 'clients:write'):
            return JsonResponse({'error': 'Scope écriture requis'}, status=403)
        
        # Validation et création...
        pass
```

---

## 📊 Journalisation et Audit

### 1. Configuration Logging Sécurisé

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{asctime}] {levelname} SECURITY {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10*1024*1024,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. Logs d'Audit Standardisés

```python
# apps/core/audit.py
import logging
from django.utils import timezone

security_logger = logging.getLogger('security')

class AuditLogger:
    @staticmethod
    def log_access(user, organization, resource_type, resource_id=None, action='read'):
        """Log d'accès aux ressources"""
        security_logger.info(
            f"ACCESS {action.upper()} {resource_type} "
            f"user={user.id} org={organization.id} resource={resource_id}"
        )
    
    @staticmethod
    def log_permission_denied(user, required_scope, current_scopes, resource):
        """Log de refus d'accès"""
        security_logger.warning(
            f"PERMISSION_DENIED user={user.id} "
            f"required={required_scope} current={current_scopes} "
            f"resource={resource}"
        )
    
    @staticmethod
    def log_suspicious_activity(user, activity_type, details):
        """Log d'activité suspecte"""
        security_logger.error(
            f"SUSPICIOUS_ACTIVITY {activity_type} "
            f"user={user.id} details={details}"
        )
```

---

## 🚨 Détection d'Anomalies

### 1. Middleware de Détection

```python
# apps/core/middleware.py
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone

class SecurityMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            self.check_suspicious_activity(request)
        
        response = self.get_response(request)
        return response
    
    def check_suspicious_activity(self, request):
        """Détecte les activités suspectes"""
        user_id = request.user.id
        now = timezone.now()
        
        # Vérifier le taux de requêtes
        cache_key = f"request_rate:{user_id}"
        requests = cache.get(cache_key, [])
        
        # Nettoyer les requêtes anciennes (> 1 minute)
        recent_requests = [
            req_time for req_time in requests 
            if now - req_time < timedelta(minutes=1)
        ]
        recent_requests.append(now)
        
        cache.set(cache_key, recent_requests, 300)  # 5 minutes
        
        # Alerte si > 60 requêtes/minute
        if len(recent_requests) > 60:
            AuditLogger.log_suspicious_activity(
                request.user,
                'HIGH_REQUEST_RATE',
                f'{len(recent_requests)} requests in 1 minute'
            )
    
    def check_cross_org_access(self, request):
        """Détecte les tentatives d'accès cross-organisation"""
        if hasattr(request, 'current_org'):
            # Vérifier si l'utilisateur change souvent d'organisation
            cache_key = f"org_switches:{request.user.id}"
            switches = cache.get(cache_key, [])
            
            if switches and switches[-1] != request.current_org.id:
                switches.append(request.current_org.id)
                
                # Alerte si > 5 changements d'org en 10 minutes
                if len(switches) > 5:
                    AuditLogger.log_suspicious_activity(
                        request.user,
                        'FREQUENT_ORG_SWITCHES',
                        f'Switched between {len(set(switches))} organizations'
                    )
            
            cache.set(cache_key, switches[-10:], 600)  # Garder 10 derniers
```

---

## 📋 Check-list Finale de Sécurité

### Authentification & Autorisation
- [ ] Toutes les vues métier ont `@login_required` ou `@require_organization`
- [ ] Toutes les vues sensibles ont `@require_scope`
- [ ] Aucune vue critique accessible anonymement
- [ ] Rôles et scopes vérifiés côté serveur (jamais côté client uniquement)

### Isolation Multi-Tenant
- [ ] Tous les querysets filtrent par `organization=request.current_org`
- [ ] Décorateur `@validate_same_organization` sur vues de détail/modification
- [ ] Aucune fuite de données cross-organisation possible
- [ ] Tests de sécurité cross-org implémentés

### API & AJAX
- [ ] Toutes les API ont des décorateurs de sécurité appropriés
- [ ] Validation JSON côté serveur
- [ ] Pas de données sensibles dans les réponses JSON
- [ ] Rate limiting implémenté

### Audit & Monitoring
- [ ] Logs d'accès pour toutes les actions sensibles
- [ ] Logs de sécurité séparés des logs applicatifs
- [ ] Détection d'activités suspectes active
- [ ] Alertes automatiques configurées

### Données Sensibles
- [ ] Mots de passe jamais en clair
- [ ] Données PII masquées selon les rôles
- [ ] Suppression logique préférée à la suppression physique
- [ ] Audit trail complet (qui, quoi, quand)

---

**Check-list sécurité définie : 4 niveaux de protection + monitoring automatique**

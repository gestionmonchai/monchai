# Plan de Migration - Mon Chai V1

## Date : 2025-09-24

## 🎯 Objectif de la Migration

Migrer de l'architecture actuelle vers la nouvelle architecture avec :
- Séparation `/admin/` technique vs `/backoffice/` métier
- URLs canoniques et namespaces organisés
- RBAC + Scopes avec permissions granulaires
- Rétro-compatibilité garantie via redirections 301

---

## 👥 Mapping Utilisateurs → Rôles

### Stratégie de Migration des Rôles

#### Utilisateurs Actuels → Nouveaux Rôles
```python
# Mapping automatique basé sur les permissions Django actuelles
ROLE_MAPPING = {
    # Superusers Django → SuperAdmin
    'is_superuser=True': 'SuperAdmin',
    
    # Staff avec toutes permissions → AdminOrganisation  
    'is_staff=True + all_permissions': 'AdminOrganisation',
    
    # Staff avec permissions limitées → Manager
    'is_staff=True + limited_permissions': 'Manager',
    
    # Utilisateurs avec permissions comptables → Comptabilité
    'has_billing_permissions': 'Comptabilité',
    
    # Utilisateurs avec permissions stock → Opérateur
    'has_stock_permissions': 'Opérateur',
    
    # Utilisateurs sans permissions spéciales → LectureSeule
    'default': 'LectureSeule'
}
```

#### Script de Migration des Rôles
```python
# management/commands/migrate_user_roles.py
from django.core.management.base import BaseCommand
from apps.accounts.models import User, Membership

class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            for membership in user.memberships.all():
                # Déterminer le nouveau rôle
                new_role = self.determine_new_role(user, membership)
                
                # Migrer vers le nouveau système
                membership.role = new_role
                membership.save()
                
                self.stdout.write(f"Migré {user.email} → {new_role}")
    
    def determine_new_role(self, user, membership):
        if user.is_superuser:
            return 'superadmin'
        elif user.is_staff and self.has_all_permissions(user):
            return 'admin_organisation'
        elif user.is_staff:
            return 'manager'
        elif self.has_billing_permissions(user):
            return 'comptabilite'
        elif self.has_stock_permissions(user):
            return 'operateur'
        else:
            return 'lecture_seule'
```

---

## 🔐 Attribution Initiale des Scopes

### Stratégie Conservative (Lecture Seule d'abord)

#### Phase 1 : Attribution Minimale
```python
# Tous les utilisateurs commencent avec lecture seule
INITIAL_SCOPES = {
    'SuperAdmin': [
        'catalogue:read', 'catalogue:write', 'catalogue:delete',
        'clients:read', 'clients:write', 'clients:delete', 
        'ventes:read', 'ventes:write', 'ventes:financial',
        'stocks:read', 'stocks:write', 'stocks:manage',
        'referentiels:read', 'referentiels:write',
        'parametres:read', 'parametres:write', 'parametres:admin'
    ],
    
    'AdminOrganisation': [
        'catalogue:read', 'clients:read', 'ventes:read', 
        'stocks:read', 'referentiels:read', 'parametres:read'
    ],
    
    'Manager': [
        'catalogue:read', 'clients:read', 'stocks:read', 'referentiels:read'
    ],
    
    'Comptabilité': [
        'clients:read', 'ventes:read', 'ventes:financial'
    ],
    
    'Opérateur': [
        'catalogue:read', 'stocks:read'
    ],
    
    'LectureSeule': [
        'catalogue:read'
    ]
}
```

#### Phase 2 : Élargissement Progressif (après validation)
```python
# Après 1 semaine de validation, élargir les scopes
EXPANDED_SCOPES = {
    'AdminOrganisation': [
        # Ajouter les droits d'écriture
        'catalogue:write', 'clients:write', 'ventes:write',
        'stocks:write', 'referentiels:write', 'parametres:write'
    ],
    
    'Manager': [
        # Ajouter les droits d'écriture sur son périmètre
        'catalogue:write', 'clients:write', 'stocks:write'
    ],
    
    'Comptabilité': [
        # Ajouter les droits financiers complets
        'ventes:write', 'ventes:validate'
    ],
    
    'Opérateur': [
        # Ajouter les droits de saisie stock
        'stocks:write', 'stocks:inventory'
    ]
}
```

---

## 🚩 Feature Flags pour Activation Progressive

### Configuration des Feature Flags

#### Flags Principaux
```python
# apps/metadata/models.py - Extension du modèle existant
ROUTING_FEATURE_FLAGS = {
    # Migration globale
    'new_routing_enabled': {
        'default': False,
        'description': 'Active le nouveau système de routage'
    },
    
    # Par domaine métier
    'backoffice_enabled': {
        'default': False,
        'description': 'Active l\'interface /backoffice/'
    },
    
    'ventes_module_enabled': {
        'default': False,
        'description': 'Active le module /ventes/'
    },
    
    'rbac_scopes_enabled': {
        'default': False,
        'description': 'Active le système RBAC + Scopes'
    },
    
    # Par organisation (granularité fine)
    'org_migration_enabled': {
        'default': False,
        'description': 'Active la migration pour une organisation spécifique',
        'scope': 'organization'  # Flag par organisation
    }
}
```

#### Middleware de Feature Flags
```python
# apps/metadata/middleware.py
class FeatureFlagMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ajouter les flags au contexte de la requête
        request.feature_flags = self.get_feature_flags(request)
        return self.get_response(request)
    
    def get_feature_flags(self, request):
        flags = {}
        
        # Flags globaux
        flags['new_routing'] = FeatureFlag.is_enabled('new_routing_enabled')
        flags['backoffice'] = FeatureFlag.is_enabled('backoffice_enabled')
        
        # Flags par organisation
        if hasattr(request, 'current_org'):
            flags['org_migration'] = FeatureFlag.is_enabled(
                'org_migration_enabled', 
                organization=request.current_org
            )
        
        return flags
```

---

## 🔄 Activation des Redirections 301

### Stratégie de Déploiement des Redirections

#### Étape 1 : Redirections Critiques (Jour J)
```python
# monchai/urls.py - Ajout des redirections prioritaires
from django.views.generic import RedirectView

# Redirections critiques (clients, ventes)
CRITICAL_REDIRECTS = [
    # Clients
    path('admin/sales/customer/', 
         RedirectView.as_view(url='/clients/', permanent=True)),
    
    # Ventes (si module activé)
    path('admin/sales/quote/', 
         RedirectView.as_view(url='/ventes/devis/', permanent=True)),
    path('admin/sales/order/', 
         RedirectView.as_view(url='/ventes/commandes/', permanent=True)),
    
    # Facturation
    path('admin/billing/invoice/', 
         RedirectView.as_view(url='/ventes/factures/', permanent=True)),
]
```

#### Étape 2 : Redirections Complètes (Jour J+7)
```python
# Toutes les redirections du fichier redirects_map.csv
COMPLETE_REDIRECTS = [
    # API versioning
    path('api/auth/<path:path>', 
         RedirectView.as_view(url='/api/v1/auth/%(path)s', permanent=True)),
    
    # Référentiels
    path('ref/<path:path>', 
         RedirectView.as_view(url='/referentiels/%(path)s', permanent=True)),
    
    # Paramètres
    path('auth/settings/<path:path>', 
         RedirectView.as_view(url='/backoffice/parametres/%(path)s', permanent=True)),
]
```

#### Middleware de Redirection Intelligente
```python
# apps/core/middleware.py
class SmartRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.redirect_map = self.load_redirect_map()
    
    def __call__(self, request):
        # Vérifier si l'URL nécessite une redirection
        if request.path in self.redirect_map:
            new_url = self.redirect_map[request.path]
            
            # Log de la redirection pour monitoring
            logger.info(f"Redirection 301: {request.path} → {new_url}")
            
            return HttpResponsePermanentRedirect(new_url)
        
        return self.get_response(request)
    
    def load_redirect_map(self):
        # Charger depuis redirects_map.csv
        return {
            '/admin/sales/customer/': '/clients/',
            '/ref/': '/referentiels/',
            # ... autres redirections
        }
```

---

## 📊 Plan de Rollback

### Stratégie de Retour Arrière

#### Rollback Niveau 1 : Désactivation Feature Flags
```python
# Rollback immédiat sans redéploiement
def emergency_rollback():
    # Désactiver tous les nouveaux flags
    FeatureFlag.objects.filter(
        key__in=['new_routing_enabled', 'backoffice_enabled', 'rbac_scopes_enabled']
    ).update(is_active=False)
    
    # Forcer le cache refresh
    cache.delete_pattern('feature_flag:*')
    
    print("✅ Rollback niveau 1 effectué - retour à l'ancien système")
```

#### Rollback Niveau 2 : Désactivation Redirections
```python
# apps/core/middleware.py
class SmartRedirectMiddleware:
    def __call__(self, request):
        # Vérifier le flag de rollback
        if not FeatureFlag.is_enabled('redirections_enabled'):
            return self.get_response(request)  # Pas de redirection
        
        # Logique normale de redirection
        # ...
```

#### Rollback Niveau 3 : Restauration Base de Données
```sql
-- Sauvegarde avant migration
CREATE TABLE user_roles_backup AS 
SELECT * FROM accounts_membership;

-- Rollback si nécessaire
TRUNCATE accounts_membership;
INSERT INTO accounts_membership SELECT * FROM user_roles_backup;
```

---

## 📅 Planning de Migration

### Semaine -1 : Préparation
- [ ] **Lundi** : Sauvegarde complète base de données
- [ ] **Mardi** : Tests de migration sur environnement de staging
- [ ] **Mercredi** : Validation des redirections critiques
- [ ] **Jeudi** : Formation équipe sur nouveau système
- [ ] **Vendredi** : Validation finale et go/no-go

### Jour J : Migration
- [ ] **09h00** : Maintenance programmée (30 min)
- [ ] **09h30** : Déploiement nouvelle version avec flags désactivés
- [ ] **10h00** : Activation progressive des redirections critiques
- [ ] **10h30** : Tests de fumée sur fonctionnalités critiques
- [ ] **11h00** : Activation feature flag `new_routing_enabled`
- [ ] **11h30** : Monitoring intensif des erreurs
- [ ] **14h00** : Activation `backoffice_enabled` si tout OK
- [ ] **16h00** : Activation `rbac_scopes_enabled` si tout OK

### Semaine +1 : Stabilisation
- [ ] **Jour J+1** : Monitoring et correction des bugs critiques
- [ ] **Jour J+3** : Activation des redirections complètes
- [ ] **Jour J+5** : Élargissement des scopes utilisateurs
- [ ] **Jour J+7** : Bilan et optimisations

---

## 🔍 Monitoring de la Migration

### Métriques Clés à Surveiller

#### Erreurs HTTP
```python
# Alertes automatiques
MIGRATION_ALERTS = {
    '404_rate': {
        'threshold': '> 5% sur 5 min',
        'action': 'Vérifier les redirections manquantes'
    },
    
    '500_rate': {
        'threshold': '> 1% sur 5 min', 
        'action': 'Rollback niveau 1 immédiat'
    },
    
    'redirect_rate': {
        'threshold': '> 50% sur 10 min',
        'action': 'Vérifier la charge serveur'
    }
}
```

#### Dashboard de Migration
```python
# apps/metadata/views.py
def migration_dashboard(request):
    stats = {
        'redirections_count': get_redirections_count_last_hour(),
        'error_rate': get_error_rate_last_hour(),
        'users_migrated': get_users_with_new_roles_count(),
        'feature_flags_status': get_all_feature_flags_status(),
    }
    return render(request, 'metadata/migration_dashboard.html', stats)
```

#### Logs Structurés
```python
import structlog

logger = structlog.get_logger()

# Log de redirection
logger.info("url_redirected", 
    old_url=request.path,
    new_url=new_url,
    user_id=request.user.id,
    organization_id=request.current_org.id
)

# Log d'erreur de permission
logger.warning("permission_denied",
    user_id=request.user.id,
    required_scope="clients:write",
    user_scopes=user.scopes,
    url=request.path
)
```

---

## 🧪 Tests de Migration

### Tests Automatisés

#### Test de Redirections
```python
# tests/test_migration.py
class MigrationTestCase(TestCase):
    def test_critical_redirections(self):
        """Test que toutes les redirections critiques fonctionnent"""
        critical_urls = [
            '/admin/sales/customer/',
            '/admin/sales/quote/',
            '/ref/',
            '/auth/settings/billing/',
        ]
        
        for old_url in critical_urls:
            response = self.client.get(old_url)
            self.assertEqual(response.status_code, 301)
            self.assertIn('Location', response.headers)
    
    def test_user_role_migration(self):
        """Test que les rôles utilisateurs sont correctement migrés"""
        # Créer un utilisateur avec ancien système
        user = User.objects.create_user('test@example.com')
        user.is_staff = True
        user.save()
        
        # Exécuter la migration
        call_command('migrate_user_roles')
        
        # Vérifier le nouveau rôle
        membership = user.memberships.first()
        self.assertEqual(membership.role, 'manager')
```

#### Test de Performance
```python
def test_redirection_performance(self):
    """Test que les redirections n'impactent pas trop les performances"""
    start_time = time.time()
    
    for _ in range(100):
        response = self.client.get('/admin/sales/customer/')
        self.assertEqual(response.status_code, 301)
    
    elapsed = time.time() - start_time
    self.assertLess(elapsed, 1.0)  # Moins de 1 seconde pour 100 redirections
```

---

## 📋 Checklist de Migration

### Pré-Migration
- [ ] Sauvegarde base de données complète
- [ ] Tests sur environnement de staging validés
- [ ] Feature flags configurés (désactivés)
- [ ] Redirections critiques testées
- [ ] Équipe formée sur nouveau système
- [ ] Plan de rollback validé

### Migration Jour J
- [ ] Déploiement réussi sans erreur
- [ ] Feature flags activés progressivement
- [ ] Redirections critiques fonctionnelles
- [ ] Tests de fumée passés
- [ ] Monitoring actif sans alerte
- [ ] Utilisateurs migrés vers nouveaux rôles

### Post-Migration
- [ ] Aucune erreur critique pendant 24h
- [ ] Toutes les redirections activées
- [ ] Scopes utilisateurs élargis
- [ ] Performance stable
- [ ] Feedback utilisateurs positif
- [ ] Documentation mise à jour

---

**Plan de migration défini : 3 phases sur 2 semaines avec rollback à chaque étape**

# Scopes par Utilisateur - Mon Chai V1

## Date : 2025-09-24

## 🎯 Définition des Scopes

### Concept
Les **scopes** définissent **quelles données** un utilisateur peut consulter/modifier, indépendamment de son **rôle** qui définit **quelles actions** il peut faire.

### Règle d'or
**Deny by default** : Ce qui n'est pas explicitement accordé est refusé.
**Le plus restrictif gagne** : En cas de conflit rôle vs scope, la restriction la plus forte s'applique.

---

## 🏢 Périmètres par Organisation

### Niveau Organisation
Chaque utilisateur appartient à une ou plusieurs organisations avec des droits différents :

```
Utilisateur Denis:
├── Organisation A (Domaine Château Margaux)
│   ├── Rôle: Manager
│   └── Scopes: catalogue:read+write, clients:read, stocks:read
└── Organisation B (Domaine Pichon Baron) 
    ├── Rôle: LectureSeule
    └── Scopes: catalogue:read
```

### Isolation des données

- **Stricte** : Un utilisateur ne voit QUE les données des organisations auxquelles il a accès
- **Automatique** : Filtrage transparent par middleware
- **Vérifiable** : Logs d'accès pour audit

---

## 📊 Domaines de Scopes

### 1. Catalogue (catalogue:)
**Données concernées :**
- Cuvées, lots, SKU, mouvements de production
- Recettes, assemblages, analyses œnologiques

**Niveaux d'accès :**
- `catalogue:read` - Consultation des produits
- `catalogue:write` - Création/modification des produits
- `catalogue:delete` - Suppression des produits
- `catalogue:export` - Export des données catalogue

### 2. Clients (clients:)
**Données concernées :**
- Fiches clients, contacts, historique
- Segmentation, préférences, notes commerciales

**Niveaux d'accès :**
- `clients:read` - Consultation des clients
- `clients:write` - Création/modification des clients
- `clients:delete` - Suppression des clients
- `clients:export` - Export des données clients

### 3. Ventes (ventes:)
**Données concernées :**
- Devis, commandes, factures, paiements
- Tarifs, remises, conditions commerciales

**Niveaux d'accès :**
- `ventes:read` - Consultation des ventes
- `ventes:write` - Création/modification des ventes
- `ventes:financial` - Accès aux données financières (prix, marges)
- `ventes:validate` - Validation des factures/paiements

### 4. Stocks (stocks:)
**Données concernées :**
- Inventaires, mouvements, transferts
- Alertes, seuils, valorisation

**Niveaux d'accès :**
- `stocks:read` - Consultation des stocks
- `stocks:write` - Saisie des mouvements
- `stocks:manage` - Gestion des seuils/alertes
- `stocks:inventory` - Réalisation d'inventaires

### 5. Référentiels (referentiels:)
**Données concernées :**
- Cépages, parcelles, unités, entrepôts
- Appellations, millésimes, classifications

**Niveaux d'accès :**
- `referentiels:read` - Consultation des référentiels
- `referentiels:write` - Création/modification des référentiels
- `referentiels:import` - Import de données externes

### 6. Paramètres (parametres:)
**Données concernées :**
- Configuration organisation, taxes, devises
- Paramètres de facturation, conditions générales

**Niveaux d'accès :**
- `parametres:read` - Consultation des paramètres
- `parametres:write` - Modification des paramètres
- `parametres:admin` - Administration complète

---

## 🔧 Modèle de Données Conceptuel

### Table : UserOrganizationScope
```sql
CREATE TABLE user_organization_scopes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth_user(id),
    organization_id UUID REFERENCES accounts_organization(id),
    scope_domain VARCHAR(50),  -- 'catalogue', 'clients', etc.
    scope_level VARCHAR(50),   -- 'read', 'write', 'delete', etc.
    granted_by_id UUID REFERENCES auth_user(id),
    granted_at TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(user_id, organization_id, scope_domain, scope_level)
);
```

### Index pour performance
```sql
CREATE INDEX idx_user_org_scopes_active 
ON user_organization_scopes(user_id, organization_id, is_active)
WHERE is_active = TRUE;
```

---

## 💡 Exemples de Configurations

### Exemple 1 : Denis - Manager polyvalent
```json
{
  "user": "denis@domaine.fr",
  "organization": "Château Margaux",
  "role": "Manager",
  "scopes": [
    "catalogue:read", "catalogue:write",
    "clients:read", "clients:write", 
    "ventes:read", "ventes:write",
    "stocks:read", "stocks:write", "stocks:manage",
    "referentiels:read", "referentiels:write"
  ]
}
```

### Exemple 2 : Marie - Comptable
```json
{
  "user": "marie@expert-comptable.fr", 
  "organization": "Château Margaux",
  "role": "Comptabilité",
  "scopes": [
    "catalogue:read",
    "clients:read", "clients:export",
    "ventes:read", "ventes:financial", "ventes:validate",
    "stocks:read"
  ]
}
```

### Exemple 3 : Pierre - Caviste
```json
{
  "user": "pierre@domaine.fr",
  "organization": "Château Margaux", 
  "role": "Opérateur",
  "scopes": [
    "catalogue:read",
    "stocks:read", "stocks:write", "stocks:inventory"
  ],
  "restrictions": {
    "stocks:entrepots": ["cave-principale", "chai-vieillissement"],
    "ventes:financial": false
  }
}
```

### Exemple 4 : Distributeur externe
```json
{
  "user": "commercial@distributeur.fr",
  "organization": "Château Margaux",
  "role": "Partenaire", 
  "scopes": [
    "catalogue:read"
  ],
  "restrictions": {
    "catalogue:products": "public_only",
    "clients:own_orders_only": true
  }
}
```

---

## ⚖️ Règles de Résolution de Conflits

### 1. Rôle vs Scope
```
Si Rôle = "Manager" (peut créer produits)
ET Scope = "catalogue:read" (lecture seule)
→ RÉSULTAT = lecture seule (le plus restrictif gagne)
```

### 2. Scopes multiples
```
Si Scopes = ["catalogue:read", "catalogue:write"]
→ RÉSULTAT = lecture + écriture (union des droits)
```

### 3. Expiration de scopes
```
Si Scope expiré
→ RÉSULTAT = révocation automatique + notification admin
```

### 4. Scope inexistant
```
Si action demandée non couverte par les scopes
→ RÉSULTAT = refus + log de tentative d'accès
```

---

## 🛡️ Cas d'Usage Avancés

### Multi-organisations
**Contexte** : Consultant travaillant pour plusieurs domaines

```json
{
  "user": "consultant@oenologie.fr",
  "organizations": {
    "château-margaux": {
      "role": "LectureSeule",
      "scopes": ["catalogue:read", "stocks:read"]
    },
    "domaine-romanee": {
      "role": "Manager", 
      "scopes": ["catalogue:read", "catalogue:write", "referentiels:read"]
    }
  }
}
```

### Restrictions temporaires
**Contexte** : Stagiaire avec accès limité dans le temps

```json
{
  "user": "stagiaire@ecole-vin.fr",
  "organization": "Château Margaux",
  "role": "LectureSeule",
  "scopes": [
    {
      "scope": "catalogue:read",
      "expires_at": "2025-12-31T23:59:59Z"
    },
    {
      "scope": "stocks:read", 
      "expires_at": "2025-12-31T23:59:59Z"
    }
  ]
}
```

### Restrictions géographiques
**Contexte** : Responsable d'un seul chai

```json
{
  "user": "chef-chai@domaine.fr",
  "organization": "Château Margaux",
  "role": "Opérateur",
  "scopes": [
    "stocks:read", "stocks:write", "stocks:inventory"
  ],
  "restrictions": {
    "stocks:warehouses": ["chai-rouge", "chai-blanc"],
    "stocks:exclude_warehouses": ["chai-reserve", "chai-prestige"]
  }
}
```

---

## 🔍 Interface d'Administration

### Attribution de Scopes (AdminOrganisation)
```
┌─ Utilisateur: denis@domaine.fr ─────────────────┐
│                                                 │
│ Rôle actuel: Manager                           │
│                                                 │
│ Scopes par domaine:                            │
│ ┌─ Catalogue ─────────────────────────────────┐ │
│ │ ☑ Lecture    ☑ Écriture    ☐ Suppression  │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─ Clients ───────────────────────────────────┐ │
│ │ ☑ Lecture    ☑ Écriture    ☐ Suppression  │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─ Ventes ────────────────────────────────────┐ │
│ │ ☑ Lecture    ☐ Écriture    ☐ Financier    │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [Sauvegarder]  [Annuler]  [Historique]        │
└─────────────────────────────────────────────────┘
```

### Audit des Accès
```
┌─ Journal des accès - denis@domaine.fr ─────────┐
│                                                 │
│ 2025-09-24 14:30  catalogue:read   ✅ Autorisé │
│ 2025-09-24 14:31  clients:write    ✅ Autorisé │
│ 2025-09-24 14:32  ventes:financial ❌ Refusé   │
│ 2025-09-24 14:33  stocks:delete    ❌ Refusé   │
│                                                 │
│ [Exporter]  [Filtrer]  [Alertes]              │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Implémentation Technique

### Décorateur de vue
```python
@require_scope('clients:read')
def clients_list(request):
    # Vue automatiquement protégée
    pass

@require_scopes(['catalogue:read', 'stocks:read'])
def production_dashboard(request):
    # Nécessite plusieurs scopes
    pass
```

### Middleware de vérification
```python
class ScopeMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        required_scopes = getattr(view_func, 'required_scopes', [])
        user_scopes = get_user_scopes(request.user, request.current_org)
        
        if not has_required_scopes(user_scopes, required_scopes):
            return HttpResponseForbidden("Scope insuffisant")
```

### Cache des scopes
```python
@cache_user_scopes(timeout=300)  # 5 minutes
def get_user_scopes(user, organization):
    return UserOrganizationScope.objects.filter(
        user=user, 
        organization=organization,
        is_active=True,
        expires_at__gt=timezone.now()
    ).values_list('scope_domain', 'scope_level')
```

---

**Modèle de scopes défini : 6 domaines × 4 niveaux moyens = 24 scopes de base + restrictions avancées**

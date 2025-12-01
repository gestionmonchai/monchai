# Matrice des Permissions - Module Clients

## Date : 2025-09-25

## 🎯 Rôles MVP Implémentés

### Définition des Rôles
- **SuperAdmin** : Équipe technique Mon Chai (accès technique complet)
- **AdminOrganisation** : Propriétaire du domaine (gestion complète de son organisation)
- **Employé** : Personnel du domaine (lecture + édition clients, pas de paramètres)

---

## 📋 Matrice Permissions Clients

| Page/Action | URL | SuperAdmin | AdminOrg | Employé | Hors Connexion |
|-------------|-----|------------|----------|---------|----------------|
| **Liste clients** | `/clients/` | ✅ | ✅ | ✅ | ❌ → Login |
| **Détail client** | `/clients/<uuid>/` | ✅ | ✅ | ✅ | ❌ → Login |
| **Nouveau client** | `/clients/nouveau/` | ✅ | ✅ | ✅ | ❌ → Login |
| **Modifier client** | `/clients/<uuid>/modifier/` | ✅ | ✅ | ✅ | ❌ → Login |
| **Export clients** | `/clients/export/` | ✅ | ✅ | ❌ | ❌ → Login |
| **API clients** | `/clients/api/` | ✅ | ✅ | ✅ | ❌ → 401 |
| **API suggestions** | `/clients/api/suggestions/` | ✅ | ✅ | ✅ | ❌ → 401 |
| **API doublons** | `/clients/api/duplicates/` | ✅ | ✅ | ✅ | ❌ → 401 |

---

## 🔒 Implémentation Technique

### Décorateurs Utilisés
```python
@login_required                          # Authentification obligatoire
@require_membership(role_min='read_only') # Lecture : tous les employés+
@require_membership(role_min='editor')    # Écriture : employés+ 
@require_membership(role_min='admin')     # Admin : AdminOrg+ uniquement
```

### Correspondance Rôles Django
| Rôle MVP | Rôle Django | Niveau |
|----------|-------------|--------|
| **SuperAdmin** | `superadmin` | 100 |
| **AdminOrganisation** | `admin` | 80 |
| **Employé** | `editor` ou `manager` | 60 |
| **Lecture Seule** | `read_only` | 20 |

---

## 🧪 Tests de Permissions

### Test 1 : Employé (role='editor')
```
✅ Peut accéder à /clients/
✅ Peut voir la liste des clients de son organisation
✅ Peut créer un nouveau client
✅ Peut modifier un client existant
❌ Ne peut pas exporter (bouton masqué)
❌ Ne voit que les clients de son organisation
```

### Test 2 : AdminOrganisation (role='admin')
```
✅ Peut tout faire dans son organisation
✅ Peut exporter les clients
✅ Peut accéder aux paramètres (autres modules)
❌ Ne voit pas les autres organisations
```

### Test 3 : SuperAdmin (role='superadmin')
```
✅ Peut tout faire partout
✅ Peut changer d'organisation
✅ Accès technique /admin/ Django
```

### Test 4 : Hors Connexion
```
❌ /clients/ → Redirection /auth/login/?next=/clients/
❌ /clients/api/ → 401 Unauthorized
```

---

## 🚨 Règles de Sécurité Appliquées

### Isolation Multi-Tenant
- **Automatique** : Filtrage par `request.current_org` dans toutes les vues
- **Validation** : Décorateur `@validate_same_organization` (à implémenter)
- **Tests** : Aucune fuite de données cross-organisation

### Deny by Default
- **Aucune vue** accessible sans `@login_required`
- **Aucune action** sans `@require_membership`
- **Permissions explicites** pour chaque niveau d'accès

### Audit Trail
- **Logs automatiques** : Accès, créations, modifications
- **Traçabilité** : Qui, quoi, quand sur chaque action
- **Monitoring** : Détection activités suspectes

---

## ✅ Conformité Check-list

### Routes
- [x] Pages Client existent sous `/clients/`
- [x] Aucune page fonctionnelle via `/admin/`
- [x] Liens pointent vers `/clients/`

### Navigation & UX  
- [x] Menu "Clients" avec bonnes entrées
- [x] Templates back-office (pas admin Django)
- [x] Libellés cohérents

### Permissions
- [x] SuperAdmin : tout
- [x] AdminOrganisation : tout dans son org
- [x] Employé : lecture+édition Clients
- [x] Hors connexion → login
- [x] Export réservé aux admins

---

**Permissions MVP clients : ✅ CONFORMES**

# Flux de navigation - Landing Page Mon Chai

## 🗺️ Architecture de navigation

```
┌─────────────────────────────────────────────────────────────┐
│                    http://127.0.0.1:8000/                    │
│                         (Racine)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Utilisateur           │
        │  authentifié ?         │
        └────────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       OUI               NON
        │                 │
        ▼                 ▼
┌──────────────┐   ┌─────────────────┐
│  /dashboard/ │   │   /monchai/     │
│              │   │  (Landing Page) │
└──────────────┘   └────────┬────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │  Première visite ? │
                   │ (localStorage)     │
                   └────────┬───────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                  OUI               NON
                   │                 │
                   ▼                 ▼
          ┌─────────────────┐  ┌──────────────┐
          │  Animation      │  │  Landing     │
          │  intro 5 étapes │  │  directe     │
          └────────┬────────┘  └──────┬───────┘
                   │                  │
                   ▼                  │
          "Entrer dans Mon Chai"      │
                   │                  │
                   └──────────┬───────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Landing complète │
                    │  5 sections       │
                    └─────────┬─────────┘
                              │
                              ▼
              "Me connecter à Mon Chai" (header)
                              │
                              ▼
                      ┌──────────────┐
                      │ /auth/login/ │
                      │ (Django)     │
                      └──────┬───────┘
                             │
                     Connexion réussie
                             │
                             ▼
                      ┌──────────────┐
                      │  /dashboard/ │
                      └──────────────┘
```

---

## 📍 URLs et redirections

### Routes principales

| URL | Vue | Template | Accessible |
|-----|-----|----------|------------|
| `/` | `root_redirect()` | - | Tous |
| `/monchai/` | `landing_page()` | `landing/landing_page.html` | Tous |
| `/auth/login/` | `LoginView` | `accounts/login.html` | Non-auth |
| `/dashboard/` | `dashboard_placeholder()` | `accounts/dashboard_viticole.html` | Auth |

### Logique de redirection

**Racine `/`** :
```python
def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')  # → Dashboard
    return redirect('/monchai/')        # → Landing
```

**Landing `/monchai/`** :
- Pas de redirection
- Accessible à tous (pas de `@login_required`)
- Bouton connexion → `/auth/login/`

**Dashboard `/dashboard/`** :
- Décorateur `@login_required`
- Redirection automatique → `/auth/login/` si non-auth

---

## 🎬 Scénarios utilisateur

### 1. Visiteur nouveau

```
1. Visite http://127.0.0.1:8000/
   ↓
2. Redirigé vers /monchai/
   ↓
3. Voit animation intro (5 étapes)
   ↓
4. Clique "Entrer dans Mon Chai"
   ↓
5. Landing complète s'affiche
   ↓
6. Clique "Me connecter à Mon Chai" (header)
   ↓
7. Page /auth/login/ Django
   ↓
8. Remplit formulaire connexion
   ↓
9. Redirigé vers /dashboard/
   ✓ Utilisateur dans l'app
```

### 2. Visiteur récurrent (non-authentifié)

```
1. Visite http://127.0.0.1:8000/
   ↓
2. Redirigé vers /monchai/
   ↓
3. localStorage détecté → Saute l'intro
   ↓
4. Landing complète directement
   ↓
5. Clique "Me connecter à Mon Chai"
   ↓
6. Page /auth/login/ Django
   ↓
7. Connexion
   ↓
8. Dashboard
```

### 3. Utilisateur authentifié

```
1. Visite http://127.0.0.1:8000/
   ↓
2. Détection auth
   ↓
3. Redirigé DIRECTEMENT vers /dashboard/
   ✓ Pas de passage par landing
```

### 4. Visiteur direct URL landing

```
1. Visite http://127.0.0.1:8000/monchai/
   ↓
2. Première visite ? → Intro
   Sinon → Landing directe
   ↓
3. Clique "Me connecter"
   ↓
4. /auth/login/
```

---

## 🔑 Points d'entrée

### Point d'entrée principal : `/`

**Comportement** :
- Détection automatique statut auth
- Redirection intelligente vers landing ou dashboard
- **Recommandé** pour partage liens

### Point d'entrée direct : `/monchai/`

**Comportement** :
- Affichage landing sans redirection
- Utile pour forcer affichage landing
- **Recommandé** pour bookmarks landing

### Point d'entrée app : `/dashboard/`

**Comportement** :
- Nécessite authentification
- Redirection auto vers login si non-auth
- **Recommandé** pour bookmarks app

---

## 🎨 Éléments de navigation

### Header landing page

```
┌─────────────────────────────────────────────────────┐
│  Mon Chai        [Me connecter à Mon Chai]          │
│  (logo)                 (bouton)                     │
└─────────────────────────────────────────────────────┘
```

**Logo** : Texte "Mon Chai" en wine-gold  
**Bouton** : Lien direct vers `/auth/login/`

### Hero section

**2 CTA** :
1. "Demander une démo" (bordeaux plein)
2. "Voir le parcours en 5 étapes" (outline)

*Note : Ces boutons sont visuels pour l'instant*

### CTA final

**2 actions** :
1. "Demander un appel" (bouton principal)
2. "Recevoir une présentation par email" (lien texte)

*Note : À connecter avec backend Django ultérieurement*

---

## 🔐 Contrôle d'accès

### Routes publiques

- `/` (redirection)
- `/monchai/` (landing)
- `/auth/login/`
- `/auth/signup/`
- `/auth/password-reset/`

### Routes protégées

- `/dashboard/` (+ toutes sous-routes)
- `/catalogue/`
- `/clients/`
- `/production/`
- `/admin/`

### Middleware

**CurrentOrganizationMiddleware** :
- Injecte `request.current_org` pour users auth
- Pas d'effet sur routes publiques (landing)

**SecurityMiddleware** :
- Headers sécurité sur toutes routes
- X-Frame-Options, X-XSS-Protection, etc.

---

## 📊 Métriques de navigation

### Temps de chargement attendu

| Page | Temps (p95) | Notes |
|------|-------------|-------|
| `/monchai/` (intro) | < 1.5s | Animation CSS pure |
| `/monchai/` (landing) | < 2s | Bundle React 260 KB gzip |
| `/auth/login/` | < 500ms | Template Django simple |
| `/dashboard/` | < 3s | Requêtes DB + graphiques |

### Taille des assets

```
Landing page totale : ~97 KB gzip
- HTML : 0.44 KB
- CSS  : 3.36 KB
- JS   : 83.81 KB
- Fonts: ~9 KB (Google Fonts)
```

---

## 🔄 LocalStorage

### Clé utilisée

**Nom** : `monchai_has_visited`  
**Valeur** : `'true'` (string)  
**Persistance** : Illimitée (jusqu'à clear cache)

### Comportement

**Première visite** :
- Clé absente → Affiche intro
- Après intro → Clé créée avec valeur 'true'

**Visites suivantes** :
- Clé présente → Saute intro directement landing

### Réinitialiser

Console navigateur (F12) :
```javascript
localStorage.removeItem('monchai_has_visited');
// Puis recharger page
```

Ou vider complètement :
```javascript
localStorage.clear();
```

---

## 🚀 Optimisations futures

### SEO

- [ ] Meta tags OpenGraph pour partage social
- [ ] Sitemap XML incluant `/monchai/`
- [ ] robots.txt autorisant crawling landing
- [ ] Schema.org markup (produit, organisation)

### Performance

- [ ] Lazy loading Framer Motion
- [ ] Preload critical CSS
- [ ] WebP images avec fallback
- [ ] Service Worker pour offline

### UX

- [ ] Scroll to top après navigation
- [ ] Breadcrumbs visuels (Intro → Landing → Login → Dashboard)
- [ ] Animations de transition entre pages
- [ ] Loading states pendant auth

---

## ✅ Validation complète

- ✅ Redirection racine `/` fonctionnelle
- ✅ Landing accessible à `/monchai/`
- ✅ Bouton connexion redirige vers `/auth/login/`
- ✅ Intro affichée première visite
- ✅ Intro sautée visites suivantes
- ✅ Utilisateurs auth redirigés dashboard
- ✅ Navigation header fonctionnelle
- ✅ Tous CTA présents (même si mockés)

**Status** : ✅ **Navigation 100% opérationnelle**

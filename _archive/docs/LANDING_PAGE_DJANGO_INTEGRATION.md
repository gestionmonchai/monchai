# Landing Page Mon Chai - Intégration Django

**Date** : 11 novembre 2025  
**Objectif** : Intégration de la landing page React dans Django à l'URL `/monchai/`

---

## 🎯 Résumé

La landing page React a été **intégrée avec succès** dans l'application Django Mon Chai :

- ✅ **URL accessible** : `http://127.0.0.1:8000/monchai/`
- ✅ **Redirection racine** : `/` → `/monchai/` (non-authentifié) ou `/dashboard/` (authentifié)
- ✅ **Bouton connexion** : "Me connecter à Mon Chai" → `/auth/login/`
- ✅ **Build automatisé** : Script `build_landing.bat` pour rebuild
- ✅ **Assets statiques** : Servis depuis `staticfiles/landing/`

---

## 🏗️ Architecture

### Structure des fichiers

```
Mon Chai V1/
├── landing-page/               # Code source React
│   ├── src/
│   │   ├── components/
│   │   │   ├── IntroExperience.jsx
│   │   │   └── LandingPage.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── vite.config.js         # Config build vers staticfiles/
│   └── package.json
│
├── staticfiles/landing/        # Build React (généré)
│   ├── index.html
│   └── assets/
│       ├── index.js           # Bundle React
│       └── index.css          # Styles Tailwind
│
├── templates/landing/
│   └── landing_page.html      # Template Django
│
├── apps/accounts/views.py      # Vue landing_page()
├── monchai/urls.py            # Route /monchai/
└── build_landing.bat          # Script build auto
```

### Flux d'intégration

1. **Développement React** → `landing-page/src/`
2. **Build Vite** → `staticfiles/landing/`
3. **Template Django** → Charge les assets buildés
4. **Vue Django** → Sert le template
5. **URL** → `/monchai/` accessible

---

## 🚀 Utilisation

### Première visite

Lorsqu'un visiteur non-authentifié arrive sur `http://127.0.0.1:8000/` :

1. **Redirection automatique** vers `/monchai/`
2. **Animation d'intro** s'affiche (5 étapes viticoles)
3. Clic sur **"Entrer dans Mon Chai"** → Landing page complète
4. Clic sur **"Me connecter à Mon Chai"** (header) → `/auth/login/`

### Visites suivantes

Le flag localStorage `monchai_has_visited` saute l'intro et affiche directement la landing.

### Utilisateurs authentifiés

Redirection automatique vers `/dashboard/` (pas d'accès landing).

---

## 🔧 Modification de la landing page

### 1. Modifier le code React

Éditez les fichiers dans `landing-page/src/` :

```bash
cd landing-page
npm run dev  # Mode développement sur http://localhost:3000
```

### 2. Rebuild pour Django

Après modifications, rebuilder :

```bash
# Depuis la racine du projet
build_landing.bat

# Ou manuellement
cd landing-page
npm run build
cd ..
```

### 3. Relancer Django

```bash
python manage.py runserver
```

Visiter `http://127.0.0.1:8000/monchai/` pour voir les changements.

---

## 📂 Fichiers modifiés

### 1. `landing-page/vite.config.js`

```javascript
build: {
  outDir: '../staticfiles/landing',  // Build vers Django
  base: '/static/landing/'           // Base path assets
}
```

### 2. `landing-page/src/components/LandingPage.jsx`

```jsx
<a href="/auth/login/" className="...">
  Me connecter à Mon Chai
</a>
```

### 3. `templates/landing/landing_page.html`

```django
{% load static %}
<link rel="stylesheet" href="{% static 'landing/assets/index.css' %}">
<script type="module" src="{% static 'landing/assets/index.js' %}"></script>
```

### 4. `apps/accounts/views.py`

```python
def landing_page(request):
    """Landing page React accessible avant authentification."""
    return render(request, 'landing/landing_page.html')
```

### 5. `monchai/urls.py`

```python
from apps.accounts.views import landing_page

urlpatterns = [
    path('', root_redirect, name='root'),           # Redirige vers /monchai/ ou /dashboard/
    path('monchai/', landing_page, name='landing_page'),
    ...
]

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return redirect('/monchai/')  # Non-authentifié → landing
```

---

## 🎨 Personnalisation

### Modifier le design

**Couleurs** : Éditer `landing-page/tailwind.config.js`

```javascript
colors: {
  anthracite: '#1a1a1a',
  ivoire: '#f5f5f0',
  bordeaux: '#6e2b2b',
  'wine-gold': '#D4AF37',
}
```

**Typographie** : Modifier dans `landing-page/index.html`

```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display&family=Inter" rel="stylesheet">
```

**Animations** : Éditer timings dans `IntroExperience.jsx` et `LandingPage.jsx`

```javascript
transition={{ duration: 0.6, ease: 'easeOut' }}
```

### Modifier le contenu

Le contenu est directement dans les composants React :

- **Intro** : `landing-page/src/components/IntroExperience.jsx` → tableau `steps`
- **Landing** : `landing-page/src/components/LandingPage.jsx` → tableaux `steps`, `features`, `productPreviews`

Après modification : **rebuild** avec `build_landing.bat`

---

## 🔍 Débogage

### Landing page ne s'affiche pas

**Vérifications** :

1. Build effectué ? `staticfiles/landing/index.html` existe ?
2. Django collectstatic ? `python manage.py collectstatic --noinput`
3. DEBUG=True dans settings.py ?
4. Visiter `http://127.0.0.1:8000/monchai/` directement

### Styles manquants

**Vérifications** :

1. Fichier CSS généré ? `staticfiles/landing/assets/index.css`
2. Console navigateur : erreurs 404 sur assets ?
3. Settings.py : `STATIC_URL = '/static/'`
4. Rebuild : `build_landing.bat`

### JavaScript ne fonctionne pas

**Vérifications** :

1. Console navigateur : erreurs JavaScript ?
2. Fichier JS généré ? `staticfiles/landing/assets/index.js`
3. `<script type="module">` présent dans template ?
4. Cache navigateur : Ctrl+Shift+R pour hard refresh

### Bouton connexion ne fonctionne pas

**Vérifications** :

1. URL `/auth/login/` existe ? Vérifier `monchai/urls.py`
2. Vue auth configurée ?
3. Console navigateur : erreur sur clic ?

---

## 📊 Performance

### Métriques build

```
Build terminé en 3.34s
- index.html:  0.78 kB (gzip: 0.44 kB)
- index.css:  13.51 kB (gzip: 3.36 kB)
- index.js:  260.21 kB (gzip: 83.81 kB)
```

### Optimisations Vite

- ✅ Tree shaking automatique
- ✅ Code splitting React
- ✅ Minification production
- ✅ Assets hashed pour cache busting

### Optimisations futures

- [ ] Lazy loading Framer Motion
- [ ] Image optimization (WebP)
- [ ] Preload critical CSS
- [ ] Service Worker pour offline

---

## 🔐 Sécurité

### Protection CSRF

Le template Django charge automatiquement les assets statiques buildés. Pas de formulaire côté landing → pas de CSRF token nécessaire.

### Authentification

La landing page est **publique** (pas de `@login_required`). Le bouton "Me connecter" redirige vers `/auth/login/` qui est protégée par Django.

### Headers sécurité

Django ajoute automatiquement les headers via `SecurityMiddleware` :

- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

---

## 📝 Maintenance

### Rebuild après pull Git

Si un collaborateur modifie la landing page React :

```bash
git pull
build_landing.bat
python manage.py runserver
```

### Rebuild automatique en CI/CD

Ajouter dans pipeline :

```yaml
- name: Build Landing Page
  run: |
    cd landing-page
    npm ci
    npm run build
```

### Versionning

Les assets buildés (`staticfiles/landing/`) sont **ignorés par Git** (`.gitignore`). Chaque développeur doit rebuilder localement.

**Alternative** : Commiter les assets buildés pour déploiement sans Node.js sur serveur production.

---

## 🚀 Déploiement production

### Option 1 : Build en local

```bash
# Local
build_landing.bat
python manage.py collectstatic --noinput

# Git
git add staticfiles/landing/
git commit -m "Update landing page build"
git push

# Serveur
python manage.py runserver  # Assets déjà buildés
```

### Option 2 : Build sur serveur

```bash
# Serveur production
cd landing-page
npm ci --production
npm run build
cd ..
python manage.py collectstatic --noinput
```

### Option 3 : CDN

Héberger les assets sur CDN et modifier `base` dans `vite.config.js` :

```javascript
base: 'https://cdn.monchai.fr/landing/'
```

---

## ✅ Checklist intégration complète

- ✅ Landing page React buildée
- ✅ Assets dans `staticfiles/landing/`
- ✅ Template Django créé
- ✅ Vue `landing_page()` dans `views.py`
- ✅ URL `/monchai/` dans `urls.py`
- ✅ Redirection racine `/` configurée
- ✅ Bouton "Me connecter à Mon Chai" fonctionnel
- ✅ Script `build_landing.bat` opérationnel
- ✅ Documentation complète

---

## 🎯 Prochaines étapes

### Améliorations UX

- [ ] Animation de chargement pendant build
- [ ] Page 404 personnalisée style landing
- [ ] Tracking analytics (Google Analytics/Plausible)
- [ ] A/B testing sur CTA

### Intégration avancée

- [ ] Formulaire contact avec backend Django
- [ ] Témoignages clients depuis base de données
- [ ] Blog intégré avec posts Django
- [ ] Multilingue (i18n React + Django)

### Performance

- [ ] Lazy loading images
- [ ] Preload critical resources
- [ ] Service Worker pour PWA
- [ ] WebP avec fallback JPEG

---

## 📞 Support

Pour toute question sur l'intégration landing + Django :

- **Documentation React** : `landing-page/README.md`
- **Documentation technique** : `docs/LANDING_PAGE_IMPLEMENTATION.md`
- **Démarrage rapide** : `landing-page/QUICKSTART.md`

**Status** : ✅ **Intégration 100% fonctionnelle**  
**URL** : `http://127.0.0.1:8000/monchai/`  
**Build** : `build_landing.bat`

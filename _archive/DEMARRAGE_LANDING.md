# 🚀 Démarrage rapide - Landing Page Mon Chai

## ✅ C'est déjà fait !

La landing page est **déjà buildée et intégrée** dans Django.

---

## 🎯 Comment y accéder ?

### 1. Lancer le serveur Django

```bash
python manage.py runserver
```

### 2. Ouvrir votre navigateur

Visitez l'une de ces URLs :

- **Racine** : `http://127.0.0.1:8000/`  
  → Redirige automatiquement vers `/monchai/`

- **Direct** : `http://127.0.0.1:8000/monchai/`  
  → Landing page React

### 3. Naviguer

**Première visite** :
1. Animation d'intro avec 5 étapes viticoles s'affiche
2. Cliquez sur **"Entrer dans Mon Chai"**
3. Landing page complète s'affiche
4. En haut à droite : **"Me connecter à Mon Chai"** → Connexion Django

**Visites suivantes** :
- L'intro est sautée automatiquement (localStorage)
- Vous voyez directement la landing page

**Utilisateurs authentifiés** :
- Redirection automatique vers `/dashboard/`

---

## 🔄 Modifier la landing page

Si vous voulez modifier le design ou le contenu :

### 1. Modifier le code React

```bash
cd landing-page
npm run dev  # Serveur développement sur http://localhost:3000
```

Éditez les fichiers dans `landing-page/src/components/`

### 2. Rebuilder pour Django

```bash
# Depuis la racine du projet
build_landing.bat
```

### 3. Relancer Django

```bash
python manage.py runserver
```

Rafraîchir `http://127.0.0.1:8000/monchai/`

---

## 📁 Fichiers importants

- **Landing page React** : `landing-page/src/`
- **Build généré** : `staticfiles/landing/`
- **Template Django** : `templates/landing/landing_page.html`
- **Vue Django** : `apps/accounts/views.py` → `landing_page()`
- **URL** : `monchai/urls.py` → `path('monchai/', ...)`
- **Script build** : `build_landing.bat`

---

## 🎨 Personnalisation rapide

### Changer les couleurs

Éditer `landing-page/tailwind.config.js` :

```javascript
colors: {
  anthracite: '#1a1a1a',  // Fond
  ivoire: '#f5f5f0',      // Texte
  bordeaux: '#6e2b2b',    // Accents
  'wine-gold': '#D4AF37', // Détails
}
```

Puis rebuilder : `build_landing.bat`

### Modifier le contenu

Éditer `landing-page/src/components/LandingPage.jsx` :

- Titre Hero : ligne ~155
- Les 5 étapes : ligne ~27 (tableau `steps`)
- "Pourquoi Mon Chai" : ligne ~111 (tableau `features`)

Puis rebuilder : `build_landing.bat`

---

## 🐛 Problème ?

### Landing page ne s'affiche pas

1. Vérifier que le build existe : `staticfiles/landing/index.html`
2. Si non : lancer `build_landing.bat`
3. Relancer Django : `python manage.py runserver`

### Modifications non visibles

1. Rebuilder : `build_landing.bat`
2. Hard refresh navigateur : **Ctrl + Shift + R**
3. Vider cache : **Ctrl + Shift + Delete**

### Erreur 404 sur assets

1. Vérifier `DEBUG = True` dans `settings.py`
2. Rebuilder : `build_landing.bat`
3. Collectstatic : `python manage.py collectstatic --noinput`

---

## 📚 Documentation complète

- **Intégration Django** : `docs/LANDING_PAGE_DJANGO_INTEGRATION.md`
- **Spécifications techniques** : `docs/LANDING_PAGE_IMPLEMENTATION.md`
- **README React** : `landing-page/README.md`
- **Quickstart React** : `landing-page/QUICKSTART.md`

---

## ✨ C'est tout !

Lancez `python manage.py runserver` et visitez `http://127.0.0.1:8000/` 🍷

**URL landing** : `/monchai/`  
**URL connexion** : `/auth/login/`  
**URL dashboard** : `/dashboard/` (authentifié)

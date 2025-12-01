# 🚀 Démarrage rapide - Landing Page Mon Chai

## Installation et lancement (3 commandes)

```bash
# 1. Naviguer dans le dossier
cd landing-page

# 2. Installer les dépendances (première fois uniquement)
npm install

# 3. Lancer le serveur de développement
npm run dev
```

**Résultat** : L'application s'ouvre automatiquement sur `http://localhost:3000`

---

## 🎬 Première visite

1. **Animation d'intro** s'affiche avec 5 étapes qui apparaissent successivement
2. Cliquez sur **"Entrer dans Mon Chai"** après ~5 secondes
3. Vous accédez à la **landing page complète**

## 🔄 Visites suivantes

L'intro est **automatiquement ignorée** - vous accédez directement à la landing.

### Pour revoir l'animation d'intro

Ouvrez la console du navigateur (F12) et tapez :
```javascript
localStorage.removeItem('monchai_has_visited');
```
Puis rechargez la page (F5).

---

## 📦 Build pour production

```bash
npm run build
```

Le dossier `dist/` contient les fichiers optimisés prêts pour déploiement.

---

## 🎨 Ce qui a été implémenté

✅ **Animation d'intro immersive** (5 étapes viticoles)  
✅ **Landing page haut de gamme** (5 sections complètes)  
✅ **Design sobre et luxueux** (palette bordeaux/anthracite/wine-gold)  
✅ **Responsive** desktop/mobile  
✅ **Animations fluides** (Framer Motion)  
✅ **Mémorisation** localStorage (pas d'intro répétée)  
✅ **Contenu réel** (pas de lorem ipsum)  

---

## 📖 Documentation complète

Voir `README.md` pour la documentation détaillée.

---

## 🐛 Besoin d'aide ?

Les **warnings CSS `@tailwind`** dans l'IDE sont **normaux** - ils disparaissent au build.

Tout est prêt, il suffit de lancer `npm run dev` ! 🍷

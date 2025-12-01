# Mon Chai - Landing Page

Landing page haut de gamme pour le SaaS viticole **Mon Chai**.  
Design sobre et luxueux inspiré des maisons de vin, avec animation d'intro immersive.

---

## 🎨 Design

### Palette de couleurs
- **Anthracite** : `#1a1a1a` (fond principal)
- **Ivoire** : `#f5f5f0` (texte)
- **Bordeaux** : `#6e2b2b` (accents, CTA)
- **Wine Gold** : `#D4AF37` (détails luxueux)

### Typographie
- **Titres** : Playfair Display (serif élégant)
- **Texte courant** : Inter (sans-serif moderne)

### Concept
Interface gravée, sobre et luxueuse évoquant l'univers du chai :
- Animations subtiles (fade, slide, parallax léger)
- Transitions fluides
- Design responsive desktop/mobile
- Ambiance : bois, métal, silence, précision

---

## 🎬 Fonctionnalités

### Animation d'intro (première visite)
Parcours immersif en **5 étapes** :
1. **Gestion de la vigne** - Parcelles et traitements
2. **Vendanges** - Entrées de récolte
3. **Encuvage** - Suivi des cuves
4. **Mise en bouteilles** - Lots et étiquettes
5. **Ventes** - Du stock au client

- Ligne horizontale traverse l'écran
- Étapes apparaissent avec fade + slide
- Bouton "Entrer dans Mon Chai" pour accéder à la landing
- **Mémorisation** : les visites suivantes sautent directement à la landing (localStorage)

### Landing principale
5 sections complètes :

1. **Hero Section**
   - Titre accrocheur
   - Proposition de valeur claire
   - 2 CTA : "Demander une démo" + "Voir le parcours"
   - Image/illustration stylisée

2. **Le parcours en 5 étapes**
   - Timeline verticale élégante
   - Chaque étape avec icône, titre, description
   - Points clés révélés en accordéon (hover/clic)

3. **Pourquoi Mon Chai ?**
   - 3 cartes : Clair et sobre, Aligné sur le réel, Pensé pour grandir
   - Effets hover subtils

4. **Aperçu produit**
   - Grille 2x2 de vignettes (placeholders)
   - Vue parcellaire, Vendange, Cuve, Stock

5. **CTA final**
   - Grand encart centré avec dégradé
   - 2 actions : "Demander un appel" + "Présentation email"

---

## 🛠️ Technologies

- **React 18** - Composants fonctionnels
- **Vite** - Build tool rapide
- **Tailwind CSS** - Utility-first CSS
- **Framer Motion** - Animations fluides
- **localStorage** - Mémorisation visite

---

## 📦 Installation

### Prérequis
- Node.js 18+ et npm/yarn

### Étapes

```bash
# 1. Naviguer dans le dossier
cd landing-page

# 2. Installer les dépendances
npm install
# ou
yarn install

# 3. Lancer le serveur de développement
npm run dev
# ou
yarn dev

# 4. Ouvrir le navigateur
# L'application s'ouvre automatiquement sur http://localhost:3000
```

---

## 🏗️ Structure du projet

```
landing-page/
├── src/
│   ├── components/
│   │   ├── IntroExperience.jsx   # Animation d'intro 5 étapes
│   │   └── LandingPage.jsx        # Landing principale
│   ├── App.jsx                     # Routing intro/landing + localStorage
│   ├── main.jsx                    # Point d'entrée React
│   └── index.css                   # Styles Tailwind
├── index.html                      # Template HTML
├── package.json                    # Dépendances
├── vite.config.js                  # Configuration Vite
├── tailwind.config.js              # Configuration Tailwind
├── postcss.config.js               # Configuration PostCSS
└── README.md                       # Ce fichier
```

---

## 🎯 Utilisation

### Première visite
1. L'utilisateur arrive sur le site
2. Animation d'intro avec les 5 étapes s'affiche
3. Clic sur "Entrer dans Mon Chai"
4. Accès à la landing complète
5. Un flag est enregistré dans `localStorage`

### Visites suivantes
1. L'utilisateur arrive sur le site
2. Détection du flag `monchai_has_visited` dans localStorage
3. Affichage direct de la landing (saut de l'intro)

### Réinitialiser l'intro
Pour revoir l'animation d'intro :
```javascript
// Dans la console du navigateur
localStorage.removeItem('monchai_has_visited');
// Puis recharger la page
```

---

## 🎨 Personnalisation

### Modifier les couleurs
Éditer `tailwind.config.js` :
```javascript
theme: {
  extend: {
    colors: {
      anthracite: '#1a1a1a',
      ivoire: '#f5f5f0',
      bordeaux: '#6e2b2b',
      'wine-gold': '#D4AF37',
    },
  },
}
```

### Modifier les animations
Éditer les `transition` dans `IntroExperience.jsx` et `LandingPage.jsx` :
```javascript
transition={{ duration: 0.6, ease: 'easeOut' }}
```

### Ajouter des images
Remplacer les placeholders SVG dans `LandingPage.jsx` :
```jsx
<img src="/path/to/image.jpg" alt="Description" className="..." />
```

---

## 🚀 Build pour production

```bash
# Créer le build optimisé
npm run build
# ou
yarn build

# Le dossier dist/ contient les fichiers prêts pour déploiement

# Prévisualiser le build
npm run preview
# ou
yarn preview
```

---

## 📝 Notes techniques

### Composants principaux

**`App.jsx`**
- Gère le routing entre intro et landing
- Vérifie `localStorage` pour `monchai_has_visited`
- Affiche un loader minimal pendant la vérification

**`IntroExperience.jsx`**
- Animation séquencée des 5 étapes
- Ligne horizontale traversante
- Bouton d'entrée avec callback `onComplete`
- Icônes SVG minimalistes

**`LandingPage.jsx`**
- 5 sections complètes
- Animations Framer Motion (fadeInUp, stagger)
- Accordéon pour les points clés des étapes
- Navigation et footer minimalistes

### Performances
- Lazy loading des animations avec `whileInView`
- Animations optimisées avec `transform` et `opacity`
- Build Vite ultra-rapide
- Code splitting automatique

---

## 🎯 Améliorations futures possibles

- [ ] Intégration formulaire de contact avec backend
- [ ] Vidéos de démonstration dans aperçu produit
- [ ] Témoignages clients vignerons
- [ ] Version multilingue (FR/EN)
- [ ] Mode sombre/clair (actuellement sombre uniquement)
- [ ] Intégration analytics (Google Analytics, Plausible)
- [ ] A/B testing sur les CTA

---

## 📄 Licence

Propriété de **Mon Chai**. Tous droits réservés.

---

## 🤝 Contact

Pour toute question ou demande de personnalisation, contactez l'équipe Mon Chai.

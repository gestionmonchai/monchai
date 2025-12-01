# ✅ Landing Page Automnale avec Header Progressif

## 🍂 Palette Automnale BORDEAUX (Sans Blanc)

La landing page utilise maintenant une **palette 100% automnale** avec des tons chauds bordeaux/brun/ocre :

| Couleur | Code | Usage |
|---------|------|-------|
| **Brun foncé** | #2C1810 | Fond principal (très sombre) |
| **Brun moyen** | #3D2416 | Fond secondaire |
| **Brun clair** | #4D2E1C | Fond cartes |
| **Bordeaux** | #8B2F2F | Couleur accent, titres |
| **Bordeaux vif** | #A63F3F | Hover, surbrillance active |
| **Or antique** | #C9A961 | CTA pricing |
| **Vert olive foncé** | #4A5C2A | Badges verts |
| **Terre** | #6B4423 | Bordures |
| **Terracotta** | #B8653F | Accents terre cuite |
| **Brun cuir** | #5C3D2E | Gradients |
| **Ocre doré** | #D4A574 | Textes clairs |

**Ambiance** : Cave automnale, bois vieilli, tonneaux de chêne, terre et feuilles d'automne 🍂🍷

**IMPORTANT** : Plus aucun fond blanc ! Tout est dans les tons bruns/bordeaux.

---

## 🎯 Header Progressif au Scroll

### Comportement

**En haut de page (scroll < 50px)** :
- Fond **semi-transparent** : `rgba(44, 24, 16, 0.3)` → devient progressivement plus opaque
- Bordure subtile terre : `rgba(107, 68, 35, 0.3)`
- Pas d'ombre

**Après scroll (scroll > 50px)** :
- Fond **opaque bordeaux foncé** : `rgba(44, 24, 16, 0.95)`
- Ombre **rouge bordeaux** : `0 4px 6px rgba(139, 47, 47, 0.3)`
- Bordure **bordeaux** : `rgba(139, 47, 47, 0.5)`

### Transition

- **Fluide** : `transition-all duration-500` sur le header
- **Progressive** : Opacité augmente linéairement de 0.3 à 0.95 entre 0-50px de scroll
- **Performance** : Event listener avec `passive: true`

### Code JavaScript

```javascript
const header = document.getElementById('main-header');

function updateHeader() {
  const scrollY = window.scrollY;
  
  if (scrollY > 50) {
    // Header scrollé : opaque avec ombre bordeaux
    header.style.backgroundColor = 'rgba(44, 24, 16, 0.95)';
    header.style.boxShadow = '0 4px 6px -1px rgba(139, 47, 47, 0.3)';
    header.style.borderBottomColor = 'rgba(139, 47, 47, 0.5)';
  } else {
    // Header transparent progressif
    const opacity = scrollY / 50;
    header.style.backgroundColor = `rgba(44, 24, 16, ${0.3 + opacity * 0.65})`;
    header.style.boxShadow = 'none';
    header.style.borderBottomColor = 'rgba(107, 68, 35, 0.3)';
  }
}

window.addEventListener('scroll', updateHeader, { passive: true });
```

---

## 🎨 Changements Visuels Majeurs

### 1. Fond général
✅ Dégradé **brun foncé** : `from-chai-bg via-chai-bgSoft to-chai-bgMedium`  
❌ Plus de blanc ou crème

### 2. Sections
- **Parcours** : Dégradé `from-chai-bgSoft to-chai-bgMedium`
- **Pourquoi** : Dégradé `from-chai-bgMedium to-chai-bg`
- **Pricing** : Dégradé `from-chai-accent/20 to-chai-bgSoft` (légère teinte bordeaux)
- **Aperçu** : Dégradé `from-chai-bg to-chai-bgSoft`
- **CTA Final** : Dégradé bordeaux `from-chai-accent to-chai-accentSoft`

### 3. Cartes
✅ **Avant** : Fond blanc  
✅ **Après** : Gradients brun `from-chai-bgMedium via-chai-brun to-chai-bgSoft`

### 4. Textes
✅ **Titres** : Bordeaux (#8B2F2F)  
✅ **Textes clairs** : Ocre (#D4A574 avec opacité 80-90%)  
✅ **Textes secondaires** : Ocre avec opacité 60-70%

### 5. Visuel Hero
✅ Fond carte : Gradient `from-chai-bgMedium to-chai-bgSoft`  
✅ Bordure : Gradient `from-chai-brun to-chai-terre`  
✅ Tous les textes en ocre/or

---

## 🖱️ Accordéon - Surbrillance Active

**Style actif mis à jour** pour la palette automnale :

```css
.etape-active .etape-numero {
  background-color: #8B2F2F !important; /* Bordeaux */
  border-color: #8B2F2F !important;
}

.etape-active .etape-carte {
  border-color: #8B2F2F !important;
  background: linear-gradient(to bottom right, 
    rgba(139, 47, 47, 0.2), 
    #4D2E1C, 
    #5C3D2E) !important;
  box-shadow: 0 4px 6px rgba(139, 47, 47, 0.4) !important;
}
```

**Plus de fond blanc** dans l'état actif !

---

## 📊 Structure Visuelle Complète

```
HEADER (progressif)
  Transparent → Opaque bordeaux au scroll
  Ombre bordeaux après 50px

HERO (brun foncé)
  Badge vert olive
  Titre bordeaux
  Textes ocre
  Visuel brun/terre

PARCOURS (gradient brun)
  5 étapes sur fond brun gradient
  Bordures terre
  Textes ocre
  Surbrillance bordeaux au clic

POURQUOI (gradient brun inverse)
  3 cartes brun gradient
  Titres bordeaux
  Textes ocre

PRICING (léger accent bordeaux)
  Carte brun gradient
  Prix bordeaux
  CTA or
  Textes ocre

APERÇU (gradient brun)
  4 screenshots fond brun
  Titres bordeaux
  Textes ocre

CTA FINAL (gradient bordeaux vif)
  Fond rouge bordeaux dégradé
  Carte semi-transparente
  Textes blancs

FOOTER (brun foncé)
  Textes ocre clair
  Liens hover bordeaux
```

---

## 🚀 Tester

```bash
python manage.py runserver
```

Visitez : **`http://127.0.0.1:8000/monchai/`**

### À tester :

1. **Scroll** : Regardez le header devenir progressivement opaque avec ombre bordeaux
2. **Tons automnaux** : Vérifiez qu'il n'y a plus de blanc, tout est brun/bordeaux/ocre
3. **Étapes cliquables** : Cliquez sur 1-5 pour voir la surbrillance bordeaux foncé
4. **Ambiance** : Cave d'automne, tonneaux, terre, chaleur

---

## ✅ Checklist

### Header progressif
- ✅ Transparent en haut (0.3 opacité)
- ✅ Transition fluide au scroll
- ✅ Opaque bordeaux après 50px
- ✅ Ombre bordeaux dynamique
- ✅ Bordure change de couleur

### Palette automnale
- ✅ Brun foncé fond principal
- ✅ Bordeaux titres et accents
- ✅ Ocre pour textes
- ✅ Terre pour bordures
- ✅ Or pour CTA pricing
- ✅ **Plus aucun blanc**

### Sections
- ✅ Toutes les sections en gradient brun
- ✅ Cartes en gradient brun
- ✅ Textes en ocre
- ✅ Bordures en terre/bordeaux

### Accordéon
- ✅ Style neutre brun au départ
- ✅ Surbrillance bordeaux au clic
- ✅ Gradient brun dans l'état actif

---

## 🎨 Inspiration Visuelle

**Thème** : Cave à vin automnale
- Tonneaux de chêne vieillis
- Terre de vignoble en automne
- Feuilles de vigne rousses
- Bordeaux profond du vin
- Lumière tamisée d'une cave

**Couleurs clés** :
- 🤎 Brun = Bois, terre, cave
- 🍷 Bordeaux = Vin, raisin, passion
- 🍂 Ocre = Feuilles d'automne, lumière chaude
- 🌿 Vert olive = Vigne, nature

---

**La landing page respire maintenant l'automne viticole avec un header qui s'anime au scroll !** 🍂🍷✨

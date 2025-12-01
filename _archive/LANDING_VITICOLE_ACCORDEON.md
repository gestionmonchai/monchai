# ✅ Landing Page Viticole avec Accordéon - Version Chaude !

## 🎨 Palette Viticole CHAUDE

La landing page a une **direction artistique viticole chaleureuse** avec des couleurs riches et naturelles :

| Couleur | Code | Usage |
|---------|------|-------|
| **Crème chaud** | #FFF5E6 | Fond principal (plus chaud que beige) |
| **Abricot** | #FFE8CC | Fond secondaire, cartes |
| **Rouge brique** | #A0302F | Couleur principale, titres |
| **Rouge vif** | #C64440 | Hover, accents |
| **Or riche** | #D4A017 | CTA pricing, checkmarks |
| **Vert olive** | #6B7F39 | Badges, détails |
| **Terracotta** | #B8653F | Bordures, séparations |
| **Ocre** | #D8885C | Accents terracotta |

**Ambiance** : Chaleureuse, riche, rappelle le soleil sur les vignes et la terre ocre

---

## 🖱️ Étapes Parcours Cliquables (Accordéon + Sélection Active)

### Comment ça fonctionne

**Au chargement** :
- Les 5 étapes sont affichées avec leurs titres
- **Toutes les étapes** ont le même style neutre (fond crème/abricot)
- Les détails sont **masqués**
- Un indicateur **▼** apparaît sur chaque carte (tourné à 90° = fermé)

**Au 1er clic sur une étape** :
1. L'étape devient **ACTIVE** avec surbrillance rouge :
   - ✅ Numéro : **fond rouge brique** (#A0302F) + **texte blanc**
   - ✅ Carte : **bordure rouge** + fond légèrement teinté rouge
   - ✅ Ombre colorée rouge
2. Les détails **s'ouvrent** en douceur (animation 0.3s)
3. L'indicateur **tourne** vers le bas (▼)

**Au 2ème clic (même étape)** :
1. L'étape se **DÉSACTIVE** : retour au style neutre
2. Les détails se **referment** en douceur
3. L'indicateur revient en position latérale (►)

**Plusieurs étapes** :
- Vous pouvez activer plusieurs étapes en même temps
- Chaque étape garde son état indépendamment

### Éléments cliquables

Les 5 étapes du parcours :
1. **Vigne** • Traitements & suivi parcellaire
2. **Vendanges** • Entrées de récolte  
3. **Encuvage** • Suivi des cuves & opérations (mise en avant)
4. **Mises** • Lots & étiquettes
5. **Ventes** • Du stock au client

---

## 🎯 Changements Majeurs

### 1. Palette de couleurs
✅ **Fini le noir !** Fond crème/beige chaleureux  
✅ **Bordeaux viticole** (#8B2F39) pour les titres  
✅ **Vert vigne** (#5C6F3E) pour les badges  
✅ **Or** (#C9A961) pour le CTA pricing  
✅ **Terre** (#8B7355) pour les bordures

### 2. Accordéon interactif
✅ **JavaScript** pour rendre les étapes cliquables  
✅ **Animation smooth** (0.3s ease-out)  
✅ **Indicateur visuel** (▼) qui tourne  
✅ **Effet hover** (ombre au survol)  
✅ **Cursor pointer** pour indiquer le clic

### 3. Design général
✅ **Header** sur fond crème avec logo bordeaux  
✅ **Hero** avec badge vert vigne + titre bordeaux  
✅ **Sections** alternant blanc et beige doux  
✅ **Pricing** sur fond légèrement accenté  
✅ **CTA final** sur fond dégradé bordeaux  
✅ **Footer** sur fond beige

---

## 📊 Structure Visuelle

```
HEADER (crème)
  Logo bordeaux + Menu + Bouton bordeaux

HERO (dégradé beige)
  Badge vert vigne
  Titre bordeaux
  2 CTA (bordeaux + outline)
  Visuel sur fond blanc/beige

PARCOURS (blanc) ← ACCORDÉON ICI
  5 étapes cliquables
  Détails masqués par défaut
  Indicateur ▼ tournant

POURQUOI (beige doux)
  3 cartes blanches

PRICING (beige avec accent bordeaux léger)
  Carte pricing bordeaux
  CTA or

APERÇU (blanc)
  4 screenshots sur fond beige

CTA FINAL (dégradé bordeaux)
  Fond bordeaux avec carte semi-transparente

FOOTER (beige)
  Liens gris
```

---

## 🖱️ JavaScript Accordéon - Détails Techniques

```javascript
// Au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
  // Sélectionne les 5 étapes
  const etapes = document.querySelectorAll('#parcours .space-y-10 > div');
  
  etapes.forEach((etape) => {
    const carte = etape.querySelector('.flex-1');
    const details = carte.querySelector('dl');
    
    // 1. Masque les détails au départ
    details.style.maxHeight = '0';
    details.style.overflow = 'hidden';
    
    // 2. Ajoute l'indicateur ▼
    const indicator = document.createElement('span');
    indicator.innerHTML = '▼';
    indicator.style.transform = 'rotate(-90deg)'; // Tourné à 90°
    
    // 3. Rend cliquable
    carte.addEventListener('click', function() {
      if (isOpen) {
        // Fermer
        details.style.maxHeight = '0';
        indicator.style.transform = 'rotate(-90deg)';
      } else {
        // Ouvrir
        details.style.maxHeight = details.scrollHeight + 'px';
        indicator.style.transform = 'rotate(0deg)';
      }
    });
  });
});
```

**Animations** :
- Transition : `max-height 0.3s ease-out`
- Rotation : `transform rotate()`
- Hover : `shadow-lg`

---

## 🚀 Tester Maintenant

```bash
python manage.py runserver
```

Visitez : **`http://127.0.0.1:8000/monchai/`**

### Ce que vous verrez :

1. **Design chaleureux** avec couleurs viticoles (crème/beige/bordeaux)
2. **Étapes du parcours** avec indicateur ▼
3. **Cliquez sur une étape** → détails s'affichent
4. **Cliquez à nouveau** → détails se masquent
5. **Pricing** mis en avant avec couleur or
6. **Navigation fluide** entre les sections

---

## ✅ Checklist Complète

### Couleurs viticoles
- ✅ Fond crème/beige (fini le noir)
- ✅ Bordeaux pour titres et accents
- ✅ Vert vigne pour badges
- ✅ Or pour pricing CTA
- ✅ Terre pour bordures

### Accordéon parcours
- ✅ JavaScript fonctionnel
- ✅ Détails masqués au chargement
- ✅ Indicateur ▼ qui tourne
- ✅ Animation smooth 0.3s
- ✅ Cursor pointer
- ✅ Effet hover

### Fonctionnalités
- ✅ 5 étapes cliquables
- ✅ Ouverture/fermeture au clic
- ✅ Pricing à 29,99€ visible
- ✅ Bouton "Me connecter" → /auth/login/
- ✅ Slogan "De la vigne à la vente"
- ✅ Responsive mobile/desktop

---

## 🎨 Comparaison Avant/Après

### AVANT (noir)
- ❌ Fond noir total
- ❌ Ambiance sombre
- ❌ Pas viticole
- ❌ Étapes statiques

### APRÈS (viticole)
- ✅ Fond crème/beige chaleureux
- ✅ Palette viticole (bordeaux/vert/or)
- ✅ Ambiance cave/vignoble
- ✅ **Étapes cliquables avec accordéon**
- ✅ Direction artistique forte

---

## 📝 Fichier Modifié

**Un seul fichier** : `templates/landing/landing_page_simple.html`

**Modifications** :
1. Palette couleurs viticole (lignes 21-29)
2. Toutes les sections : fond/texte/bordures
3. JavaScript accordéon (lignes 559-606)

**Taille** : ~40 lignes de JavaScript ajoutées

---

## 💡 Utilisation de l'Accordéon

**Pour l'utilisateur** :
1. Il voit les 5 titres d'étapes
2. Il clique sur celle qui l'intéresse
3. Les 3 fonctionnalités s'affichent
4. Il peut fermer en recliquant
5. Il peut ouvrir plusieurs étapes en même temps

**Avantages** :
- Moins de scroll
- Focus sur ce qui intéresse
- Interaction engageante
- Design épuré

---

**La landing page est prête avec des couleurs vraiment viticoles et des étapes cliquables !** 🍇🍷

**Testez le système d'accordéon en cliquant sur les étapes du parcours !**

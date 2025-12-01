# ✅ Landing Page - Version Finale Viticole

## 🎯 Base : landing_test.html

La landing page est basée sur **l'agencement exact de landing_test.html** avec des modifications minimales.

---

## 🎨 Modifications apportées

### 1. Couleurs viticoles (subtiles)
Les couleurs sont légèrement plus chaudes et viticoles, mais gardent l'ambiance sombre :

| Couleur | Code | Usage |
|---------|------|-------|
| **Fond** | #1a1612 | Fond principal (brun très foncé au lieu de noir pur) |
| **Fond doux** | #252018 | Fond secondaire |
| **Accent** | #8B4049 | Couleur principale (bordeaux rosé) |
| **Accent clair** | #A34D56 | Hover, accents |
| **Or** | #C9A961 | CTA premium |

**Changement** : Palette légèrement plus chaude avec des tons brun-bordeaux au lieu du noir complet.

### 2. Slogan "De la vigne à la vente"
✅ Titre page  
✅ Badge hero  
✅ Titre H1  
✅ Footer

### 3. Header modifié
**Navigation** :
- Parcours
- **Tarif** (nouveau lien vers #pricing)
- Pourquoi
- **Me connecter** (bouton qui va vers /auth/login/)

### 4. Section Pricing ajoutée

**Position** : Entre "Pourquoi Mon Chai" et "Aperçu produit"

**Contenu** :
- Prix : **29,99€/mois**
- Inclus :
  - ✓ Toutes les fonctionnalités incluses
  - ✓ Vigne, vendanges, chai, ventes
  - ✓ Traçabilité complète et DRM
  - ✓ Mises à jour régulières
  - ✓ Données hébergées en France
- CTA : "Commencer maintenant" (bouton or)
- Mentions : 30 jours d'essai gratuit • Sans engagement

**Pas de mention de support téléphone/mail** comme demandé.

---

## 📋 Structure complète

1. **Header** (sticky)
   - Logo Mon Chai
   - Menu : Parcours, Tarif, Pourquoi
   - Bouton "Me connecter"

2. **Hero**
   - Badge "De la vigne à la vente"
   - Titre : "De la vigne à la vente, tout votre domaine"
   - 2 CTA
   - Visuel 5 étapes

3. **Parcours** (5 étapes)
   - Vigne, Vendanges, Encuvage, Mises, Ventes
   - Carte Encuvage mise en avant

4. **Pourquoi Mon Chai** (3 cartes)
   - Clair et sobre
   - Aligné sur le réel
   - Pensé pour grandir

5. **💰 Pricing** (NOUVEAU)
   - Carte centrée
   - 29,99€/mois
   - Liste inclus
   - Essai gratuit

6. **Aperçu produit** (4 screenshots)
   - Parcellaire, Vendanges, Cuves, Stock

7. **CTA Final**
   - Demander un appel
   - Présentation email

8. **Footer**
   - Copyright + liens

---

## 🎯 Points clés

✅ **Agencement identique** à landing_test.html  
✅ **Couleurs** légèrement plus viticoles (brun-bordeaux)  
✅ **Slogan** "De la vigne à la vente" partout  
✅ **Pricing** simple et clair à 29,99€  
✅ **Pas de support** téléphone/mail mentionné  
✅ **Bouton connexion** → /auth/login/  

---

## 🚀 Tester

```bash
python manage.py runserver
```

Visitez : **`http://127.0.0.1:8000/monchai/`**

---

## 🎨 Différences visuelles avec landing_test.html

| Élément | Avant (test) | Maintenant |
|---------|--------------|------------|
| **Fond** | Noir pur #111111 | Brun foncé #1a1612 |
| **Accent** | #6e2b2b (bordeaux foncé) | #8B4049 (bordeaux rosé) |
| **Or** | ❌ Absent | ✅ #C9A961 (CTA pricing) |
| **Slogan** | "Du cep à la bouteille" | "De la vigne à la vente" |
| **Header** | Demander une démo | Me connecter |
| **Menu** | Contact | Tarif |
| **Pricing** | ❌ Absent | ✅ Section dédiée 29,99€ |

---

## 📝 Fichier modifié

**Un seul fichier** : `templates/landing/landing_page_simple.html`

**Base** : Copie exacte de `landing_test.html`

**Modifications** :
1. Palette couleurs (lignes 21-27)
2. Slogan (lignes 5, 75, 78, 492)
3. Header menu (lignes 55-62)
4. Section pricing (lignes 399-453)

---

**La landing page respecte votre demande : agencement de landing_test.html + couleurs viticoles + pricing 29,99€ !** 🍇🍷

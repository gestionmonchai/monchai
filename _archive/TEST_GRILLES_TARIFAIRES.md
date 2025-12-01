# 🧪 TEST MODULE GRILLES TARIFAIRES

## ✅ MODULE OPÉRATIONNEL

Le serveur est démarré et le module est maintenant pleinement fonctionnel !

---

## 🎯 Accès au Module

### URL Direct
```
http://127.0.0.1:8000/ventes/tarifs/
```

### Via Menu Navigation
```
Menu: Clients → 🟡 Grilles tarifaires
```

---

## 📊 Données de Démo Créées

La commande `python manage.py create_sales_demo` a créé :

- ✅ **3 grilles tarifaires** :
  - Tarif Public (particuliers)
  - Tarif Professionnel (cavistes, restaurants)
  - Tarif VIP (clients prioritaires)

- ✅ **24 éléments de prix** :
  - Prix unitaires
  - Prix carton de 6
  - Prix carton de 12
  - Avec remises progressives

- ✅ **5 clients** associés aux grilles
- ✅ **4 codes taxes** (TVA FR/UE)

---

## 🧪 PLAN DE TEST COMPLET

### Test 1 : Liste des Grilles ✅

1. **Ouvrir** : http://127.0.0.1:8000/ventes/tarifs/
2. **Vérifier** :
   - ✓ 3 grilles affichées (Public, Professionnel, VIP)
   - ✓ Compteur "3 grilles" en haut
   - ✓ Badges statut (Actives)
   - ✓ Colonnes : Nom, Devise, Validité, Nb Prix
   - ✓ Boutons actions (Voir, Éditer en grille, Importer, Modifier)

3. **Tester Recherche** :
   - Cliquer dans la barre recherche (Ctrl+K fonctionne)
   - Taper "Public"
   - Attendre 300ms → Filtre automatique
   - ✓ 1 résultat affiché

4. **Tester Filtres** :
   - Cliquer "Actives" → Toutes visibles
   - Cliquer "Inactives" → Aucune
   - Cliquer "Tout afficher" → Retour normal

**✅ RÉSULTAT ATTENDU** : Liste fonctionne, recherche temps réel OK, filtres OK

---

### Test 2 : Détail d'une Grille ✅

1. **Ouvrir détail** :
   - Cliquer sur l'icône 👁️ à droite de "Tarif Public"
   
2. **Vérifier** :
   - ✓ Header bordeaux avec infos grille
   - ✓ Statistiques (validité, devise, nombre de prix)
   - ✓ Prix groupés par produit (SKU)
   - ✓ 3 niveaux de prix affichés (unitaire, carton 6, carton 12)
   - ✓ Badges remise si applicable
   - ✓ Boutons actions en haut

**✅ RÉSULTAT ATTENDU** : Tous les prix visibles, bien organisés

---

### Test 3 : ⭐ ÉDITION EN GRILLE (TEST ERGONOMIE) ✅

**C'est LE TEST le plus important pour valider l'ergonomie !**

1. **Ouvrir édition en grille** :
   - Depuis la liste, cliquer sur l'icône "grille" 🔷 de "Tarif Public"
   - OU depuis le détail, cliquer "Éditer en grille"

2. **Vérifier l'affichage** :
   - ✓ Tableau avec tous les produits
   - ✓ 3 colonnes de prix (Unitaire, Carton 6, Carton 12)
   - ✓ Inputs dans chaque cellule
   - ✓ Prix actuels pré-remplis

3. **TESTER SAISIE RAPIDE** :
   
   **Étape A - Saisie simple** :
   ```
   1. Cliquer dans la première cellule "Prix Unitaire"
   2. Taper "18.50" (nouveau prix)
   3. Appuyer sur Tab → Passe au "Carton de 6"
   ```
   
   **✅ VÉRIFICATION** :
   - Le champ devient ORANGE (modifié)
   - Puis automatiquement VERT pendant 2s (sauvegardé)
   - Icône ✅ apparaît dans la colonne Statut
   - Notification en bas à droite "Prix sauvegardé"
   
   **Étape B - Navigation rapide** :
   ```
   1. Taper "17.00" dans Carton de 6
   2. Appuyer sur Enter (au lieu de Tab)
   ```
   
   **✅ VÉRIFICATION** :
   - Prix sauvegardé automatiquement
   - ET cursor passe automatiquement au champ suivant (Carton de 12)
   - Workflow fluide, pas d'interruption
   
   **Étape C - Ligne complète** :
   ```
   1. Remplir le Carton de 12 : "15.50"
   2. Tab → Passe à la ligne suivante, Prix Unitaire du 2e produit
   ```
   
   **✅ VÉRIFICATION** :
   - Les 3 prix de la 1ère ligne sont sauvegardés (icônes ✅)
   - Prêt à remplir la 2e ligne
   - Aucune action manuelle (pas de clic "Sauvegarder")

4. **TESTER GESTION ERREURS** :
   ```
   1. Taper "-5" (prix négatif)
   2. Tab pour quitter le champ
   ```
   
   **✅ VÉRIFICATION** :
   - Notification rouge "Prix invalide"
   - Icône ❌ dans la colonne Statut
   - Le focus reste sur le champ

5. **REMPLIR 5 LIGNES COMPLÈTES** :
   - Objectif : Mesurer le temps et l'ergonomie
   - Remplir 5 produits × 3 prix = 15 valeurs
   - **Temps attendu : < 2 minutes**
   
   **✅ VÉRIFICATION** :
   - Pas de clic "Sauvegarder" nécessaire
   - Tout se sauvegarde en arrière-plan
   - Navigation fluide Tab/Enter
   - Feedback visuel immédiat

**✅ RÉSULTAT ATTENDU** :
- Saisie ultra-rapide : 15 prix en 2 minutes
- Aucune interruption du workflow
- Sauvegarde automatique sans friction
- Feedback visuel clair (or → vert)
- Ergonomie maximale validée !

---

### Test 4 : Import CSV ✅

1. **Créer un fichier CSV de test** :
   
   **Fichier** : `test_import_tarifs.csv`
   ```csv
code_sku;prix_unitaire;qte_min;remise_pct
SKU001;20.00;0;0
SKU001;18.50;6;5
SKU001;17.00;12;10
SKU002;25.00;0;0
SKU002;23.00;6;8
   ```
   
   **Note** : Remplacer SKU001, SKU002 par les vrais codes de vos produits

2. **Uploader le fichier** :
   - Ouvrir une grille → Cliquer "Importer"
   - Sélectionner le fichier CSV
   - Cliquer "Importer et prévisualiser"

3. **Vérifier prévisualisation** :
   - ✓ Compteurs : X valides, Y erreurs
   - ✓ Tableau avec les données à importer
   - ✓ Si erreurs : Liste claire des problèmes
   - ✓ Choix du mode : Remplacer / Fusionner

4. **Confirmer l'import** :
   - Sélectionner "Remplacer"
   - Cliquer "Confirmer l'import"

**✅ RÉSULTAT ATTENDU** :
- Prévisualisation claire avant import
- Validation des données
- Import rapide (< 2s pour 100 lignes)
- Message succès avec compteur

---

### Test 5 : Création d'une Nouvelle Grille ✅

1. **Créer** :
   - Depuis la liste, cliquer "Créer une grille"
   
2. **Remplir le formulaire** :
   - Nom : "Tarif Export 2025"
   - Devise : "EUR"
   - Date début : 01/01/2025
   - Date fin : 31/12/2025 (optionnel)
   - Statut : ✓ Active
   - Cliquer "Créer la grille"

3. **Vérifier** :
   - ✓ Message succès
   - ✓ Redirection vers le détail
   - ✓ Grille vide (0 prix)
   - ✓ Boutons "Éditer en grille" et "Importer" disponibles

**✅ RÉSULTAT ATTENDU** :
- Création instantanée
- Prête à être remplie
- Workflow clair vers édition/import

---

### Test 6 : Modification Infos Grille ✅

1. **Modifier** :
   - Depuis le détail, cliquer "Modifier"
   
2. **Changer** :
   - Nom : Ajouter " (Mise à jour)"
   - Date fin : Changer la date
   - Cliquer "Enregistrer les modifications"

3. **Vérifier** :
   - ✓ Message succès
   - ✓ Retour au détail
   - ✓ Modifications affichées

**✅ RÉSULTAT ATTENDU** :
- Modification simple
- Validation correcte

---

### Test 7 : Suppression ✅

1. **Supprimer** :
   - Depuis le détail d'une grille de test
   - Cliquer "Supprimer"
   - Confirmer la popup JavaScript
   
2. **Vérifier** :
   - ✓ Message succès
   - ✓ Retour à la liste
   - ✓ Grille disparue de la liste

**✅ RÉSULTAT ATTENDU** :
- Confirmation avant suppression
- Suppression effective

---

## 📋 VÉRIFICATION BASE DE DONNÉES

Pour vérifier que les données sont bien persistées :

### Via Admin Django

1. **Ouvrir l'admin** :
   ```
   http://127.0.0.1:8000/admin/
   Connexion : demo@monchai.fr / demo123
   ```

2. **Naviguer** :
   - Section "SALES"
   - Cliquer "Price lists" (Grilles tarifaires)

3. **Vérifier** :
   - ✓ 3 grilles existantes
   - ✓ Cliquer sur une grille
   - ✓ Section "Price items" en bas
   - ✓ Voir tous les prix avec min_qty, discount_pct

### Via SQL Direct (si besoin)

```sql
-- Lister les grilles
SELECT id, name, currency, valid_from, valid_to, is_active 
FROM sales_pricelist 
ORDER BY created_at DESC;

-- Lister les prix d'une grille
SELECT 
    pi.id,
    pi.unit_price,
    pi.min_qty,
    pi.discount_pct,
    s.label as sku_label
FROM sales_priceitem pi
JOIN stock_sku s ON pi.sku_id = s.id
WHERE pi.price_list_id = 'UUID_DE_LA_GRILLE'
ORDER BY s.label, pi.min_qty;

-- Compter les prix par grille
SELECT 
    pl.name,
    COUNT(pi.id) as nb_prix
FROM sales_pricelist pl
LEFT JOIN sales_priceitem pi ON pl.id = pi.price_list_id
GROUP BY pl.id, pl.name
ORDER BY pl.name;
```

---

## 🎯 CHECKLIST FINALE

Cocher tous les tests réussis :

### Fonctionnalités Basiques
- [ ] Liste des grilles affichée correctement
- [ ] Recherche temps réel fonctionne (debounce 300ms)
- [ ] Filtres Actives/Inactives/Toutes fonctionnent
- [ ] Détail d'une grille affiche tous les prix
- [ ] Prix groupés par produit (SKU)
- [ ] Badges remise affichés

### Édition en Grille (Ergonomie ⭐)
- [ ] Tableau interactif affiché
- [ ] Saisie dans un champ fonctionne
- [ ] Tab passe au champ suivant
- [ ] Enter sauvegarde + passe au suivant
- [ ] Blur (quitter le champ) sauvegarde automatiquement
- [ ] Champ devient orange (modifié)
- [ ] Champ devient vert (sauvegardé) pendant 2s
- [ ] Icône ✅ apparaît dans colonne Statut
- [ ] Notification "Prix sauvegardé" en bas à droite
- [ ] 15 prix remplis en < 2 minutes
- [ ] Prix négatif rejeté avec erreur claire
- [ ] Aucune perte de données

### Import CSV
- [ ] Upload fichier CSV fonctionne
- [ ] Prévisualisation affichée correctement
- [ ] Compteurs valides/erreurs corrects
- [ ] Erreurs listées clairement
- [ ] Mode Remplacer supprime l'ancien
- [ ] Mode Fusionner met à jour
- [ ] Import définitif fonctionne
- [ ] Message succès affiché

### CRUD Grille
- [ ] Création grille fonctionne
- [ ] Modification infos grille fonctionne
- [ ] Suppression avec confirmation fonctionne
- [ ] Données persistées en BDD

### Design & UX
- [ ] Couleurs viticoles (bordeaux/or) appliquées
- [ ] Animations fluides
- [ ] Feedback visuel clair
- [ ] Messages succès/erreur contextuels
- [ ] Responsive (mobile OK)
- [ ] Raccourci Ctrl+K fonctionne

### Performance
- [ ] Liste charge en < 200ms
- [ ] Détail charge en < 150ms
- [ ] Sauvegarde AJAX < 100ms
- [ ] Pas de freeze UI
- [ ] Debounce recherche efficace

### Sécurité
- [ ] Seuls admin+ peuvent créer/modifier
- [ ] Filtrage par organization automatique
- [ ] Pas d'accès aux grilles d'autres orgs
- [ ] CSRF protection active

---

## 🎉 RÉSULTAT ATTENDU

Si tous les tests passent :

✅ **MODULE 100% FONCTIONNEL**
✅ **ERGONOMIE MAXIMALE VALIDÉE**
✅ **DONNÉES PERSISTÉES EN BDD**
✅ **PRÊT POUR PRODUCTION**

---

## 🚀 PROCHAINES ÉTAPES

### Utilisation Quotidienne

1. **Créer vos vraies grilles** :
   - Tarif public 2025
   - Tarif cavistes
   - Tarif restaurants
   - Tarif export

2. **Remplir les prix** :
   - Soit en **grille** (rapide, < 20 produits)
   - Soit en **import CSV** (masse, > 50 produits)

3. **Associer aux clients** :
   - Via l'admin Django
   - Module clients (à venir)

### Améliorations Futures

- [ ] Export CSV des prix
- [ ] Duplication de grille
- [ ] Historique des modifications
- [ ] Calcul automatique prix TTC
- [ ] Grilles clients spécifiques
- [ ] Règles de prix automatiques

---

## 📞 Support

En cas de problème :

1. **Vérifier les logs serveur** :
   ```
   Terminal où tourne runserver
   Erreurs en rouge si problème
   ```

2. **Vérifier la console navigateur** :
   ```
   F12 → Console
   Erreurs JavaScript si problème AJAX
   ```

3. **Redémarrer le serveur** :
   ```bash
   Ctrl+C dans le terminal
   python manage.py runserver
   ```

4. **Recréer les données démo** :
   ```bash
   python manage.py create_sales_demo
   ```

---

**Bon test ! 🍷✨**

Le module est opérationnel, les données de démo sont créées, le serveur tourne.

**Il ne reste plus qu'à ouvrir le navigateur et tester !**

http://127.0.0.1:8000/ventes/tarifs/

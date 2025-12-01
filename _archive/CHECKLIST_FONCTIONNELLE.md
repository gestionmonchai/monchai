# ✅ Checklist Fonctionnelle Complète - Mon Chai

## 🎯 Objectif
Vérifier que **TOUS** les modules sont fonctionnels, en particulier :
- Dashboard viticole
- Devis/Commandes
- Factures
- Ventes primeur (si applicable)
- UI complète

---

## 1. ✅ DASHBOARD VITICOLE

### Tests à Effectuer

#### Test 1.1 : Accès Dashboard
```
URL: http://127.0.0.1:8000/dashboard/
Attendu: Page charge sans erreur
Statut: ✅ CORRIGÉ (amount_due)
```

#### Test 1.2 : Métriques Affichées
- [ ] Volume récolté (kg + litres)
- [ ] Volume en cuve (litres + nb lots)
- [ ] Chiffre d'affaires (€ TTC + HT + nb factures)
- [ ] Clients actifs
- [ ] Cuvées actives
- [ ] Commandes en cours
- [ ] Factures impayées

#### Test 1.3 : Actions Rapides
- [ ] Bouton "Gérer les clients" → `/ventes/clients/`
- [ ] Bouton "Gérer les cuvées" → `/catalogue/cuvees/`
- [ ] Bouton "Stocks & Transferts" → `/stocks/`
- [ ] Bouton "Vendanges" → `/admin/production/vendangereception/`
- [ ] Bouton "Factures" → `/admin/billing/invoice/`
- [ ] Bouton "Configuration" → `/onboarding/checklist/`

#### Test 1.4 : Responsive
- [ ] Desktop (> 992px) : 3 colonnes métriques
- [ ] Tablet (768-992px) : 1 colonne métriques, 2 colonnes stats
- [ ] Mobile (< 768px) : 1 colonne partout

---

## 2. 📋 MODULE DEVIS

### Tests à Effectuer

#### Test 2.1 : Liste Devis
```
URL: http://127.0.0.1:8000/ventes/devis/
Attendu: Liste des devis avec filtres
Actions:
- [ ] Recherche par client
- [ ] Filtre par statut (draft, sent, accepted, lost, expired)
- [ ] Filtre par date
- [ ] Pagination fonctionne
```

#### Test 2.2 : Création Devis
```
URL: http://127.0.0.1:8000/ventes/devis/nouveau/
Attendu: Formulaire de création
Actions:
- [ ] Sélection client (autocomplétion)
- [ ] Ajout lignes produits
- [ ] Calcul automatique totaux HT/TTC
- [ ] Sauvegarde réussie
- [ ] Redirection vers détail
```

#### Test 2.3 : Détail Devis
```
URL: http://127.0.0.1:8000/ventes/devis/<uuid>/
Attendu: Affichage complet du devis
Vérifications:
- [ ] Informations client
- [ ] Lignes produits
- [ ] Totaux HT/TVA/TTC
- [ ] Statut
- [ ] Date validité
```

#### Test 2.4 : Modification Devis
```
URL: http://127.0.0.1:8000/ventes/devis/<uuid>/modifier/
Attendu: Formulaire pré-rempli
Actions:
- [ ] Modification client
- [ ] Ajout/suppression lignes
- [ ] Modification quantités
- [ ] Recalcul automatique
- [ ] Sauvegarde réussie
```

---

## 3. 📦 MODULE COMMANDES

### Tests à Effectuer

#### Test 3.1 : Liste Commandes
```
URL: http://127.0.0.1:8000/ventes/commandes/
Attendu: Liste des commandes
Statut: ⚠️ PLACEHOLDER (à implémenter)
```

#### Test 3.2 : Création Commande
```
URL: http://127.0.0.1:8000/ventes/commandes/nouveau/
Attendu: Formulaire de création
Statut: ⚠️ PLACEHOLDER (à implémenter)
```

#### Test 3.3 : Conversion Devis → Commande
```
Workflow: Devis accepté → Bouton "Convertir en commande"
Attendu: Création automatique commande
Statut: ⚠️ À IMPLÉMENTER
```

---

## 4. 🧾 MODULE FACTURES

### Tests à Effectuer

#### Test 4.1 : Liste Factures
```
URL: http://127.0.0.1:8000/admin/billing/invoice/
Attendu: Liste admin des factures
Actions:
- [ ] Recherche par numéro/client
- [ ] Filtre par statut (draft, issued, paid, cancelled)
- [ ] Filtre par date
- [ ] Tri par colonnes
```

#### Test 4.2 : Création Facture
```
URL: http://127.0.0.1:8000/admin/billing/invoice/add/
Attendu: Formulaire admin
Actions:
- [ ] Sélection client
- [ ] Sélection commande (optionnel)
- [ ] Ajout lignes
- [ ] Calcul totaux
- [ ] Génération numéro automatique
- [ ] Sauvegarde réussie
```

#### Test 4.3 : Émission Facture
```
Workflow: Facture draft → Statut "issued"
Attendu: 
- [ ] Génération écritures comptables
- [ ] Débit 411 (Client)
- [ ] Crédit 707 (Ventes)
- [ ] Crédit 4457 (TVA)
```

#### Test 4.4 : Paiement Facture
```
Workflow: Facture issued → Enregistrement paiement
Attendu:
- [ ] Création Payment
- [ ] Lettrage automatique (Reconciliation)
- [ ] Mise à jour amount_due
- [ ] Statut → "paid" si soldé
```

---

## 5. 🍷 MODULE VENTES PRIMEUR

### Contexte
Les champs primeur ont été **supprimés** par la migration `0003_remove_customer_sales_customer_segment_idx_and_more`.

### Tests à Effectuer

#### Test 5.1 : Vérifier Suppression
```bash
python manage.py showmigrations sales
```
Attendu: Migration 0003 appliquée ✅

#### Test 5.2 : Modèles Actuels
Vérifier que les modèles Quote/Order n'ont PLUS :
- [ ] ❌ is_primeur
- [ ] ❌ vintage_year
- [ ] ❌ expected_delivery_date
- [ ] ❌ primeur_campaign
- [ ] ❌ primeur_discount_pct

#### Test 5.3 : Réimplémentation (Si Nécessaire)
Si les ventes primeur sont requises :
- [ ] Créer nouvelle migration avec champs primeur
- [ ] Ajouter formulaires spécifiques
- [ ] Créer workflow primeur
- [ ] Tester création devis primeur

---

## 6. 👥 MODULE CLIENTS

### Tests à Effectuer

#### Test 6.1 : Liste Clients
```
URL: http://127.0.0.1:8000/ventes/clients/
Attendu: Liste des clients avec recherche
Actions:
- [ ] Recherche par nom
- [ ] Filtre par type (pro/part)
- [ ] Pagination
- [ ] Export CSV
```

#### Test 6.2 : Création Client
```
URL: http://127.0.0.1:8000/ventes/clients/nouveau/
Attendu: Formulaire de création
Actions:
- [ ] Saisie nom/raison sociale
- [ ] Sélection type (pro/part)
- [ ] Adresse facturation
- [ ] Numéro TVA (si pro)
- [ ] Sauvegarde réussie
```

#### Test 6.3 : Détail Client
```
URL: http://127.0.0.1:8000/ventes/clients/<uuid>/
Attendu: Fiche client complète
Vérifications:
- [ ] Informations générales
- [ ] Adresses
- [ ] Historique devis
- [ ] Historique commandes
- [ ] Historique factures
```

---

## 7. 📦 MODULE STOCKS

### Tests à Effectuer

#### Test 7.1 : Dashboard Stocks
```
URL: http://127.0.0.1:8000/stocks/
Attendu: Vue d'ensemble stocks
Vérifications:
- [ ] Volume total
- [ ] Entrepôts actifs
- [ ] Lots en stock
- [ ] Mouvements récents
```

#### Test 7.2 : Transferts
```
URL: http://127.0.0.1:8000/stocks/transferts/
Attendu: Liste transferts
Actions:
- [ ] Voir historique
- [ ] Créer nouveau transfert
- [ ] Validation stock suffisant
```

---

## 8. 🍇 MODULE PRODUCTION

### Tests à Effectuer

#### Test 8.1 : Vendanges
```
URL: http://127.0.0.1:8000/admin/production/vendangereception/
Attendu: Liste vendanges
Actions:
- [ ] Voir liste
- [ ] Créer vendange
- [ ] Saisir poids (kg)
- [ ] Saisir volume (litres)
- [ ] Affecter parcelle
- [ ] Affecter cuvée
```

---

## 9. 🎨 MODULE CATALOGUE

### Tests à Effectuer

#### Test 9.1 : Liste Cuvées
```
URL: http://127.0.0.1:8000/catalogue/cuvees/
Attendu: Liste des cuvées
Actions:
- [ ] Recherche
- [ ] Filtres (appellation, couleur, millésime)
- [ ] Tri
- [ ] Pagination
```

#### Test 9.2 : Détail Cuvée
```
URL: http://127.0.0.1:8000/catalogue/cuvees/<uuid>/
Attendu: Fiche cuvée complète
Vérifications:
- [ ] Informations générales
- [ ] Appellation
- [ ] Cépages
- [ ] Millésimes disponibles
- [ ] Stock par millésime
```

---

## 10. ⚙️ MODULE CONFIGURATION

### Tests à Effectuer

#### Test 10.1 : Checklist Onboarding
```
URL: http://127.0.0.1:8000/onboarding/checklist/
Attendu: Checklist configuration
Vérifications:
- [ ] Infos exploitation
- [ ] TVA/Taxes
- [ ] Devise/Formats
- [ ] CGV
- [ ] Progression %
```

#### Test 10.2 : Paramètres Facturation
```
URL: http://127.0.0.1:8000/settings/billing/
Attendu: Formulaire paramètres
Actions:
- [ ] Nom légal
- [ ] Adresse fiscale
- [ ] SIRET
- [ ] Numéro TVA
- [ ] Contact facturation
```

---

## 11. 🔐 MODULE AUTHENTIFICATION

### Tests à Effectuer

#### Test 11.1 : Connexion
```
URL: http://127.0.0.1:8000/auth/login/
Actions:
- [ ] Connexion email/password
- [ ] Redirection dashboard
- [ ] Session active
```

#### Test 11.2 : Déconnexion
```
URL: http://127.0.0.1:8000/auth/logout/
Actions:
- [ ] Déconnexion
- [ ] Redirection login
- [ ] Session détruite
```

---

## 12. 📊 TESTS DE PERFORMANCE

### Métriques à Vérifier

#### Dashboard
- [ ] Temps chargement < 500ms
- [ ] 7 requêtes SQL max
- [ ] Pas de N+1 queries

#### Liste Devis
- [ ] Temps chargement < 300ms
- [ ] Pagination efficace
- [ ] Recherche AJAX < 200ms

#### Liste Clients
- [ ] Temps chargement < 400ms
- [ ] Recherche trigram < 600ms
- [ ] Export CSV < 2s pour 1000 clients

---

## 13. 🎨 TESTS UI/UX

### Vérifications Visuelles

#### Responsive
- [ ] Mobile (< 768px) : Navigation hamburger
- [ ] Tablet (768-992px) : Layout adapté
- [ ] Desktop (> 992px) : Toutes colonnes visibles

#### Design System
- [ ] Couleurs cohérentes
- [ ] Typographie uniforme
- [ ] Icônes Bootstrap Icons
- [ ] Boutons styles cohérents
- [ ] Formulaires accessibles

#### Accessibilité
- [ ] Labels sur tous inputs
- [ ] Focus visible
- [ ] Navigation clavier
- [ ] Contraste suffisant
- [ ] Aria labels

---

## 14. 🔧 TESTS TECHNIQUES

### Commandes Django

#### Migrations
```bash
python manage.py showmigrations
```
Attendu: Toutes migrations appliquées ✅

#### Check
```bash
python manage.py check
```
Attendu: 0 issues ✅

#### Tests Unitaires
```bash
python manage.py test
```
Attendu: Tous tests passent

---

## 15. 📝 DOCUMENTATION

### Fichiers à Vérifier

- [ ] README.md à jour
- [ ] DASHBOARD_VITICOLE.md complet
- [ ] DASHBOARD_AMELIORATION_RESUME.md complet
- [ ] DASHBOARD_PREVIEW.md complet
- [ ] Cette CHECKLIST_FONCTIONNELLE.md

---

## 🎯 RÉSUMÉ PRIORITÉS

### Critique (À Tester Immédiatement)
1. ✅ Dashboard viticole (CORRIGÉ)
2. ⏳ Module Devis (liste, création, détail, modification)
3. ⏳ Module Factures (liste, création, émission, paiement)
4. ⏳ Module Clients (liste, création, détail)

### Important (À Tester Ensuite)
5. ⏳ Module Commandes (à implémenter si nécessaire)
6. ⏳ Module Stocks (dashboard, transferts)
7. ⏳ Module Production (vendanges)
8. ⏳ Module Catalogue (cuvées)

### Optionnel (Si Temps Disponible)
9. ⏳ Ventes Primeur (réimplémentation si nécessaire)
10. ⏳ Tests performance
11. ⏳ Tests UI/UX
12. ⏳ Documentation

---

## 🚀 PROCÉDURE DE TEST

### Étape 1 : Démarrer le Serveur
```bash
cd "c:\Users\33685\Desktop\Mon Chai V1"
python manage.py runserver
```

### Étape 2 : Tester Dashboard
```
http://127.0.0.1:8000/dashboard/
```
Vérifier : Pas d'erreur, métriques affichées

### Étape 3 : Tester Devis
```
http://127.0.0.1:8000/ventes/devis/
```
Actions : Liste, création, détail, modification

### Étape 4 : Tester Factures
```
http://127.0.0.1:8000/admin/billing/invoice/
```
Actions : Liste, création, émission

### Étape 5 : Tester Clients
```
http://127.0.0.1:8000/ventes/clients/
```
Actions : Liste, création, détail

### Étape 6 : Cocher Cette Checklist
Au fur et à mesure des tests, cocher les cases ✅

---

## 📞 SUPPORT

### En Cas de Problème

#### Erreur 500
1. Vérifier logs Django
2. Vérifier migrations appliquées
3. Vérifier configuration .env

#### Erreur 404
1. Vérifier URLs configurées
2. Vérifier namespace correct
3. Vérifier vues importées

#### Erreur FieldError
1. Vérifier champs modèle
2. Vérifier properties vs fields DB
3. Corriger requêtes ORM

---

*Checklist créée le : 30/10/2024*
*Version : 1.0*
*Statut : En cours de test*

# DB Roadmap 03 - Ventes, Clients & Pricing

## Vue d'ensemble

Implémentation complète du système de ventes avec CRM simple, gestion des prix flexible et intégration stock selon la DB Roadmap 03.

## Modèles créés

### Gestion des taxes
- **TaxCode** : Codes TVA français et européens (TVA20, TVA10, TVA0, etc.)

### Gestion clients
- **Customer** : Clients B2B/B2C avec adresses facturation/livraison
- **CustomerPriceList** : Association clients-grilles tarifaires avec priorités

### Système de prix
- **PriceList** : Grilles tarifaires avec validité temporelle
- **PriceItem** : Éléments de prix avec seuils quantité et remises

### Documents de vente
- **Quote** : Devis avec statuts (draft, sent, accepted, lost, expired)
- **QuoteLine** : Lignes de devis avec calculs automatiques
- **Order** : Commandes avec statuts et paiement
- **OrderLine** : Lignes de commande avec totaux
- **StockReservation** : Réservations automatiques lors confirmation

## Gestionnaires métier

### PricingManager
- **resolve_price()** : Résolution intelligente des prix
  1. Grilles clients (par priorité)
  2. Grille par défaut organisation
  3. Erreur si non trouvé
- **get_tax_code()** : Détermination TVA selon client/pays

### SalesManager
- **create_quote_from_cart()** : Création devis depuis panier
- **convert_quote_to_order()** : Conversion devis→commande
- **confirm_order()** : Confirmation avec réservations stock
- **fulfill_order()** : Expédition avec mouvements stock
- **cancel_order()** : Annulation et libération réservations

## Règles métier implémentées

### Résolution des prix
1. **Priorité clients** : Grilles spécifiques par priorité
2. **Seuils quantité** : Prix dégressifs selon min_qty
3. **Remises** : Pourcentages de remise par tranche
4. **Fallback** : Grille par défaut si pas de prix client

### Gestion TVA
- **France** : TVA 20% standard
- **Pro UE avec TVA** : Autoliquidation (0%)
- **Pro UE sans TVA** : TVA française (20%)
- **Hors UE** : Pas de TVA (0%)

### Workflow ventes
1. **Panier** → **Devis** (draft)
2. **Devis** → **Accepté** → **Commande** (draft)
3. **Commande** → **Confirmée** (réservations stock)
4. **Commande** → **Expédiée** (mouvements stock)

## Contraintes d'intégrité

- **UNIQUE** : (organization, legal_name) sur Customer
- **UNIQUE** : (organization, code) sur TaxCode  
- **UNIQUE** : (price_list, sku, min_qty) sur PriceItem
- **UNIQUE** : (order, sku, warehouse) sur StockReservation
- **FK same org** : Validation cross-organisation sur toutes relations
- **Quantités positives** : MinValueValidator sur qty, unit_price
- **Dates cohérentes** : valid_to > valid_from sur PriceList

## Index de performance

### Recherche clients
- **BTree** : (organization, legal_name)
- **BTree** : (organization, vat_number)
- **BTree** : (organization, type)

### Résolution prix
- **Composite** : (price_list, sku, min_qty)

### Historique ventes
- **Composite** : (organization, created_at) sur Quote/Order
- **Composite** : (organization, customer) sur Quote/Order
- **Composite** : (organization, status) sur Quote/Order

### Réservations stock
- **Composite** : (organization, sku, warehouse)
- **Composite** : (organization, order)

## Tests de robustesse

### SalesModelsTestCase (9 tests)
1. **test_customer_creation_and_validation** : Clients B2B/B2C
2. **test_price_list_and_items** : Grilles et seuils
3. **test_pricing_manager_resolution** : Résolution prix intelligente
4. **test_quote_creation_and_totals** : Calculs automatiques devis
5. **test_sales_manager_quote_creation** : Création via gestionnaire
6. **test_order_confirmation_and_stock_reservation** : Réservations
7. **test_insufficient_stock_error** : Validation stock suffisant
8. **test_cross_organization_validation** : Isolation multi-tenant
9. **test_tax_code_resolution** : TVA selon client/pays

## Interface d'administration

### Modèles configurés
- **TaxCodeAdmin** : Codes taxes avec filtres pays/taux
- **CustomerAdmin** : Clients avec recherche et fieldsets
- **PriceListAdmin** : Grilles avec inline PriceItem
- **QuoteAdmin** : Devis avec inline QuoteLine
- **OrderAdmin** : Commandes avec inline OrderLine + StockReservation

### Fonctionnalités
- **Recherche** : Par nom client, numéro TVA, produit
- **Filtres** : Par statut, pays, devise, organisation
- **Readonly** : Totaux calculés, métadonnées
- **Inlines** : Lignes et réservations dans documents

## Commandes de gestion

### create_sales_demo
```bash
python manage.py create_sales_demo
python manage.py create_sales_demo --org-name "Mon Domaine"
```

**Génère** :
- 4 codes taxes (TVA20, TVA10, TVA0, VAT20)
- 5 clients (2 particuliers, 3 professionnels)
- 3 grilles tarifaires (Public, Professionnel, VIP)
- 24 éléments de prix (avec seuils et remises)
- 2 devis de démonstration
- 1 commande confirmée avec réservations

## Intégration avec modules existants

### Stock (DB Roadmap 02)
- **SKU** : Référencés dans PriceItem et lignes
- **StockSKUBalance** : Vérification disponibilité
- **StockManager** : Mouvements lors expédition
- **Warehouse** : Réservations par entrepôt

### Viticulture (DB Roadmap 01)
- **Organization** : RLS et isolation données
- **UnitOfMeasure** : Via SKU pour pricing

### Accounts
- **User** : Audit trail sur mouvements
- **Organization** : Multi-tenant complet

## Performance attendue

### Résolution prix
- **p95 < 100ms** : Grilles clients avec cache
- **Seuils quantité** : Index composite efficace

### Recherche clients
- **p95 < 50ms** : Index sur nom et TVA
- **Pagination** : Keyset sur created_at

### Calculs totaux
- **Temps réel** : Calculs automatiques sur save()
- **Cohérence** : Transactions atomiques

## Sécurité et permissions

### RLS logique
- **Filtrage automatique** : Par organization sur tous querysets
- **Validation FK** : Same-org sur toutes relations
- **Isolation complète** : Multi-tenant étanche

### Validation métier
- **Stock suffisant** : Avant confirmation commande
- **Prix obligatoire** : Erreur si non trouvé
- **Quantités positives** : Validation sur tous champs
- **Dates cohérentes** : Validation temporelle

## Évolutions futures

### Roadmap 04 - Facturation
- **Invoice** : Génération depuis Order
- **Payment** : Suivi paiements
- **Credit** : Avoirs et remboursements

### Roadmap 05 - Reporting
- **CA par client/période** : Agrégations
- **Marges par produit** : Analyse rentabilité
- **Prévisions** : Tendances ventes

---

**Status** : DB Roadmap 03 - 100% TERMINÉE ✅  
**Fondation** : Solide pour facturation et reporting (DB04-05)  
**Tests** : 9 tests robustes - 100% de succès  
**Données démo** : Prêtes pour validation utilisateur

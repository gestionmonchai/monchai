# Documentation Mon Chai

## Module Production
Le cœur du système. Gère le cycle de vie du vin de la vigne à la bouteille.
- **Vigne** : Gestion des parcelles (`/production/parcelles/`) et des vendanges (`/production/vendanges/`).
- **Chai** :
  - **Encuvage** : Transformation de la vendange en lot technique (vrac).
  - **Lots Techniques** : Les cuves en cours de vinification. On y saisit les analyses (densité, température) et les opérations (soutirage, ouillage).
  - **Assemblage** : Mélange de plusieurs lots.
- **Élevage** : Suivi du vieillissement.
- **Conditionnement** : Mises en bouteille (OF). Transforme du vrac (Lot technique) en produit fini (Stock SKU).

## Module Achat / Ventes
Gère la commercialisation.
- **Clients** : Base de données clients (`/ventes/clients/`). Types : Particulier, Pro, Caviste, Export.
- **Devis & Commandes** : Création de pièces commerciales.
- **Factures** : Génération des factures et suivi des paiements.
- **Vente Primeur** : Gestion spécifique des réservations avant disponibilité.
- **Vente Vrac** : Vente de vin en gros (négoce).

## Module DRM & Réglementaire
Assure la conformité douanière.
- **DRM** : Déclaration Récapitulative Mensuelle. Générée automatiquement d'après les mouvements de stock.
- **DAE / DSA** : Documents d'accompagnement pour le transport.
- **CRD** : Capsules Représentatives de Droits (gestion du stock de capsules).
- **Registres INAO** : Tracabilité légale.

## Module Stocks
Vue globale des stocks.
- **Produits Finis** : Bouteilles prêtes à la vente (Catalogue produits).
- **Matières Sèches** : Bouchons, étiquettes, cartons.
- **Inventaires** : Saisie des inventaires physiques.

## Référentiels
Configuration des données maîtresses.
- **Cépages** : Liste des variétés de raisins.
- **Cuvées** : Les "marques" du domaine. Définissent les assemblages types et les tarifs.
- **Cuves & barriques** : Cuves, fûts, amphores, barriques.

## Aide Démarrage (Onboarding)
Pour commencer :
1. Créer les **Parcelles** et **Cépages**.
2. Configurer les **Cuvées**.
3. Saisir une **Vendange**.
4. Faire un **Encuvage** pour créer du stock vrac.

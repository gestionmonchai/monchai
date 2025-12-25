# 📖 Guide Complet des Fonctionnalités MonChai

> **Version:** 2.0  
> **Dernière mise à jour:** Décembre 2024  
> **Application:** MonChai - Gestion Viticole SaaS

---

## 🏠 Vue d'Ensemble

MonChai est une application SaaS complète pour la gestion viticole, couvrant l'ensemble de la chaîne de production du raisin à la bouteille, incluant la traçabilité, la gestion commerciale et les déclarations réglementaires (DRM).

### Architecture Fonctionnelle

```
┌─────────────────────────────────────────────────────────────────┐
│                        MONCHAI                                  │
├─────────────┬─────────────┬─────────────┬─────────────┬────────┤
│   VIGNE     │    CHAI     │   ÉLEVAGE   │  COMMERCE   │  DRM   │
├─────────────┼─────────────┼─────────────┼─────────────┼────────┤
│ • Parcelles │ • Vendanges │ • Contenants│ • Clients   │• Export│
│ • Cépages   │ • Encuvages │ • Analyses  │ • Devis     │• CRD   │
│ • Journal   │ • Soutirages│ • Assemblage│ • Commandes │• INAO  │
│ • Météo     │ • Vinif.    │ • Mises     │ • Factures  │        │
└─────────────┴─────────────┴─────────────┴─────────────┴────────┘
```

---

## 🔐 Module Authentification & Organisation

### Fonctionnalités Principales

#### Gestion des Comptes
- **Inscription** : Création de compte avec email et mot de passe sécurisé
- **Connexion** : Authentification avec protection contre les attaques brute-force
- **Récupération mot de passe** : Réinitialisation par email sécurisé
- **Profil utilisateur** : Modification des informations personnelles

#### Multi-Organisation (Multi-Chai)
- **Création d'organisations** : Créer plusieurs domaines viticoles
- **Sélection d'organisation** : Basculer entre différents chais
- **Invitation de membres** : Inviter par email avec rôle prédéfini
- **Gestion des rôles** : Owner, Admin, Manager, Member, Viewer

#### Rôles et Permissions

| Rôle | Description | Permissions |
|------|-------------|-------------|
| **Owner** | Propriétaire | Tous droits + suppression org |
| **Admin** | Administrateur | Tous droits sauf suppression org |
| **Manager** | Gestionnaire | CRUD données + invitations |
| **Member** | Membre | CRUD données limitées |
| **Viewer** | Lecteur | Lecture seule |

#### Dashboard Personnalisable
- **Widgets déplaçables** : Réorganiser les blocs d'information
- **Configuration** : Ajouter/supprimer des widgets
- **Sauvegarde** : Configuration persistante par utilisateur
- **Widgets disponibles** :
  - Statistiques production
  - Alertes stock
  - Derniers mouvements
  - Météo parcelles
  - Prochaines tâches
  - Graphiques ventes

### Cas d'Usage

**Créer une nouvelle organisation :**
1. Aller dans `/auth/organizations/`
2. Cliquer sur "Nouvelle organisation"
3. Renseigner le nom du domaine
4. Valider → Devenir automatiquement Owner

**Inviter un collaborateur :**
1. Aller dans `/auth/settings/roles/`
2. Cliquer "Inviter"
3. Saisir email + choisir rôle
4. L'invité reçoit un email avec lien d'acceptation

---

## 🍇 Module Production - Vigne

### Gestion des Parcelles

#### Fonctionnalités
- **Création de parcelle** : Nom, surface, commune, code cadastral
- **Géolocalisation** : Coordonnées GPS, intégration carte
- **Encépagement** : Association parcelle ↔ cépages avec proportions
- **Historique** : Suivi des évolutions de la parcelle

#### Informations d'une Parcelle
- Identifiant unique
- Nom usuel
- Surface (ha)
- Code cadastral (section + numéro)
- Commune
- Appellation (AOC/IGP)
- Mode de culture (conventionnel, bio, biodynamie)
- Date de plantation
- Encépagement détaillé

### Journal Cultural Unifié

Le journal cultural regroupe trois registres en un seul :

#### Onglet Interventions
- Travaux du sol (labour, enherbement)
- Taille et palissage
- Effeuillage, épamprage
- Vendanges en vert

#### Onglet Phytosanitaire
- Traitements fongicides
- Traitements insecticides
- Produits utilisés (nom, dose, DAR)
- Registre conforme réglementation

#### Onglet Maturité
- Prélèvements de baies
- Mesures de sucre (°Brix, densité)
- Acidité totale
- pH
- État sanitaire

### Alertes Météo (Smart Suggestions)

Intégration météo Open-Meteo avec alertes intelligentes :
- **Risque de pluie** : Alerte lessivage traitement
- **Risque de gel** : Alerte protection vignoble
- **Vent fort** : Alerte dérive produits phyto
- **Canicule** : Alerte stress hydrique

### Cas d'Usage

**Enregistrer un traitement phyto :**
1. Aller dans `/production/journal-cultural/?tab=phyto`
2. Cliquer "Nouveau traitement"
3. Sélectionner parcelle(s)
4. Renseigner produit, dose, conditions
5. Valider → Enregistrement horodaté

---

## 🍷 Module Production - Chai

### Gestion des Vendanges

#### Saisie Terrain (Mobile-First)
- Interface tactile optimisée
- Boutons de poids rapides (+100, +250, +500 kg)
- Sélection parcelle → Pré-remplissage infos
- Géolocalisation automatique
- Mode hors-ligne préparé

#### Informations Vendange
- Date et heure
- Parcelle source
- Poids récolté (kg)
- Degré potentiel (°)
- État sanitaire
- Équipe de récolte
- Destination (cuve)

### Encuvages & Vinification

#### Wizard Encuvage
1. **Sélection vendange** : Choisir l'apport à encuver
2. **Destination** : Sélectionner cuve(s) disponible(s)
3. **Répartition** : Si multi-cuves, définir les volumes
4. **Validation** : Création lot technique automatique

#### Opérations de Vinification
- **Remontage** : Avec date, durée, température
- **Délestage** : Volume, durée
- **Pigeage** : Fréquence, intensité
- **Sulfitage** : Dose SO2, méthode
- **Levurage** : Type levure, dose
- **Enzymage** : Produit, dose
- **Collage** : Produit, dose

### Lots Techniques

#### Vue Cuvée
Interface principale montrant :
- État de chaque cuve
- Volume actuel / Capacité
- Lot technique en cours
- Dernières opérations
- Prochaines tâches

#### Informations Lot Technique
- Identifiant unique (auto-généré)
- Millésime
- Cuvée associée
- Couleur (rouge, blanc, rosé)
- Volume actuel
- Contenant(s) de stockage
- Historique complet des opérations

### Soutirages

#### Wizard Soutirage
1. **Source** : Sélectionner contenant source
2. **Destination** : Sélectionner contenant(s) cible(s)
3. **Volume** : Définir volume à transférer
4. **Options** : Ouillage, sulfitage
5. **Validation** : Traçabilité complète

### Contenants (Cuves, Fûts, Barriques)

#### Types de Contenants
- Cuve inox
- Cuve béton
- Cuve fibre
- Fût bois (chêne)
- Barrique (225L, 228L, 300L)
- Demi-muid (500-600L)
- Foudre (1000L+)

#### Informations Contenant
- Identifiant (code ou nom)
- Type et matériau
- Capacité (L)
- Volume actuel
- Localisation (chai, travée)
- État (neuf, X passages)
- Lot technique affecté

#### Actions sur Contenant
- **Affecter lot** : Lier un lot technique
- **Vidanger** : Vider complètement
- **Nettoyage** : Enregistrer un nettoyage
- **Recalculer** : Mise à jour occupation

### Cas d'Usage

**Créer un soutirage :**
1. Aller dans `/production/soutirages/nouveau/`
2. Sélectionner cuve source
3. Sélectionner cuve(s) destination
4. Définir volume
5. Cocher options (ouillage, SO2)
6. Valider → Mouvements enregistrés

---

## 🏺 Module Production - Élevage

### Analyses Œnologiques

#### Types d'Analyses
- **Fermentaire** : Densité, température, sucres résiduels
- **Chimique** : TAV, AT, pH, AV, SO2 libre/total
- **Microbiologique** : Population levures, bactéries
- **Organoleptique** : Dégustation notée

#### Saisie d'Analyse
1. Sélectionner lot technique
2. Choisir type d'analyse
3. Saisir les valeurs
4. Joindre document (optionnel)
5. Valider → Historique alimenté

#### Alertes Analyse (Smart Suggestions)
- **AV élevée** : Alerte risque piqûre
- **SO2 bas** : Alerte protection insuffisante
- **pH hors normes** : Alerte stabilité
- **Variations rapides** : Détection anomalies

### Assemblages

#### Wizard Assemblage
1. **Lots sources** : Sélectionner lots à assembler
2. **Proportions** : Définir % de chaque lot
3. **Destination** : Cuve ou nouveau lot
4. **Nom cuvée** : Associer à une cuvée produit
5. **Validation** : Traçabilité complète

#### Règles Métier
- Vérification compatibilité appellations
- Calcul volume résultant
- Mise à jour stocks sources
- Création lot assemblé

### Mises en Bouteille

#### Wizard Mise
**Étape 1 - Source :**
- Sélection lot(s) technique(s)
- Volume disponible affiché

**Étape 2 - Conditionnement :**
- Format bouteille (75cl, 150cl, etc.)
- Nombre de bouteilles
- Calcul automatique volume
- Pertes estimées

**Étape 3 - Produit :**
- Association SKU produit
- Millésime
- Lot commercial généré

**Étape 4 - Validation :**
- Récapitulatif
- Confirmation
- Création lot commercial

### Cas d'Usage

**Créer un assemblage :**
1. Aller dans `/production/assemblages/nouveau/`
2. Sélectionner lots sources (2 minimum)
3. Définir proportions (total = 100%)
4. Choisir destination
5. Nommer la cuvée résultante
6. Valider → Nouveau lot créé

---

## 📦 Module Inventaire

### Vue Inventaire Unifiée

Interface à onglets :
- **Vrac** : Lots techniques en cuves
- **Produits** : Bouteilles conditionnées
- **Lots commerciaux** : Lots prêts à la vente
- **Matières sèches** : Bouchons, étiquettes, cartons

### Matières Sèches (MS)

#### Gestion MS
- **Entrée** : Réception fournisseur
- **Transfert** : Entre emplacements
- **Ajustement** : Correction inventaire
- **Seuils** : Alertes stock mini

#### Types MS
- Bouteilles vides
- Bouchons (liège, synthétique, vis)
- Capsules
- Étiquettes
- Contre-étiquettes
- Cartons (1, 3, 6, 12 bout.)
- Intercalaires

### Inventaire Physique

#### Processus
1. **Lancement** : Créer session inventaire
2. **Comptage** : Saisie quantités par emplacement
3. **Écarts** : Calcul automatique différences
4. **Validation** : Approbation des écarts
5. **Application** : Ajustements stock

### Alertes Stock

#### Types d'Alertes
- Stock sous seuil minimum
- Stock proche épuisement
- Péremption proche (MS)
- Capacité cuve dépassée

#### Configuration Seuils
- Définition par produit/article
- Seuil minimum (alerte orange)
- Seuil critique (alerte rouge)
- Notifications par email (optionnel)

---

## 👥 Module Clients (CRM)

### Types de Clients

| Type | Caractéristiques |
|------|------------------|
| **Particulier** | Nom, prénom, préférences vin |
| **Professionnel** | Raison sociale, SIRET, contact |
| **Caviste** | Enseigne, volume annuel, gamme |
| **Export** | TVA intra, Incoterm, langue |

### Fiche Client (5 Volets)

#### Volet 1 : Identité & Coordonnées
- Type client
- Raison sociale / Nom
- Contact principal
- Email, téléphone
- Canal d'acquisition
- Statut (prospect, actif, inactif)
- Tags personnalisés
- Consentement marketing

#### Volet 2 : Commercial & Fiscalité
- Famille tarifaire
- Remise par défaut
- Tarifs spécifiques
- Mode de paiement
- Délais de paiement
- Plafond encours
- Conditions d'escompte
- SIRET, TVA intra

#### Volet 3 : Adresses & Logistique
- Adresse facturation
- Adresse(s) livraison
- Contact livraison
- Créneaux réception
- Conditionnement préféré
- Instructions spéciales

#### Volet 4 : Historique & Performance
- CA 12 derniers mois
- Nombre de commandes
- Panier moyen
- Dernière commande
- Produits favoris
- Taux de réachat
- Retards paiement
- Segmentation RFM

#### Volet 5 : Documents & Conformité
- Pièces KYC/KYB
- Mandat SEPA / RIB
- CGV signées
- Contrats spécifiques
- Préférences RGPD
- Intégrations (ERP, CRM)

### Fonctionnalités Avancées

- **Détection doublons** : Alerte création client similaire
- **Suggestions auto** : Autocomplétion à la saisie
- **Export** : CSV, Excel avec filtres
- **Recherche avancée** : Multi-critères, tags

---

## 💰 Module Commerce

### Cycle de Vente

```
Devis → Commande → Livraison (BL) → Facture → Encaissement
```

#### Devis / Proforma
- Création rapide depuis client
- Lignes produits avec prix unitaire
- Remises (ligne, global)
- Validité configurable
- Transformation en commande (1 clic)

#### Commandes Clients
- Depuis devis ou directe
- Réservation stock optionnelle
- Statuts : Brouillon, Validée, En préparation, Expédiée
- Génération BL automatique

#### Bons de Livraison
- Depuis commande ou direct
- Quantités livrées vs commandées
- Signature électronique (optionnel)
- Impact stock automatique

#### Factures
- Depuis BL ou commande
- Numérotation automatique
- TVA calculée automatiquement
- PDF généré
- Envoi email intégré

### Cycle d'Achat

```
Demande de prix → Commande → Réception → Facture → Paiement
```

#### Fournisseurs
- Même structure que clients
- Catalogue articles associé
- Conditions d'achat

#### Documents Achat
- Demande de prix
- Commande fournisseur
- Bon de réception
- Facture fournisseur
- Avoirs

### Gestion Tarifaire

#### Grilles Tarifaires
- Création de grilles par segment
- Prix par SKU
- Import/export CSV
- Édition en grille (style Excel)
- Historique des prix

#### Conditions Commerciales
- Remises par famille client
- Escompte paiement rapide
- Franco de port (montant mini)
- Incoterms (export)

### Templates Documents

#### Builder Visuel
- Drag & drop des blocs
- Variables dynamiques
- Aperçu temps réel
- Export PDF

#### Variables Disponibles
- `{{client.nom}}` : Nom client
- `{{document.numero}}` : N° document
- `{{document.date}}` : Date document
- `{{ligne.produit}}` : Nom produit
- `{{ligne.quantite}}` : Quantité
- `{{total.ttc}}` : Total TTC
- Et bien plus...

---

## 📊 Module DRM (Déclaration Récapitulative Mensuelle)

### Fonctionnalités

#### Dashboard DRM
- Période courante
- Statut déclaration
- Échéances
- Historique

#### Éditeur de Brouillon
- Calcul automatique depuis mouvements
- Vérification cohérence
- Modification manuelle possible
- Aperçu avant export

#### Export
- Format CSV (douanes)
- Format PDF (archive)
- Checksum pour intégrité
- Historique exports

### Codes INAO

- Recherche par appellation
- Filtrage par région
- Association produits
- Import référentiel officiel

### Timer Légal (Smart Suggestions)

- Notification J-10 avant échéance
- Pré-remplissage automatique
- Alerte documents manquants
- Statuts : À faire, En cours, Transmis, Validé

---

## 📚 Module Référentiels

### Cépages
- Nom officiel et synonymes
- Code INAO
- Couleur
- Caractéristiques

### Unités de Mesure
- Nom et symbole
- Catégorie (volume, poids, quantité)
- Conversions

### Entrepôts
- Nom et localisation
- Type (chai, stockage sec)
- Emplacements
- Capacité totale

### Import CSV
- Validation format
- Aperçu avant import
- Rapport d'erreurs
- Import partiel possible

---

## 🤖 Module IA - Aide Intelligente

### Assistant Contextuel

- Aide contextuelle par page
- Recherche dans documentation
- Suggestions basées sur le contexte
- Raccourci : `?` ou `Ctrl+H`

### Smart Suggestions

#### Météo-Sensible
- Alertes météo par parcelle
- Suggestions d'actions
- Prévisions 7 jours

#### Calculateur Destination
- Score de compatibilité cuve
- Mise en évidence visuelle
- Grisage cuves inadaptées

#### Détective d'Analyse
- Alertes valeurs hors normes
- Détection variations rapides
- Suggestions correctives

#### Timer DRM
- Rappels automatiques
- Pré-brouillon alimenté
- Deadline tracking

#### Mémoire Intrants
- Historique par opération
- Pré-remplissage formulaires
- Suggestions basées usage

---

## ⚙️ Paramètres & Configuration

### Paramètres Organisation
- Informations légales
- Logo et personnalisation
- Devise et TVA
- Numérotation documents

### Paramètres Utilisateur
- Langue interface
- Fuseau horaire
- Notifications
- Dashboard personnalisé

### Intégrations
- Webhook sortants
- API tokens
- Connexions ERP/CRM

---

## 📱 Ergonomie & Navigation

### Responsive Design
- Desktop optimisé
- Tablette adapté
- Mobile fonctionnel (saisie terrain)

### Raccourcis Globaux
| Touche | Action |
|--------|--------|
| `Ctrl+K` | Recherche globale |
| `Ctrl+N` | Nouveau (contextuel) |
| `?` | Aide contextuelle |
| `Esc` | Fermer modal |

### Navigation
- Menu latéral rétractable
- Fil d'Ariane (breadcrumb)
- Tabs pour sous-sections
- Recherche instantanée

---

*Documentation générée pour MonChai v2.0 - Système d'aide ULTRA performant*

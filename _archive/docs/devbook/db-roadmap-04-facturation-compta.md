# DB Roadmap 04 - Facturation & Comptabilité

## Vue d'ensemble

Implémentation complète du système de facturation et comptabilité avec écritures automatiques, lettrage des paiements et exports comptables selon la DB Roadmap 04.

## Modèles créés

### Facturation
- **Invoice** : Factures avec numérotation séquentielle française (YYYY-NNNN)
- **InvoiceLine** : Lignes de facture avec calculs automatiques HT/TTC
- **CreditNote** : Avoirs avec numérotation AV-YYYY-NNNN

### Paiements et lettrage
- **Payment** : Encaissements clients avec méthodes (SEPA, carte, chèque, espèces)
- **Reconciliation** : Lettrage paiements-factures avec allocation multi-factures

### Comptabilité
- **AccountMap** : Plan comptable paramétrable par organisation
- **GLEntry** : Écritures comptables automatiques (journal VEN, BAN, OD)

## Gestionnaires métier

### BillingManager
- **generate_invoice_number()** : Numérotation séquentielle française
- **create_invoice_from_order()** : Facturation automatique depuis commandes
- **issue_invoice()** : Émission avec génération écritures comptables
- **create_credit_note()** : Création avoirs avec écritures inverses
- **allocate_payment()** : Lettrage automatique avec mise à jour statuts

### AccountingManager
- **create_invoice_entries()** : Écritures facture (411/707/4457)
- **create_payment_entries()** : Écritures paiement (512/411)
- **export_journal()** : Export CSV/JSON paramétrables
- **get_account_code()** : Résolution comptes via mapping ou défauts

## Règles métier implémentées

### Numérotation française
- **Factures** : YYYY-NNNN (ex: 2025-0001)
- **Avoirs** : AV-YYYY-NNNN (ex: AV-2025-0001)
- **Séquentiel par année** : Reset automatique chaque année

### Workflow facturation
1. **Commande expédiée** → **Facture (draft)**
2. **Émission facture** → **Écritures comptables** + **Status issued**
3. **Paiement reçu** → **Lettrage** → **Status paid**
4. **Avoir** → **Écritures inverses**

### Lettrage intelligent
- **Multi-paiements** sur une facture
- **Multi-factures** avec un paiement
- **Trop-perçu** géré automatiquement
- **Statut automatique** : paid quand soldé

### Écritures comptables automatiques
**Facture émise** :
- Débit 411 (Client) = Total TTC
- Crédit 707 (Ventes) = Total HT
- Crédit 4457 (TVA) = Total TVA

**Paiement reçu** :
- Débit 512 (Banque) = Montant
- Crédit 411 (Client) = Montant

**Avoir** :
- Écritures inverses de la facture

## Contraintes d'intégrité

- **UNIQUE** : (organization, number) sur Invoice et CreditNote
- **UNIQUE** : (payment, invoice) sur Reconciliation
- **UNIQUE** : (organization, mapping_type, key) sur AccountMap
- **Validation** : due_date >= date_issue sur Invoice
- **Validation** : Débit XOR Crédit sur GLEntry (pas les deux)
- **FK same org** : Validation cross-organisation sur toutes relations

## Index de performance

### Facturation
- **Composite** : (organization, customer, date_issue) sur Invoice
- **Composite** : (organization, status, date_issue) sur Invoice
- **BTree** : (organization, number) pour recherche rapide

### Paiements
- **Composite** : (organization, customer, date_received) sur Payment
- **Composite** : (organization, method, date_received) sur Payment

### Comptabilité
- **Composite** : (organization, journal, date) sur GLEntry
- **Composite** : (organization, account_code, date) sur GLEntry
- **Composite** : (organization, doc_type, doc_id) pour traçabilité

## Gestion des arrondis

### Arrondi bancaire ROUND_HALF_UP
- **Totaux lignes** : HT et TVA arrondis à 2 décimales
- **Totaux factures** : Somme des lignes arrondies
- **Avoirs proportionnels** : Calculs avec arrondi cohérent

## Tests de robustesse

### BillingModelsTestCase (15 tests)
1. **test_invoice_number_generation** : Numérotation séquentielle
2. **test_create_invoice_from_order** : Facturation depuis commande
3. **test_issue_invoice_and_accounting_entries** : Écritures automatiques
4. **test_payment_and_reconciliation** : Lettrage simple
5. **test_partial_payment_allocation** : Paiements partiels
6. **test_multiple_payments_on_invoice** : Multi-paiements
7. **test_credit_note_creation** : Avoirs avec calculs
8. **test_account_mapping** : Plan comptable personnalisé
9. **test_journal_export_csv** : Export comptable
10. **test_cross_organization_validation** : Isolation multi-tenant
11. **test_rounding_consistency** : Cohérence arrondis
12. **test_gl_entry_debit_credit_validation** : Validation écritures
13. **test_invoice_due_date_validation** : Validation dates
14. **test_overpayment_allocation** : Gestion trop-perçu
15. **test_invoice_cannot_be_created_twice_from_order** : Unicité facturation

## Interface d'administration

### Modèles configurés
- **InvoiceAdmin** : Factures avec inline lignes et réconciliations
- **PaymentAdmin** : Paiements avec inline réconciliations
- **CreditNoteAdmin** : Avoirs avec liens factures
- **GLEntryAdmin** : Écritures readonly (générées automatiquement)
- **AccountMapAdmin** : Plan comptable par organisation

### Fonctionnalités
- **Recherche** : Par numéro, client, référence paiement
- **Filtres** : Par statut, méthode, journal, organisation
- **Readonly** : Totaux calculés, écritures comptables
- **Indicateurs** : Retards de paiement, montants dus

## Plan comptable français

### Comptes par défaut
- **707** : Ventes de marchandises
- **4457** : TVA collectée
- **411** : Clients
- **512** : Banque
- **530** : Caisse

### Mapping personnalisable
- **Produits** : Par SKU ou catégorie
- **Clients** : Par type (pro/particulier)
- **Taxes** : Par code TVA
- **Paiements** : Par méthode

## Commandes de gestion

### create_billing_demo
```bash
python manage.py create_billing_demo
python manage.py create_billing_demo --org-name "Mon Domaine"
```

**Génère** :
- 13 comptes comptables (plan français standard)
- 2 factures manuelles émises avec écritures
- 2 paiements avec lettrage (1 partiel, 1 complet)
- 1 avoir de démonstration (30% d'une facture)
- 11 écritures comptables automatiques
- Export CSV/JSON de démonstration

## Exports comptables

### Formats supportés
- **CSV** : Séparateur point-virgule, format français
- **JSON** : Structure complète avec métadonnées

### Journaux disponibles
- **VEN** : Journal des ventes (factures, avoirs)
- **BAN** : Journal de banque (paiements)
- **OD** : Opérations diverses

### Colonnes exportées
- Date, Journal, Pièce, Compte, Libellé, Débit, Crédit

## Intégration avec modules existants

### Sales (DB Roadmap 03)
- **Order** : Facturation automatique des commandes expédiées
- **Customer** : Réutilisation clients avec adresses
- **TaxCode** : Calculs TVA cohérents

### Stock (DB Roadmap 02)
- **SKU** : Référencés dans lignes de facture
- **Audit trail** : Traçabilité complète

### Accounts
- **Organization** : Multi-tenant avec plan comptable
- **User** : Audit trail sur émissions et paiements

## Performance attendue

### Facturation
- **p95 < 200ms** : Création facture depuis commande
- **p95 < 100ms** : Émission avec écritures comptables

### Lettrage
- **p95 < 50ms** : Allocation paiement simple
- **p95 < 150ms** : Multi-allocation complexe

### Exports
- **p95 < 500ms** : Export mensuel (< 1000 écritures)
- **Streaming** : Gros volumes via pagination

## Sécurité et conformité

### RLS logique
- **Filtrage automatique** : Par organization sur tous querysets
- **Validation FK** : Same-org sur toutes relations
- **Isolation comptable** : Étanche par organisation

### Audit trail
- **Écritures append-only** : Pas de modification/suppression
- **Traçabilité complète** : Doc_type + doc_id sur toutes écritures
- **Numérotation** : Séquentielle et sans trou

### Conformité française
- **Numérotation** : Séquentielle par année
- **Plan comptable** : PCG français standard
- **TVA** : Calculs conformes réglementation

## Évolutions futures

### Roadmap 05 - Reporting
- **Tableaux de bord** : CA, encours, retards
- **Analyses** : Marges, rentabilité client
- **Prévisions** : Cash-flow, saisonnalité

### Intégrations
- **Export-comptable** : Sage, Ciel, EBP
- **Paiements en ligne** : Stripe, PayPal
- **Relances automatiques** : Email, courrier

---

**Status** : DB Roadmap 04 - 100% TERMINÉE ✅  
**Fondation** : Solide pour reporting et analyses (DB05)  
**Tests** : 15 tests robustes - 100% de succès  
**Données démo** : Factures, paiements, écritures prêtes

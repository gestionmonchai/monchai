# Matrice RBAC - Mon Chai V1

## Date : 2025-09-24

## 🎭 Rôles définis

### 1. SuperAdmin (interne)
- **Contexte** : Équipe technique Mon Chai
- **Accès** : Total à tout, y compris `/admin/` Django
- **Responsabilités** : Maintenance technique, support niveau 3

### 2. AdminOrganisation (propriétaire)
- **Contexte** : Propriétaire du vignoble/domaine
- **Accès** : Gestion complète de son organisation
- **Responsabilités** : Gestion utilisateurs, paramètres, données métier

### 3. Manager (responsable)
- **Contexte** : Chef de cave, responsable production
- **Accès** : Création/modification produits, clients, commandes
- **Responsabilités** : Gestion opérationnelle quotidienne

### 4. Comptabilité (financier)
- **Contexte** : Responsable administratif et financier
- **Accès** : Lecture ventes, export, factures, écriture paiements
- **Responsabilités** : Suivi financier, facturation, reporting

### 5. Opérateur (caviste)
- **Contexte** : Personnel de production et logistique
- **Accès** : Lecture + création limitée (mouvements stock)
- **Responsabilités** : Saisie des mouvements, inventaires

### 6. Partenaire (externe)
- **Contexte** : Distributeur, négociant, client professionnel
- **Accès** : Lecture restreinte (cuvées publiques, tarifs négociés)
- **Responsabilités** : Consultation catalogue, commandes

### 7. LectureSeule (consultant)
- **Contexte** : Consultant, auditeur, stagiaire
- **Accès** : Lecture globale de l'organisation, aucune écriture
- **Responsabilités** : Consultation, reporting, analyse

---

## 📊 Matrice de Permissions

| Domaine | Action | SuperAdmin | AdminOrg | Manager | Comptabilité | Opérateur | Partenaire | LectureSeule |
|---------|--------|------------|----------|---------|--------------|-----------|------------|--------------|
| **CATALOGUE** | | | | | | | | |
| Voir produits | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 Publics | ✅ |
| Créer produits | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier produits | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer produits | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Exporter catalogue | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **CLIENTS** | | | | | | | | |
| Voir clients | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Créer clients | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier clients | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer clients | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Exporter clients | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **VENTES** | | | | | | | | |
| Voir devis/commandes | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 Ses commandes | ✅ |
| Créer devis/commandes | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Modifier devis/commandes | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer devis/commandes | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Voir factures | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Créer factures | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Voir paiements | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Saisir paiements | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Approuver factures | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **STOCKS** | | | | | | | | |
| Voir stocks | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 Ses entrepôts | ✅ |
| Créer mouvements | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Modifier mouvements | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Supprimer mouvements | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Faire inventaires | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Gérer seuils/alertes | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **RÉFÉRENTIELS** | | | | | | | | |
| Voir référentiels | ✅ | ✅ | ✅ | ✅ | ✅ | 🔒 Publics | ✅ |
| Créer référentiels | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modifier référentiels | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Supprimer référentiels | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Importer données | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **PARAMÈTRES** | | | | | | | | |
| Voir paramètres org | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Modifier paramètres org | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gérer taxes/remises | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **UTILISATEURS** | | | | | | | | |
| Voir utilisateurs org | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Inviter utilisateurs | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Modifier rôles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Supprimer utilisateurs | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 🔒 Règles spéciales

### Restrictions par rôle

**Partenaire externe :**
- ✅ Voir uniquement les cuvées marquées "publiques"
- ✅ Voir ses propres commandes uniquement
- ✅ Tarifs négociés spécifiques à son compte
- ❌ Aucune donnée interne (coûts, marges, etc.)

**Opérateur :**
- ✅ Mouvements de stock dans ses entrepôts assignés
- ✅ Inventaires des zones dont il est responsable
- ❌ Pas d'accès aux données financières
- ❌ Pas de suppression de données

**Comptabilité :**
- ✅ Accès complet aux données financières
- ✅ Export pour reporting externe
- ❌ Pas de modification des données produits
- ❌ Pas de gestion des utilisateurs

### Hiérarchie des rôles

```
SuperAdmin > AdminOrganisation > Manager > Comptabilité/Opérateur > Partenaire > LectureSeule
```

**Règles d'héritage :**
- Un rôle supérieur peut faire tout ce qu'un rôle inférieur peut faire
- Exception : Comptabilité et Opérateur ont des périmètres différents (pas d'héritage direct)
- SuperAdmin peut tout faire dans toutes les organisations

### Actions sensibles nécessitant confirmation

**Suppression de données :**
- Clients avec commandes → Confirmation + justification
- Produits avec stock → Confirmation + impact calculé
- Utilisateurs actifs → Confirmation + transfert de responsabilités

**Modifications financières :**
- Factures validées → Nécessite rôle Comptabilité + confirmation
- Paiements > 1000€ → Double validation (AdminOrg + Comptabilité)
- Remises > 20% → Validation AdminOrganisation

---

## 🎯 Cas d'usage typiques

### Scénario 1 : Nouveau caviste
**Rôle assigné** : Opérateur
**Accès** : Entrepôt "Cave principale" uniquement
**Peut** : Saisir mouvements, faire inventaires de sa zone
**Ne peut pas** : Voir les prix, modifier les produits, accéder aux autres entrepôts

### Scénario 2 : Comptable externe
**Rôle assigné** : Comptabilité
**Accès** : Données financières complètes
**Peut** : Créer factures, saisir paiements, exporter données
**Ne peut pas** : Modifier les produits, gérer les utilisateurs

### Scénario 3 : Distributeur partenaire
**Rôle assigné** : Partenaire
**Accès** : Catalogue public + ses commandes
**Peut** : Consulter disponibilités, passer commandes
**Ne peut pas** : Voir les coûts, accéder aux données internes

### Scénario 4 : Propriétaire du domaine
**Rôle assigné** : AdminOrganisation
**Accès** : Contrôle total de son organisation
**Peut** : Tout gérer sauf l'admin technique Django
**Ne peut pas** : Accéder aux autres organisations

---

**Matrice validée : 7 rôles × 6 domaines × 5 actions = 210 permissions définies**

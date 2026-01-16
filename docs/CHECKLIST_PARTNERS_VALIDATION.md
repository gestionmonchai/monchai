# Checklist de Validation - Refonte Système Contacts/Partners

## 🎯 Objectif
Validation manuelle (smoke test) de la nouvelle architecture unifiée des tiers (clients, fournisseurs, contacts).

---

## ✅ 1. INSTALLATION & MIGRATIONS

- [ ] **Vérifier l'app dans settings**
  ```
  'apps.partners' présent dans INSTALLED_APPS
  ```

- [ ] **Appliquer les migrations**
  ```bash
  python manage.py migrate partners
  ```

- [ ] **Créer les rôles par défaut**
  ```bash
  python manage.py shell
  >>> from apps.partners.models import PartnerRole
  >>> PartnerRole.ensure_defaults()
  ```

- [ ] **Migrer les données existantes (optionnel)**
  ```bash
  python manage.py migrate partners 0002_migrate_customers_to_partners
  ```

---

## ✅ 2. NAVIGATION & MENUS

### 2.1 Menu Référentiels
- [ ] Aller dans Référentiels > Entité switcher
- [ ] Vérifier que "Contacts (Tiers)" apparaît dans la liste
- [ ] Cliquer dessus → redirection vers `/contacts/`

### 2.2 Menu Ventes
- [ ] Aller dans Ventes > Clients (sidebar)
- [ ] Vérifier la redirection vers `/contacts/clients/`
- [ ] Liste filtrée : uniquement les partenaires avec rôle "Client"

### 2.3 Menu Achats
- [ ] Aller dans Achats > Fournisseurs (sidebar)
- [ ] Vérifier la redirection vers `/contacts/fournisseurs/`
- [ ] Liste filtrée : uniquement les partenaires avec rôle "Fournisseur"

---

## ✅ 3. LISTE DES PARTENAIRES

### 3.1 Liste globale (`/contacts/`)
- [ ] Page accessible sans erreur
- [ ] Affichage de tous les partenaires (tous rôles)
- [ ] Colonnes visibles : Code, Nom, Rôles, Contact, Localisation, Statut, Actions
- [ ] Badge de rôle affiché (Client = bleu, Fournisseur = vert, etc.)

### 3.2 Recherche
- [ ] Saisir un texte dans le champ recherche
- [ ] Résultats filtrés en temps réel (debounce ~300ms)
- [ ] Compteur "X résultats sur Y" mis à jour

### 3.3 Filtres avancés
- [ ] Cliquer sur "Avancé"
- [ ] Filtrer par Segment → résultats corrects
- [ ] Filtrer par Statut (Actif/Inactif) → résultats corrects
- [ ] Filtrer par Pays → résultats corrects
- [ ] Bouton "Effacer" → reset tous les filtres

### 3.4 Pagination
- [ ] Vérifier la pagination si >25 partenaires
- [ ] Cliquer sur page suivante → chargement correct

---

## ✅ 4. CRÉATION DE PARTENAIRE

### 4.1 Depuis liste globale
- [ ] Cliquer sur "Nouveau"
- [ ] Formulaire affiché avec tous les champs
- [ ] Sélectionner rôles (checkboxes)
- [ ] Remplir infos obligatoires (Nom)
- [ ] Soumettre → création réussie
- [ ] Redirection vers fiche détail

### 4.2 Depuis Ventes > Clients
- [ ] Cliquer sur "Nouveau" 
- [ ] Rôle "Client" pré-coché
- [ ] Création → partenaire avec rôle Client

### 4.3 Depuis Achats > Fournisseurs
- [ ] Cliquer sur "Nouveau"
- [ ] Rôle "Fournisseur" pré-coché
- [ ] Création → partenaire avec rôle Fournisseur

### 4.4 Validation
- [ ] Tester SIRET invalide (pas 14 chiffres) → erreur
- [ ] Tester TVA invalide → erreur
- [ ] Nom vide → erreur

---

## ✅ 5. FICHE PARTENAIRE (DÉTAIL)

### 5.1 Onglet Aperçu
- [ ] Infos générales affichées (type, email, téléphone)
- [ ] Infos légales affichées (SIRET, TVA)
- [ ] Adresse principale affichée (si existe)
- [ ] Contact principal affiché (si existe)
- [ ] Profil Client visible (si rôle Client)
- [ ] Profil Fournisseur visible (si rôle Fournisseur)

### 5.2 Onglet Interlocuteurs
- [ ] Liste des contacts affichée
- [ ] Bouton "Ajouter" fonctionnel
- [ ] Création interlocuteur → ajouté à la liste
- [ ] Suppression interlocuteur → confirmation + suppression

### 5.3 Onglet Adresses
- [ ] Liste des adresses affichée
- [ ] Types d'adresses visibles (Facturation, Livraison, etc.)
- [ ] Badge "Par défaut" visible
- [ ] Ajout/Suppression fonctionnel

### 5.4 Onglets conditionnels
- [ ] Onglet "Ventes" visible uniquement si rôle Client
- [ ] Onglet "Achats" visible uniquement si rôle Fournisseur

### 5.5 Timeline
- [ ] Onglet Timeline accessible
- [ ] Événements affichés (si existants)

---

## ✅ 6. MODIFICATION

- [ ] Cliquer sur "Modifier" depuis la fiche
- [ ] Formulaire pré-rempli avec valeurs actuelles
- [ ] Modifier un champ → enregistrer
- [ ] Valeurs mises à jour correctement

---

## ✅ 7. RÔLES MULTIPLES

### 7.1 Partenaire Client ET Fournisseur
- [ ] Créer un partenaire avec rôles Client + Fournisseur
- [ ] Vérifier dans liste globale : 2 badges affichés
- [ ] Vérifier dans Ventes > Clients : partenaire visible
- [ ] Vérifier dans Achats > Fournisseurs : même partenaire visible
- [ ] Fiche détail : onglets Ventes ET Achats visibles

### 7.2 Ajouter un rôle
- [ ] Ouvrir fiche d'un Client
- [ ] Menu actions > "Ajouter un rôle"
- [ ] Sélectionner "Fournisseur" → valider
- [ ] Partenaire maintenant visible dans Achats > Fournisseurs

---

## ✅ 8. ARCHIVAGE

- [ ] Depuis fiche : Menu > Archiver
- [ ] Confirmation → partenaire archivé
- [ ] Partenaire plus visible dans les listes
- [ ] Restaurer le partenaire → visible à nouveau

---

## ✅ 9. PROFILS SPÉCIFIQUES

### 9.1 Profil Client
- [ ] Ouvrir fiche d'un Client
- [ ] Carte "Profil client" visible
- [ ] Cliquer sur modifier (crayon)
- [ ] Modifier conditions paiement, remise, encours
- [ ] Enregistrer → valeurs mises à jour

### 9.2 Profil Fournisseur
- [ ] Ouvrir fiche d'un Fournisseur
- [ ] Carte "Profil fournisseur" visible
- [ ] Modifier incoterm, délai, commande min
- [ ] Enregistrer → valeurs mises à jour

---

## ✅ 10. API / AJAX

### 10.1 Recherche AJAX
- [ ] Taper dans la recherche → requête AJAX envoyée
- [ ] Résultats mis à jour sans rechargement page

### 10.2 API Suggestions
- [ ] Tester `/contacts/api/suggestions/?q=test`
- [ ] Réponse JSON avec suggestions

### 10.3 Création rapide (si implémentée)
- [ ] POST `/contacts/api/creation-rapide/`
- [ ] Partenaire créé et retourné en JSON

---

## ✅ 11. COMPATIBILITÉ ANCIENNE APP

### 11.1 URLs Legacy
- [ ] `/referentiels/clients/` → toujours accessible (ancienne app)
- [ ] Données visibles (pas cassé)

### 11.2 Commerce/Documents
- [ ] Créer un document commercial (devis, commande)
- [ ] Sélectionner un client → fonctionne
- [ ] Les anciens documents restent liés

---

## 📊 RÉSUMÉ DES TESTS

| Section | Statut |
|---------|--------|
| Installation | ⬜ |
| Navigation | ⬜ |
| Liste partenaires | ⬜ |
| Création | ⬜ |
| Fiche détail | ⬜ |
| Modification | ⬜ |
| Rôles multiples | ⬜ |
| Archivage | ⬜ |
| Profils spécifiques | ⬜ |
| API/AJAX | ⬜ |
| Compatibilité legacy | ⬜ |

---

## 🐛 BUGS TROUVÉS

| # | Description | Sévérité | Statut |
|---|-------------|----------|--------|
| 1 | | | |
| 2 | | | |

---

## 📝 NOTES

- Date de validation : ____/____/____
- Validé par : ________________
- Version : 1.0.0

---

## 🚀 PROCHAINES ÉTAPES (après validation)

1. [ ] Migrer les données clients existants
2. [ ] Brancher les documents commerciaux vers Partner
3. [ ] Retirer l'ancienne app clients (après période de transition)
4. [ ] Ajouter export CSV/Excel des partenaires
5. [ ] Implémenter détection de doublons

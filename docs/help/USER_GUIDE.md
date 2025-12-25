# 📚 Guide Utilisateur MonChai

> **Pour les nouveaux utilisateurs et la formation**  
> Version 2.0 - Décembre 2024

---

## 🚀 Premiers Pas

### 1. Créer votre Compte

1. Accédez à `/auth/signup/`
2. Renseignez :
   - Votre email professionnel
   - Un mot de passe sécurisé (8+ caractères, majuscule, chiffre)
   - Votre nom complet
3. Cliquez "Créer mon compte"
4. Vérifiez votre email et cliquez sur le lien de confirmation

### 2. Créer votre Premier Domaine

Après connexion, si vous n'avez pas d'organisation :

1. Vous êtes redirigé vers `/auth/first-run/`
2. Cliquez "Créer mon domaine viticole"
3. Renseignez le nom de votre exploitation
4. Validez → Vous êtes maintenant propriétaire (Owner)

### 3. Configurer votre Dashboard

1. Allez dans `/auth/dashboard/configure/`
2. Glissez-déposez les widgets souhaités
3. Configurez chaque widget (période, filtres)
4. Cliquez "Sauvegarder"

---

## 🍇 Gérer mes Parcelles

### Créer une Parcelle

1. Menu : **Production** → **Parcelles**
2. Cliquez le bouton **+ Nouvelle parcelle**
3. Remplissez les informations :
   - **Nom usuel** : ex. "Les Grands Coteaux"
   - **Surface** : en hectares (ex. 2.50)
   - **Commune** : sélectionnez ou saisissez
   - **Code cadastral** : Section + Numéro (ex. A 123)
   - **Appellation** : AOC/IGP associée
   - **Mode de culture** : Conventionnel, Bio, Biodynamie
4. Cliquez **Enregistrer**

### Définir l'Encépagement

1. Ouvrez la fiche de la parcelle
2. Section "Encépagement" → **+ Ajouter cépage**
3. Sélectionnez le cépage (ex. Cabernet Sauvignon)
4. Indiquez la proportion (ex. 60%)
5. Répétez pour chaque cépage
6. Le total doit faire 100%

### Consulter la Météo

1. Ouvrez la fiche d'une parcelle
2. Widget "Météo" affiche :
   - Conditions actuelles
   - Prévisions 7 jours
   - Alertes (gel, pluie, vent)

---

## 📝 Journal Cultural

### Enregistrer une Intervention

1. Menu : **Production** → **Journal Cultural**
2. Onglet **Interventions**
3. Cliquez **+ Nouvelle intervention**
4. Sélectionnez :
   - **Parcelle(s)** concernée(s)
   - **Type** : Taille, Labour, Effeuillage, etc.
   - **Date et durée**
   - **Personnel** (optionnel)
   - **Notes** (optionnel)
5. Cliquez **Enregistrer**

### Enregistrer un Traitement Phyto

1. Onglet **Phytosanitaire**
2. Cliquez **+ Nouveau traitement**
3. Remplissez :
   - **Parcelle(s)** traitée(s)
   - **Produit** : nom commercial
   - **Matière active**
   - **Dose** : en L/ha ou kg/ha
   - **Volume de bouillie** : L/ha
   - **DAR** : Délai Avant Récolte
   - **Conditions météo**
4. Cliquez **Enregistrer**

> ⚠️ Ce registre est obligatoire réglementairement

### Suivi Maturité

1. Onglet **Maturité**
2. Cliquez **+ Nouveau prélèvement**
3. Renseignez :
   - **Parcelle** et **Cépage**
   - **Date** de prélèvement
   - **Sucre** : °Brix ou densité
   - **Acidité totale** : g/L H2SO4
   - **pH**
   - **État sanitaire** : Sain, Botrytis, Mildiou, etc.
4. Cliquez **Enregistrer**

---

## 🍷 Vendanges & Encuvage

### Saisir une Vendange (Terrain)

L'interface terrain est optimisée pour les smartphones :

1. Menu : **Production** → **Vendanges** → **+ Nouveau**
2. **Sélection parcelle** : Liste déroulante ou scan QR
3. **Poids** : Utilisez les boutons rapides (+100, +250, +500 kg) ou saisissez
4. **Degré** : Mesuré au réfractomètre
5. **État sanitaire** : Sain / Léger botrytis / etc.
6. **Destination** : Cuve cible (optionnel)
7. Cliquez **Enregistrer** → Retour rapide pour saisie suivante

### Encuver une Vendange

1. Ouvrez la fiche vendange
2. Cliquez **Encuver**
3. **Wizard Encuvage** :
   - Étape 1 : Vérifiez les infos vendange
   - Étape 2 : Sélectionnez la/les cuve(s) destination
   - Étape 3 : Si multi-cuves, répartissez les volumes
   - Étape 4 : Confirmez
4. Un **lot technique** est automatiquement créé

---

## 🏺 Gestion des Cuves

### Créer un Contenant

1. Menu : **Production** → **Contenants** → **+ Nouveau**
2. Remplissez :
   - **Identifiant** : Code ou nom (ex. "Cuve 01" ou "C01")
   - **Type** : Cuve inox, Cuve béton, Fût, Barrique...
   - **Capacité** : en litres
   - **Localisation** : Chai, travée (optionnel)
   - **Année** : Pour les barriques
3. Cliquez **Enregistrer**

### Vue Cuvée (Plan du Chai)

1. Menu : **Production** → **Lots Techniques**
2. Vue par défaut = "Vue Cuvée"
3. Chaque carte représente une cuve :
   - **Couleur** = Type de vin (rouge/blanc/rosé)
   - **Remplissage** = Volume actuel vs capacité
   - **Badge** = Opération récente
4. Cliquez une cuve pour voir le détail du lot

### Effectuer un Soutirage

1. Menu : **Production** → **Soutirages** → **+ Nouveau**
2. **Wizard Soutirage** :
   - **Source** : Sélectionnez cuve origine
   - **Volume** : Quantité à transférer
   - **Destination** : Cuve(s) cible(s)
   - **Options** : 
     - ☑️ Ouillage destination
     - ☑️ Sulfitage (dose SO2)
3. Cliquez **Valider**
4. Les volumes sont mis à jour automatiquement

---

## 🔬 Analyses Œnologiques

### Saisir une Analyse

1. Menu : **Production** → **Lots Élevage** → **Analyses**
2. Cliquez **+ Nouvelle analyse**
3. Remplissez :
   - **Lot technique** : Sélectionnez le lot
   - **Date** d'analyse
   - **Type** : Fermentaire, Chimique, etc.
   - **Valeurs** selon le type :
     - TAV (% vol)
     - Acidité totale (g/L)
     - pH
     - Acidité volatile (g/L)
     - SO2 libre / total (mg/L)
     - Sucres résiduels (g/L)
4. Joignez un document (optionnel)
5. Cliquez **Enregistrer**

### Alertes Automatiques

Le système détecte automatiquement :
- **AV > 0.60 g/L** → Alerte piqûre acétique
- **SO2 libre < 20 mg/L** → Alerte protection insuffisante
- **pH > 3.8** → Alerte stabilité
- **Variation AV > 0.10/semaine** → Alerte évolution rapide

---

## 🍾 Assemblage & Mise en Bouteille

### Créer un Assemblage

1. Menu : **Production** → **Assemblages** → **+ Nouveau**
2. **Wizard Assemblage** :
   - Étape 1 : Sélectionnez les lots sources (2 minimum)
   - Étape 2 : Définissez les proportions (total = 100%)
   - Étape 3 : Choisissez la destination (nouvelle cuve ou existante)
   - Étape 4 : Associez une cuvée produit
3. Cliquez **Valider**
4. Un nouveau lot technique est créé avec la traçabilité

### Faire une Mise en Bouteille

1. Menu : **Production** → **Mises** → **+ Nouveau**
2. **Wizard Mise** :
   - **Étape 1 - Source** :
     - Sélectionnez le(s) lot(s) technique(s)
     - Volume disponible affiché
   - **Étape 2 - Conditionnement** :
     - Format : 75cl, 150cl, etc.
     - Nombre de bouteilles
     - Pertes estimées calculées
   - **Étape 3 - Produit** :
     - SKU produit associé
     - Millésime
   - **Étape 4 - Confirmation** :
     - Récapitulatif complet
     - Cliquez **Valider**
3. Un **lot commercial** est créé, le stock est mis à jour

---

## 👥 Gestion des Clients

### Créer un Client

1. Menu : **Référentiels** → **Clients** → **+ Nouveau**
2. Choisissez le **type** :
   - 🧑 Particulier
   - 🏢 Professionnel
   - 🍷 Caviste
   - 🌍 Export
3. Remplissez les champs (adaptés au type)
4. Ajoutez des **adresses** (facturation, livraison)
5. Définissez les **conditions commerciales** (volet 2)
6. Cliquez **Enregistrer**

### Voir l'Historique Client

1. Ouvrez la fiche client
2. Onglet **Historique & Performance** (volet 4)
3. Consultez :
   - CA 12 derniers mois
   - Nombre de commandes
   - Panier moyen
   - Produits favoris
   - Dernière commande

---

## 💰 Créer une Vente

### Créer un Devis

1. Menu : **Ventes** → **Devis** → **+ Nouveau**
2. **En-tête** :
   - Sélectionnez le **client**
   - Date et validité
3. **Lignes** :
   - Cliquez **+ Ajouter ligne**
   - Sélectionnez le **produit** (SKU)
   - Quantité et prix unitaire
   - Remise éventuelle
4. Vérifiez les **totaux**
5. Cliquez **Enregistrer** (brouillon) ou **Valider**

### Transformer en Commande

1. Ouvrez le devis validé
2. Cliquez **→ Transformer en commande**
3. Vérifiez/modifiez si besoin
4. Cliquez **Créer la commande**

### Créer une Facture

1. Depuis une commande livrée :
   - Cliquez **→ Facturer**
2. Ou depuis le menu **Ventes** → **Factures** → **+ Nouvelle**
3. Vérifiez les informations
4. Cliquez **Valider**
5. **PDF généré** automatiquement
6. Option : **Envoyer par email** au client

---

## 📊 DRM (Déclaration Mensuelle)

### Préparer la DRM

1. Menu : **DRM** → **Éditer**
2. Le système pré-remplit depuis les mouvements du mois
3. Vérifiez chaque ligne :
   - Entrées (vendanges, achats)
   - Sorties (ventes, pertes)
   - Stock fin de mois
4. Corrigez si nécessaire
5. Cliquez **Enregistrer brouillon**

### Exporter la DRM

1. Menu : **DRM** → **Export**
2. Sélectionnez la période
3. Choisissez le format :
   - **CSV** : Pour télédéclaration douanes
   - **PDF** : Pour archivage
4. Cliquez **Télécharger**
5. Téléversez sur ProDouane (site douanes)

---

## 🔔 Alertes & Rappels

### Créer une Alerte

1. Menu : **Production** → **Alertes** → **+ Nouvelle**
2. Remplissez :
   - **Titre** : Description courte
   - **Type** : Tâche, Rappel, Deadline
   - **Date échéance**
   - **Priorité** : Basse, Normale, Haute, Urgente
   - **Lot/Contenant** associé (optionnel)
3. Cliquez **Enregistrer**

### Gérer les Alertes

- **Voir** : Menu **Production** → **Alertes**
- **Terminer** : Cliquez ✓ sur l'alerte
- **Reporter** : Cliquez 🕐 et choisissez nouvelle date
- **Ignorer** : Cliquez ✗ pour fermer sans action

---

## 👤 Mon Compte

### Modifier mon Profil

1. Cliquez votre nom (haut droite)
2. → **Mon profil**
3. Modifiez :
   - Nom, prénom
   - Langue interface
   - Fuseau horaire
   - Photo de profil
4. Cliquez **Enregistrer**

### Changer mon Mot de Passe

1. **Mon profil** → Onglet **Sécurité**
2. Saisissez :
   - Mot de passe actuel
   - Nouveau mot de passe (2 fois)
3. Cliquez **Changer le mot de passe**

### Gérer mes Sessions

1. **Mon profil** → Onglet **Sessions**
2. Voyez tous les appareils connectés
3. Cliquez **Révoquer** pour déconnecter un appareil

---

## 👥 Inviter des Collaborateurs

### Envoyer une Invitation

1. Menu : **Auth** → **Gestion des rôles**
2. Cliquez **+ Inviter**
3. Renseignez :
   - **Email** du collaborateur
   - **Rôle** : Admin, Manager, Member, Viewer
   - **Message** personnalisé (optionnel)
4. Cliquez **Envoyer**

### Rôles Disponibles

| Rôle | Ce qu'il peut faire |
|------|---------------------|
| **Admin** | Tout, sauf supprimer l'organisation |
| **Manager** | Gérer données + inviter (pas facturation) |
| **Member** | Créer et modifier données courantes |
| **Viewer** | Consulter uniquement (lecture seule) |

---

## ❓ Aide & Support

### Aide Contextuelle

- Appuyez sur **?** sur n'importe quelle page
- Ou cliquez l'icône **?** en bas à droite
- L'assistant affiche l'aide pour la page actuelle

### Recherche Globale

- Appuyez sur **Ctrl+K** (ou Cmd+K sur Mac)
- Tapez votre recherche
- Résultats : pages, clients, produits, lots...
- Entrée pour accéder directement

### Support

- Email : support@monchai.fr
- Documentation : `/docs/`
- FAQ : `/faq/`

---

## 💡 Astuces Productivité

### Raccourcis Clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+K` | Recherche globale |
| `Ctrl+N` | Nouveau (contextuel) |
| `?` | Aide contextuelle |
| `Esc` | Fermer modal |
| `Tab` | Champ suivant |
| `Shift+Tab` | Champ précédent |

### Mode Terrain (Mobile)

1. Accédez depuis votre smartphone
2. Interface adaptée automatiquement
3. Gros boutons pour faciliter la saisie
4. Boutons de quantité rapides
5. Géolocalisation automatique

### Filtres Sauvegardés

1. Sur une liste (clients, produits...)
2. Appliquez vos filtres
3. Cliquez **Sauvegarder filtre**
4. Nommez-le
5. Retrouvez-le dans le menu filtres

---

*Guide Utilisateur MonChai v2.0 - Pour toute question, consultez l'aide contextuelle (?)*

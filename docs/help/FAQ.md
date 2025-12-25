# ❓ FAQ MonChai - Questions Fréquentes

> **Version:** 2.0  
> **Dernière mise à jour:** Décembre 2024

---

## 🚀 Démarrage

### Comment créer mon compte ?
1. Allez sur `/auth/signup/`
2. Renseignez votre email et un mot de passe sécurisé
3. Validez et vérifiez votre email
4. Créez votre première organisation (domaine viticole)

### J'ai oublié mon mot de passe, que faire ?
1. Allez sur `/auth/login/`
2. Cliquez "Mot de passe oublié"
3. Saisissez votre email
4. Suivez le lien reçu par email pour définir un nouveau mot de passe

### Comment inviter un collaborateur ?
1. Menu **Auth** → **Gestion des rôles**
2. Cliquez **+ Inviter**
3. Saisissez l'email et choisissez le rôle
4. L'invitation est envoyée par email

### Quels sont les différents rôles ?
| Rôle | Permissions |
|------|-------------|
| **Owner** | Tous droits + suppression organisation |
| **Admin** | Tous droits sauf suppression organisation |
| **Manager** | Gestion données + invitations |
| **Member** | Création/modification données courantes |
| **Viewer** | Lecture seule |

---

## 🍇 Production - Vigne

### Comment créer une parcelle ?
1. **Production** → **Parcelles** → **+ Nouvelle parcelle**
2. Renseignez : nom, surface, commune, code cadastral
3. Définissez l'appellation et le mode de culture
4. Ajoutez l'encépagement (cépages et proportions)

### Comment définir l'encépagement d'une parcelle ?
1. Ouvrez la fiche de la parcelle
2. Section "Encépagement" → **+ Ajouter cépage**
3. Sélectionnez le cépage et indiquez la proportion (%)
4. Répétez pour chaque cépage (total = 100%)

### Comment enregistrer un traitement phytosanitaire ?
1. **Production** → **Journal Cultural** → Onglet **Phyto**
2. Cliquez **+ Nouveau traitement**
3. Renseignez : parcelle, produit, dose, DAR, conditions météo
4. Ce registre est obligatoire réglementairement

### Comment voir les prévisions météo d'une parcelle ?
1. Ouvrez la fiche de la parcelle
2. Le widget "Météo" affiche les conditions actuelles et prévisions
3. Les alertes (gel, pluie, vent) sont automatiques

---

## 🍷 Production - Chai

### Comment saisir une vendange ?
1. **Production** → **Vendanges** → **+ Nouveau**
2. Sélectionnez la parcelle
3. Saisissez le poids (boutons rapides disponibles)
4. Renseignez le degré potentiel et l'état sanitaire
5. L'interface terrain est optimisée pour les smartphones

### Comment encuver une vendange ?
1. Ouvrez la fiche de la vendange
2. Cliquez **Encuver**
3. Suivez le wizard : sélectionnez la cuve, validez
4. Un lot technique est automatiquement créé

### Comment faire un soutirage ?
1. **Production** → **Soutirages** → **+ Nouveau**
2. Sélectionnez la cuve source
3. Définissez le volume à transférer
4. Choisissez la ou les cuves de destination
5. Options : ouillage, sulfitage
6. Validez → Les volumes sont mis à jour

### Comment créer un assemblage ?
1. **Production** → **Assemblages** → **+ Nouveau**
2. Sélectionnez les lots sources (2 minimum)
3. Définissez les proportions (total = 100%)
4. Choisissez la destination
5. Associez à une cuvée produit

### Comment enregistrer une analyse ?
1. **Production** → **Lots Élevage** → **Analyses**
2. Cliquez **+ Nouvelle analyse**
3. Sélectionnez le lot, saisissez les valeurs
4. Les alertes sont automatiques si valeurs hors normes

---

## 🍾 Conditionnement

### Comment faire une mise en bouteille ?
1. **Production** → **Mises** → **+ Nouveau**
2. Étape 1 : Sélectionnez le(s) lot(s) source(s)
3. Étape 2 : Choisissez le format, définissez le nombre
4. Étape 3 : Associez au SKU produit
5. Validez → Le lot commercial est créé

### Comment voir mon stock de bouteilles ?
1. **Production** → **Inventaire** → Onglet **Produits**
2. Ou **Stocks** → Vue consolidée
3. Filtrez par produit, millésime, emplacement

---

## 👥 Clients & Ventes

### Comment créer un client ?
1. **Référentiels** → **Clients** → **+ Nouveau**
2. Choisissez le type : Particulier, Pro, Caviste, Export
3. Les champs s'adaptent au type sélectionné
4. Complétez les 5 volets d'information

### Comment créer un devis ?
1. **Ventes** → **Devis** → **+ Nouveau**
2. Sélectionnez le client
3. Ajoutez les lignes produits
4. Appliquez les remises éventuelles
5. Validez ou enregistrez en brouillon

### Comment transformer un devis en commande ?
1. Ouvrez le devis validé
2. Cliquez **→ Transformer en commande**
3. Vérifiez les informations
4. Cliquez **Créer la commande**

### Comment créer une facture ?
1. Depuis une commande livrée : cliquez **→ Facturer**
2. Ou **Ventes** → **Factures** → **+ Nouvelle**
3. Vérifiez les informations, validez
4. Le PDF est généré automatiquement

### Comment gérer les grilles tarifaires ?
1. **Ventes** → **Grilles tarifaires**
2. Créez une grille par segment (public, pro, export)
3. Définissez les prix par SKU
4. Importez depuis Excel si besoin

---

## 📊 DRM & Réglementation

### Comment préparer ma DRM ?
1. **DRM** → **Éditer**
2. Le système pré-remplit depuis vos mouvements du mois
3. Vérifiez chaque ligne (entrées, sorties, stocks)
4. Corrigez si nécessaire
5. Enregistrez le brouillon

### Comment exporter ma DRM ?
1. **DRM** → **Export**
2. Sélectionnez la période
3. Choisissez le format : CSV (douanes) ou PDF (archivage)
4. Téléchargez et téléversez sur ProDouane

### Quelle est l'échéance de la DRM ?
La DRM doit être transmise avant le **10 du mois suivant** la période déclarée.
Exemple : DRM de décembre 2024 à transmettre avant le 10 janvier 2025.

### Comment trouver un code INAO ?
1. **DRM** → **Codes INAO**
2. Recherchez par nom d'appellation
3. Filtrez par région ou type (AOC, IGP)

---

## 📦 Stocks & Inventaire

### Comment voir mes stocks ?
1. **Production** → **Inventaire** : Vue unifiée (vrac, produits, MS)
2. **Stocks** : Dashboard avec mouvements et alertes
3. Filtrez par type, couleur, emplacement

### Comment faire un inventaire physique ?
1. **Stocks** → **Inventaires** → **+ Nouveau**
2. Lancez une session d'inventaire
3. Saisissez les quantités comptées
4. Le système calcule les écarts
5. Validez les ajustements

### Comment configurer les alertes de stock ?
1. **Stocks** → **Seuils**
2. Définissez un seuil minimum par produit
3. Les alertes se déclenchent automatiquement
4. Visible dans le dashboard et la cloche

### Comment faire un transfert entre emplacements ?
1. **Stocks** → **Transferts** → **+ Nouveau**
2. Sélectionnez l'article et la quantité
3. Origine → Destination
4. Validez le transfert

---

## ⚙️ Paramètres & Configuration

### Comment personnaliser mon dashboard ?
1. Cliquez l'icône ⚙️ sur le dashboard
2. Ou allez dans **Auth** → **Dashboard** → **Configurer**
3. Ajoutez/supprimez des widgets
4. Déplacez-les par drag & drop
5. Sauvegardez

### Comment changer mon mot de passe ?
1. Cliquez votre nom → **Mon profil**
2. Onglet **Sécurité**
3. Saisissez l'ancien et le nouveau mot de passe
4. Cliquez **Changer le mot de passe**

### Comment gérer mes sessions actives ?
1. **Mon profil** → Onglet **Sessions**
2. Voyez tous les appareils connectés
3. Cliquez **Révoquer** pour déconnecter un appareil

### Comment changer la langue de l'interface ?
1. **Mon profil** → Onglet **Profil**
2. Changez le champ **Langue**
3. Enregistrez

### Comment gérer plusieurs domaines ?
1. **Auth** → **Mes organisations**
2. Créez une nouvelle organisation ou rejoignez une existante
3. Basculez entre organisations via le sélecteur en haut

---

## 🔧 Problèmes Courants

### Je n'arrive pas à me connecter
- Vérifiez que votre email est correct
- Utilisez "Mot de passe oublié" si besoin
- Vérifiez que votre compte n'est pas suspendu
- Contactez l'admin de votre organisation si le problème persiste

### Je ne vois pas certains menus
- Votre rôle peut limiter l'accès à certaines fonctionnalités
- Contactez un Admin pour modifier vos permissions
- Certains modules peuvent être désactivés pour votre organisation

### Mes données ne s'affichent pas
- Vérifiez que vous êtes dans la bonne organisation
- Rafraîchissez la page (F5 ou Ctrl+R)
- Videz le cache du navigateur si le problème persiste
- Vérifiez vos filtres (ils peuvent cacher des données)

### L'export ne fonctionne pas
- Vérifiez que vous avez les droits d'export
- Essayez avec moins de données (filtrez d'abord)
- Le fichier peut être volumineux, patientez
- Essayez un autre navigateur

### Les alertes ne s'affichent pas
- Vérifiez les seuils configurés dans **Stocks** → **Seuils**
- Vérifiez que vous n'avez pas acquitté les alertes
- Les alertes peuvent avoir été ignorées par un autre utilisateur

---

## 📱 Application Mobile

### MonChai fonctionne-t-il sur mobile ?
Oui, l'interface est responsive et s'adapte aux smartphones. L'interface terrain (vendanges) est spécialement optimisée pour la saisie mobile.

### Puis-je travailler hors connexion ?
Le mode hors-ligne est en préparation. Actuellement, une connexion internet est requise.

### Comment utiliser les boutons de poids rapides ?
Sur l'écran de saisie vendange mobile, utilisez les boutons +100, +250, +500 kg pour ajouter rapidement du poids sans taper au clavier.

---

## 🔐 Sécurité

### Mes données sont-elles sécurisées ?
- Toutes les connexions sont chiffrées (HTTPS)
- Les mots de passe sont hashés
- Les sessions sont protégées
- L'audit trail trace toutes les actions

### Comment activer l'authentification à deux facteurs ?
L'activation du MFA (Multi-Factor Authentication) est disponible dans **Mon profil** → **Sécurité**. Cette fonctionnalité est en cours de déploiement.

### Qui peut voir mes données ?
Seuls les membres de votre organisation avec les permissions appropriées peuvent accéder à vos données. L'isolation entre organisations est stricte.

---

## 📞 Support

### Comment contacter le support ?
- Email : support@monchai.fr
- Documentation : `/docs/`
- FAQ : Cette page

### Comment signaler un bug ?
1. Notez les étapes pour reproduire le problème
2. Faites une capture d'écran si possible
3. Envoyez à support@monchai.fr avec :
   - Description du problème
   - Navigateur et version
   - Étapes de reproduction
   - Capture d'écran

### Comment suggérer une fonctionnalité ?
Envoyez vos suggestions à feedback@monchai.fr avec :
- Description de la fonctionnalité souhaitée
- Cas d'usage concret
- Priorité selon vous

---

*FAQ MonChai v2.0 - Une question non répondue ? Contactez support@monchai.fr*

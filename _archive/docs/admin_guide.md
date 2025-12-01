# Guide Administrateur - Mon Chai V1

## Date : 2025-09-24

## 👋 Bienvenue dans Mon Chai V1

Ce guide vous accompagne dans l'administration de votre organisation sur Mon Chai V1. Vous apprendrez à gérer les utilisateurs, configurer les permissions et maintenir la sécurité de votre système.

---

## 🎯 Rôles et Responsabilités

### Votre Rôle d'Administrateur Organisation

En tant qu'**AdminOrganisation**, vous avez la responsabilité de :
- ✅ Gérer les utilisateurs de votre organisation
- ✅ Configurer les rôles et permissions
- ✅ Superviser l'activité et la sécurité
- ✅ Paramétrer l'organisation (facturation, formats, etc.)
- ❌ Vous n'avez PAS accès aux données techniques Django (`/admin/`)

### Accès au Backoffice

Votre interface d'administration se trouve à l'adresse :
**`/backoffice/`**

Vous y trouverez :
- 📊 **Dashboard** - Vue d'ensemble de votre organisation
- 👥 **Utilisateurs** - Gestion des membres et invitations
- ⚙️ **Paramètres** - Configuration de l'organisation
- 📈 **Monitoring** - Surveillance de l'activité

---

## 👥 Gestion des Utilisateurs

### 1. Inviter un Nouvel Utilisateur

#### Étapes d'Invitation
1. Accédez à **Backoffice → Utilisateurs**
2. Cliquez sur **"Inviter un utilisateur"**
3. Remplissez le formulaire :
   - **Email** : Adresse email professionnelle
   - **Rôle** : Choisissez selon les responsabilités
   - **Message** : Personnalisez l'invitation (optionnel)
4. Cliquez sur **"Envoyer l'invitation"**

#### Choix du Rôle Initial
```
🏆 AdminOrganisation : Autre administrateur (prudence !)
👨‍💼 Manager : Chef de cave, responsable production
💰 Comptabilité : Responsable financier
🍷 Opérateur : Caviste, personnel de production
👁️ LectureSeule : Consultant, stagiaire, auditeur
🤝 Partenaire : Distributeur, client professionnel
```

**💡 Conseil** : Commencez toujours par **LectureSeule** puis élargissez les permissions progressivement.

### 2. Gérer les Rôles Existants

#### Modifier un Rôle
1. Dans **Utilisateurs**, cliquez sur le nom de l'utilisateur
2. Section **"Rôle et Permissions"**
3. Sélectionnez le nouveau rôle
4. **Sauvegardez** les modifications

#### Désactiver un Utilisateur
1. Accédez au profil utilisateur
2. Décochez **"Utilisateur actif"**
3. L'utilisateur ne pourra plus se connecter
4. Ses données restent préservées

### 3. Gestion des Scopes (Permissions Avancées)

#### Qu'est-ce qu'un Scope ?
Les **scopes** définissent précisément quelles données un utilisateur peut consulter ou modifier :

```
📦 catalogue:read    → Voir les produits
📦 catalogue:write   → Créer/modifier les produits
👥 clients:read      → Voir les clients
👥 clients:write     → Gérer les clients
💰 ventes:financial  → Accès aux données financières
📊 stocks:manage     → Gérer les seuils et alertes
```

#### Attribution des Scopes
1. Profil utilisateur → **"Scopes Détaillés"**
2. Cochez les permissions nécessaires par domaine
3. **Règle d'or** : Le minimum nécessaire pour le travail

#### Exemples de Configurations

**Caviste (Opérateur)** :
- ✅ `catalogue:read` - Voir les produits
- ✅ `stocks:read` - Consulter les stocks
- ✅ `stocks:write` - Saisir les mouvements
- ❌ `ventes:financial` - Pas d'accès aux prix

**Comptable** :
- ✅ `clients:read` - Voir les clients
- ✅ `ventes:read` - Consulter les ventes
- ✅ `ventes:financial` - Accès complet financier
- ❌ `catalogue:write` - Pas de modification produits

---

## ⚙️ Configuration de l'Organisation

### 1. Paramètres Généraux

#### Accès aux Paramètres
**Backoffice → Paramètres → Généraux**

#### Devise et Formats
- **Devise** : EUR, USD, GBP, CHF
- **Format de date** : DD/MM/YYYY (français), MM/DD/YYYY (US), YYYY-MM-DD (ISO)
- **Format des nombres** : 1 234,56 (français) ou 1,234.56 (anglais)

**💡 Aperçu en temps réel** : Les changements sont prévisualisés instantanément.

#### Conditions Générales de Vente
Deux options :
- **URL externe** : Lien vers vos CGV hébergées ailleurs
- **Fichier PDF** : Upload direct (max 5 Mo)

### 2. Paramètres de Facturation

#### Informations Légales
**Backoffice → Paramètres → Facturation**

Renseignez obligatoirement :
- **Raison sociale** : Nom légal de votre entreprise
- **Adresse de facturation** : Adresse complète
- **SIRET** : 14 chiffres (optionnel mais recommandé)
- **Statut TVA** : Assujetti ou non assujetti
- **Numéro de TVA** : Si assujetti (format FR + 11 chiffres)

#### Contact Facturation (Optionnel)
- **Nom du contact**
- **Email de facturation**
- **Téléphone**

### 3. Checklist d'Onboarding

#### Suivi de Configuration
**Backoffice → Onboarding**

La checklist vous guide pour :
- ✅ **Informations exploitation** : Nom, adresse fiscale
- ✅ **TVA et taxes** : Configuration fiscale
- ✅ **Devise et formats** : Paramètres régionaux
- ✅ **Conditions générales** : CGV configurées

**🎯 Objectif** : 100% de completion pour une configuration optimale.

---

## 🔐 Sécurité et Bonnes Pratiques

### 1. Principe du Moindre Privilège

#### Règles d'Or
- **Commencez restrictif** : Rôle LectureSeule puis élargissez
- **Révisez régulièrement** : Vérifiez les permissions trimestriellement
- **Documentez les changements** : Notez pourquoi vous accordez des permissions
- **Supprimez l'inutile** : Retirez les accès non utilisés

#### Matrice de Permissions Recommandée
```
Nouveau collaborateur     → LectureSeule (1 semaine d'observation)
Caviste confirmé         → Opérateur + stocks:write
Responsable commercial   → Manager + clients:write + ventes:read
Comptable externe        → Comptabilité + ventes:financial uniquement
Consultant temporaire    → LectureSeule + date d'expiration
```

### 2. Gestion des Départs

#### Procédure de Départ (Offboarding)
1. **Immédiatement** : Désactiver le compte utilisateur
2. **Transférer** : Réassigner les responsabilités critiques
3. **Archiver** : Conserver les données pour audit (6 mois minimum)
4. **Documenter** : Noter la date et raison du départ

#### Checklist de Départ
- [ ] Compte utilisateur désactivé
- [ ] Accès révoqués dans tous les systèmes
- [ ] Données transférées au remplaçant
- [ ] Matériel récupéré (si applicable)
- [ ] Documentation mise à jour

### 3. Surveillance de l'Activité

#### Monitoring Quotidien
**Backoffice → Monitoring**

Surveillez :
- **Connexions inhabituelles** : Heures, lieux, fréquence
- **Erreurs d'accès** : Tentatives de connexion échouées
- **Activité suspecte** : Trop de requêtes, changements d'organisation fréquents
- **Performance** : Lenteurs, erreurs système

#### Alertes Automatiques
Le système vous alertera automatiquement en cas de :
- 🚨 **Tentatives de connexion multiples échouées**
- 🚨 **Accès depuis un nouveau pays/IP**
- 🚨 **Modification de données sensibles**
- 🚨 **Erreurs système répétées**

---

## 📊 Tableaux de Bord et Reporting

### 1. Dashboard Principal

#### Métriques Clés
Votre dashboard affiche :
- **Utilisateurs actifs** : Nombre de membres connectés
- **Invitations en attente** : À relancer si nécessaire
- **Activité récente** : Dernières actions importantes
- **Santé du système** : Performance et erreurs

#### Actions Rapides
Boutons d'accès direct :
- 👥 **Gérer les utilisateurs**
- ⚙️ **Configurer l'organisation**
- 📊 **Voir le monitoring**
- 📋 **Compléter l'onboarding**

### 2. Rapports d'Activité

#### Rapport Mensuel Utilisateurs
- Connexions par utilisateur
- Actions réalisées par domaine
- Temps passé dans l'application
- Fonctionnalités les plus utilisées

#### Rapport de Sécurité
- Tentatives de connexion échouées
- Changements de permissions
- Accès aux données sensibles
- Anomalies détectées

---

## 🆘 Résolution de Problèmes

### 1. Problèmes Courants

#### "L'utilisateur ne peut pas se connecter"
1. Vérifiez que le compte est **actif**
2. Confirmez que l'**invitation a été acceptée**
3. Vérifiez l'**adresse email** (pas de faute de frappe)
4. Demandez à l'utilisateur de vérifier ses **spams**

#### "L'utilisateur ne voit pas certaines données"
1. Vérifiez son **rôle** (suffisant pour l'action ?)
2. Contrôlez ses **scopes** (permissions détaillées)
3. Confirmez qu'il est dans la **bonne organisation**
4. Vérifiez les **filtres** appliqués dans l'interface

#### "Erreur de permissions"
1. L'utilisateur a-t-il le **scope requis** ?
2. Essaie-t-il d'accéder aux données d'une **autre organisation** ?
3. Son **rôle** permet-il cette action ?
4. Y a-t-il une **restriction temporaire** ?

### 2. Escalade vers le Support

#### Quand Contacter le Support Technique
- Erreurs système persistantes
- Problèmes de performance généralisés
- Suspicion de faille de sécurité
- Perte de données

#### Informations à Fournir
- **URL exacte** où le problème survient
- **Message d'erreur** complet
- **Étapes pour reproduire** le problème
- **Utilisateur concerné** et son rôle
- **Heure approximative** du problème

---

## 📚 Ressources et Formation

### 1. Formation des Utilisateurs

#### Parcours de Formation Recommandé
1. **Semaine 1** : Découverte avec rôle LectureSeule
2. **Semaine 2** : Formation sur les fonctionnalités métier
3. **Semaine 3** : Attribution des permissions de travail
4. **Mois 1** : Suivi et ajustements

#### Ressources de Formation
- **Guide utilisateur** : Documentation complète par rôle
- **Vidéos tutoriels** : Démonstrations des fonctionnalités
- **Sessions de formation** : Formations collectives sur demande
- **Support utilisateur** : Aide en ligne et chat

### 2. Veille Sécurité

#### Bonnes Pratiques à Maintenir
- **Mots de passe forts** : Minimum 12 caractères, complexes
- **Authentification à deux facteurs** : Recommandée pour les admins
- **Mise à jour régulière** : Suivre les mises à jour système
- **Sauvegarde** : Vérifier les sauvegardes automatiques

#### Signalement d'Incidents
En cas de suspicion de sécurité :
1. **Ne pas ignorer** les alertes système
2. **Documenter** l'incident (captures d'écran, logs)
3. **Contacter immédiatement** le support technique
4. **Informer** les utilisateurs concernés si nécessaire

---

## 📞 Support et Contacts

### Support Technique
- **Email** : support@monchai.fr
- **Téléphone** : +33 1 XX XX XX XX
- **Horaires** : Lundi-Vendredi 9h-18h
- **Urgences** : 24h/7j pour les incidents critiques

### Documentation
- **Guide utilisateur** : `/docs/user-guide/`
- **FAQ** : `/docs/faq/`
- **Changelog** : `/docs/changelog/`
- **API Documentation** : `/docs/api/`

---

**Vous êtes maintenant prêt à administrer efficacement votre organisation Mon Chai V1 !**

*Ce guide est mis à jour régulièrement. Consultez la version en ligne pour les dernières informations.*

# Politique de Sécurité - Mon Chai V1

## Date : 2025-09-24

## 🛡️ Principes Fondamentaux

### Notre Engagement Sécurité

Mon Chai V1 applique une politique de sécurité stricte basée sur :
- **Deny by Default** : Aucun accès sans autorisation explicite
- **Principe du Moindre Privilège** : Permissions minimales nécessaires
- **Défense en Profondeur** : Multiples couches de protection
- **Audit Complet** : Traçabilité de toutes les actions sensibles

### Responsabilités Partagées

| Responsabilité | Mon Chai (Éditeur) | Organisation (Client) |
|----------------|--------------------|-----------------------|
| **Infrastructure** | ✅ Sécurité serveurs, réseau | ❌ |
| **Application** | ✅ Code, mises à jour sécurité | ❌ |
| **Données** | ✅ Chiffrement, sauvegarde | ✅ Classification, accès |
| **Utilisateurs** | ✅ Authentification, autorisation | ✅ Gestion des comptes |
| **Conformité** | ✅ RGPD technique | ✅ RGPD organisationnel |

---

## 🔐 Authentification et Accès

### 1. Politique des Mots de Passe

#### Exigences Minimales
- **Longueur** : 12 caractères minimum
- **Complexité** : Majuscules, minuscules, chiffres, caractères spéciaux
- **Unicité** : Différent des 5 derniers mots de passe
- **Expiration** : Recommandée tous les 90 jours pour les admins

#### Mots de Passe Interdits
- ❌ Mots du dictionnaire
- ❌ Informations personnelles (nom, date de naissance)
- ❌ Mots de passe communs (password123, azerty)
- ❌ Répétition de caractères (aaaa, 1111)

### 2. Authentification Multi-Facteurs (2FA)

#### Obligatoire pour :
- ✅ **SuperAdmin** (équipe technique)
- ✅ **AdminOrganisation** (propriétaires)
- ✅ Accès aux données financières
- ✅ Accès depuis l'extérieur du réseau d'entreprise

#### Méthodes Supportées
1. **Application mobile** (Google Authenticator, Authy)
2. **SMS** (fallback uniquement)
3. **Codes de récupération** (usage unique)

### 3. Gestion des Sessions

#### Paramètres de Session
- **Durée** : 8 heures d'activité
- **Inactivité** : Déconnexion après 30 minutes
- **Concurrent** : 3 sessions maximum par utilisateur
- **Géolocalisation** : Alerte si connexion depuis nouveau pays

#### Révocation de Session
- Automatique lors du changement de mot de passe
- Manuelle via "Déconnecter tous les appareils"
- Automatique en cas d'activité suspecte

---

## 👥 Gestion des Utilisateurs

### 1. Cycle de Vie des Comptes

#### Création de Compte
1. **Invitation uniquement** par un AdminOrganisation
2. **Validation email** obligatoire
3. **Rôle initial** : LectureSeule par défaut
4. **Formation** : Accès aux ressources de sécurité

#### Modification de Permissions
- **Principe d'élévation graduelle** : Commencer restrictif
- **Validation** : Justification écrite pour permissions sensibles
- **Approbation** : Double validation pour rôles AdminOrganisation
- **Audit** : Traçabilité complète des changements

#### Désactivation de Compte
- **Immédiate** en cas de départ ou incident
- **Préservation** des données pour audit (6 mois)
- **Transfert** des responsabilités avant désactivation
- **Notification** automatique aux autres administrateurs

### 2. Matrice des Rôles et Permissions

#### Rôles Standards
```
🔴 SuperAdmin      → Accès technique complet (équipe Mon Chai)
🟠 AdminOrganisation → Gestion complète de l'organisation
🟡 Manager         → Gestion opérationnelle quotidienne
🔵 Comptabilité    → Accès financier et comptable
🟢 Opérateur       → Saisie et consultation limitée
🟣 Partenaire      → Accès externe restreint
⚪ LectureSeule    → Consultation uniquement
```

#### Permissions par Domaine
| Domaine | SuperAdmin | AdminOrg | Manager | Comptabilité | Opérateur | Partenaire | LectureSeule |
|---------|------------|----------|---------|--------------|-----------|------------|--------------|
| **Utilisateurs** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Paramètres Org** | ✅ | ✅ | ❌ | 🔸 Facturation | ❌ | ❌ | ❌ |
| **Données Financières** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | 🔸 Lecture |
| **Catalogue** | ✅ | ✅ | ✅ | 🔸 Lecture | 🔸 Lecture | 🔸 Public | 🔸 Lecture |
| **Clients** | ✅ | ✅ | ✅ | ✅ | ❌ | 🔸 Ses données | 🔸 Lecture |
| **Stocks** | ✅ | ✅ | ✅ | 🔸 Lecture | ✅ | ❌ | 🔸 Lecture |

### 3. Scopes Granulaires

#### Définition des Scopes
Les scopes permettent un contrôle fin des permissions :
- `domaine:read` - Consultation des données
- `domaine:write` - Création et modification
- `domaine:delete` - Suppression (rare)
- `domaine:export` - Export de données
- `domaine:admin` - Administration complète

#### Attribution des Scopes
- **Par défaut** : Scopes minimaux selon le rôle
- **Sur demande** : Justification et approbation requises
- **Temporaire** : Possibilité d'attribution avec expiration
- **Révision** : Contrôle trimestriel des scopes accordés

---

## 🏢 Isolation Multi-Tenant

### 1. Séparation des Données

#### Principe d'Isolation
- **Étanche** : Aucune fuite de données entre organisations
- **Automatique** : Filtrage transparent par middleware
- **Vérifiée** : Tests automatisés de non-régression
- **Auditée** : Logs de tous les accès cross-organisation

#### Mécanismes Techniques
- **RLS (Row Level Security)** : Filtrage au niveau base de données
- **Middleware** : Vérification à chaque requête
- **Décorateurs** : Validation sur chaque vue sensible
- **Tests** : Validation automatique de l'isolation

### 2. Gestion Multi-Organisation

#### Utilisateurs Multi-Organisations
Certains utilisateurs (consultants, auditeurs) peuvent avoir accès à plusieurs organisations :
- **Changement explicite** : Sélection manuelle de l'organisation active
- **Session isolée** : Données filtrées selon l'organisation courante
- **Audit renforcé** : Logs détaillés des changements d'organisation
- **Restrictions** : Limitations sur les actions cross-organisation

#### Contrôles de Sécurité
- **Validation** : Vérification de l'appartenance à l'organisation
- **Logs** : Traçabilité complète des accès
- **Alertes** : Notification en cas d'activité suspecte
- **Révocation** : Possibilité de retirer l'accès immédiatement

---

## 📊 Audit et Monitoring

### 1. Journalisation de Sécurité

#### Événements Loggés
- **Authentification** : Connexions, échecs, déconnexions
- **Autorisation** : Accès accordés, refusés, changements de permissions
- **Données** : Accès, modifications, suppressions de données sensibles
- **Administration** : Changements de configuration, gestion utilisateurs

#### Format des Logs
```json
{
  "timestamp": "2025-09-24T22:30:00Z",
  "event_type": "DATA_ACCESS",
  "user_id": "uuid",
  "organization_id": "uuid",
  "resource_type": "customer",
  "resource_id": "uuid",
  "action": "read",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "success": true
}
```

#### Rétention des Logs
- **Logs de sécurité** : 2 ans minimum
- **Logs d'audit** : 7 ans (conformité comptable)
- **Logs techniques** : 6 mois
- **Sauvegarde** : Stockage sécurisé hors site

### 2. Détection d'Anomalies

#### Alertes Automatiques
- **Connexions multiples échouées** : > 5 tentatives en 5 minutes
- **Accès géographique inhabituel** : Nouveau pays/région
- **Volume d'activité anormal** : > 100 requêtes/minute
- **Accès hors horaires** : Connexions en dehors des heures de travail
- **Changements de permissions** : Élévation de privilèges

#### Réponse aux Incidents
1. **Détection automatique** : Système d'alertes en temps réel
2. **Investigation** : Analyse des logs et du contexte
3. **Containment** : Limitation des dégâts potentiels
4. **Éradication** : Suppression de la menace
5. **Récupération** : Restauration du service normal
6. **Leçons apprises** : Amélioration des processus

---

## 🔒 Protection des Données

### 1. Classification des Données

#### Niveaux de Classification
- **🔴 Critique** : Données financières, mots de passe, clés API
- **🟠 Sensible** : Informations clients, données personnelles
- **🟡 Interne** : Données métier, configurations
- **🟢 Public** : Informations générales, documentation

#### Mesures de Protection par Niveau
| Niveau | Chiffrement | Accès | Sauvegarde | Rétention |
|--------|-------------|-------|------------|-----------|
| **Critique** | AES-256 | 2FA obligatoire | Quotidienne | 7 ans |
| **Sensible** | AES-256 | Rôles restreints | Quotidienne | 5 ans |
| **Interne** | TLS | Authentification | Hebdomadaire | 3 ans |
| **Public** | TLS | Libre | Mensuelle | 1 an |

### 2. Chiffrement

#### Chiffrement en Transit
- **TLS 1.3** : Toutes les communications HTTPS
- **Certificate Pinning** : Protection contre les attaques MITM
- **HSTS** : Forcer les connexions sécurisées
- **Perfect Forward Secrecy** : Clés de session éphémères

#### Chiffrement au Repos
- **Base de données** : Chiffrement AES-256 des colonnes sensibles
- **Fichiers** : Chiffrement des uploads utilisateurs
- **Sauvegardes** : Chiffrement complet des backups
- **Logs** : Chiffrement des logs de sécurité

### 3. Gestion des Clés

#### Hiérarchie des Clés
- **Master Key** : Stockée dans un HSM (Hardware Security Module)
- **Data Encryption Keys** : Générées et chiffrées par la Master Key
- **Rotation** : Rotation automatique tous les 90 jours
- **Révocation** : Possibilité de révoquer immédiatement

---

## 🌐 Sécurité Réseau

### 1. Architecture Réseau

#### Segmentation
- **DMZ** : Serveurs web exposés
- **Zone Application** : Serveurs applicatifs
- **Zone Base de Données** : Serveurs de données
- **Zone Administration** : Outils de gestion

#### Contrôles d'Accès
- **Firewall** : Filtrage par IP, port, protocole
- **WAF** : Protection contre les attaques web
- **IDS/IPS** : Détection et prévention d'intrusions
- **VPN** : Accès sécurisé pour l'administration

### 2. Protection contre les Attaques

#### Attaques Web
- **SQL Injection** : Requêtes paramétrées, ORM
- **XSS** : Échappement automatique, CSP
- **CSRF** : Tokens CSRF sur tous les formulaires
- **Clickjacking** : Headers X-Frame-Options

#### Attaques DDoS
- **Rate Limiting** : Limitation du nombre de requêtes
- **CDN** : Distribution de charge géographique
- **Auto-scaling** : Adaptation automatique de la capacité
- **Blacklisting** : Blocage automatique des IP malveillantes

---

## 📋 Conformité et Réglementation

### 1. RGPD (Règlement Général sur la Protection des Données)

#### Droits des Personnes
- **Droit d'accès** : Export des données personnelles
- **Droit de rectification** : Correction des données inexactes
- **Droit à l'effacement** : Suppression des données sur demande
- **Droit à la portabilité** : Export dans un format standard

#### Mesures Techniques
- **Privacy by Design** : Protection dès la conception
- **Minimisation** : Collecte des données strictement nécessaires
- **Pseudonymisation** : Remplacement des identifiants directs
- **Chiffrement** : Protection des données sensibles

### 2. Sécurité Comptable

#### Traçabilité Comptable
- **Immutabilité** : Les écritures ne peuvent être modifiées
- **Chronologie** : Horodatage précis de toutes les opérations
- **Intégrité** : Vérification de la cohérence des données
- **Archivage** : Conservation légale des documents

#### Contrôles d'Accès Financiers
- **Séparation des tâches** : Saisie ≠ Validation ≠ Paiement
- **Double validation** : Approbation pour montants élevés
- **Audit trail** : Traçabilité complète des modifications
- **Réconciliation** : Contrôles automatiques de cohérence

---

## 🚨 Gestion des Incidents

### 1. Classification des Incidents

#### Niveaux de Criticité
- **🔴 Critique** : Compromission de données, service indisponible
- **🟠 Majeur** : Fonctionnalité importante indisponible
- **🟡 Mineur** : Problème localisé, contournement possible
- **🟢 Cosmétique** : Problème d'affichage, pas d'impact métier

#### Temps de Réponse
| Criticité | Première Réponse | Résolution |
|-----------|------------------|------------|
| **Critique** | 15 minutes | 4 heures |
| **Majeur** | 1 heure | 24 heures |
| **Mineur** | 4 heures | 72 heures |
| **Cosmétique** | 24 heures | 1 semaine |

### 2. Procédure de Réponse

#### Étapes de Gestion
1. **Détection** : Alertes automatiques ou signalement
2. **Évaluation** : Classification et impact
3. **Escalade** : Notification des équipes concernées
4. **Investigation** : Analyse des causes racines
5. **Containment** : Limitation de l'impact
6. **Résolution** : Correction du problème
7. **Communication** : Information des utilisateurs
8. **Post-mortem** : Analyse et amélioration

#### Communication de Crise
- **Page de statut** : Mise à jour en temps réel
- **Email** : Notification aux administrateurs
- **In-app** : Messages dans l'application
- **Support** : Renforcement de l'équipe support

---

## 📞 Contacts et Escalade

### Équipe Sécurité
- **CISO** : ciso@monchai.fr
- **Équipe Sécurité** : security@monchai.fr
- **Incidents** : incidents@monchai.fr (24h/7j)

### Signalement de Vulnérabilités
- **Bug Bounty** : security-bounty@monchai.fr
- **Divulgation responsable** : 90 jours pour correction
- **Récompenses** : Programme de récompenses selon criticité

### Support Utilisateurs
- **Support général** : support@monchai.fr
- **Urgences sécurité** : +33 1 XX XX XX XX (24h/7j)
- **Documentation** : https://docs.monchai.fr/security

---

## 📚 Formation et Sensibilisation

### Formation Obligatoire
- **Nouveaux utilisateurs** : Formation sécurité de base
- **Administrateurs** : Formation avancée sur la gestion des risques
- **Mise à jour annuelle** : Évolution des menaces et bonnes pratiques

### Ressources Disponibles
- **Guide de sécurité** : Bonnes pratiques par rôle
- **Vidéos de formation** : Modules interactifs
- **Tests de phishing** : Simulations d'attaques
- **Veille sécurité** : Newsletter mensuelle

---

**Cette politique de sécurité est revue et mise à jour trimestriellement.**

*Version 1.0 - Effective au 24 septembre 2025*

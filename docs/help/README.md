# 📚 Documentation d'Aide MonChai

> **Version:** 2.0  
> **Application:** MonChai - Gestion Viticole SaaS  
> **Dernière mise à jour:** Décembre 2024

---

## 📂 Structure de la Documentation

```
docs/help/
├── README.md                    # Ce fichier - Index de la documentation
├── URL_REFERENCE.md             # Référence complète de toutes les URLs
├── FEATURES_GUIDE.md            # Guide des fonctionnalités par module
├── USER_GUIDE.md                # Guide utilisateur pas à pas
├── API_REFERENCE.md             # Documentation de l'API REST
├── CONTEXTUAL_HELP_INDEX.json   # Index JSON pour l'aide contextuelle
├── GLOSSARY.md                  # Glossaire des termes viticoles et techniques
├── FAQ.md                       # Questions fréquemment posées
├── SHORTCUTS.md                 # Raccourcis clavier
└── TROUBLESHOOTING.md           # Résolution des problèmes courants
```

---

## 🎯 Utilisation de cette Documentation

### Pour les Utilisateurs

| Document | Quand l'utiliser |
|----------|------------------|
| **USER_GUIDE.md** | Guide pas à pas pour démarrer et utiliser MonChai |
| **FAQ.md** | Réponses rapides aux questions courantes |
| **GLOSSARY.md** | Comprendre les termes viticoles et techniques |
| **SHORTCUTS.md** | Maîtriser les raccourcis clavier |

### Pour les Développeurs

| Document | Quand l'utiliser |
|----------|------------------|
| **URL_REFERENCE.md** | Trouver n'importe quelle URL de l'application |
| **API_REFERENCE.md** | Intégrer avec l'API REST |
| **FEATURES_GUIDE.md** | Comprendre l'architecture fonctionnelle |
| **CONTEXTUAL_HELP_INDEX.json** | Intégrer l'aide contextuelle |

### Pour le Support

| Document | Quand l'utiliser |
|----------|------------------|
| **TROUBLESHOOTING.md** | Diagnostiquer et résoudre les problèmes |
| **FAQ.md** | Répondre aux questions utilisateurs |
| **FEATURES_GUIDE.md** | Expliquer les fonctionnalités |

---

## 📖 Résumé des Documents

### 📍 URL_REFERENCE.md
**Référence exhaustive de toutes les URLs de MonChai**
- Navigation principale
- Module Authentification (/auth/)
- Module Production (/production/)
- Module Clients (/referentiels/clients/)
- Module Commerce (/achats/, /ventes/)
- Module DRM (/drm/)
- Module Stocks (/stocks/)
- API endpoints (/api/)
- Redirections et compatibilité

### 📖 FEATURES_GUIDE.md
**Guide complet des fonctionnalités par module**
- Architecture fonctionnelle
- Module Authentification & Organisation
- Module Production (Vigne, Chai, Élevage)
- Module Inventaire
- Module Clients (CRM)
- Module Commerce
- Module DRM
- Module Référentiels
- Module IA (Smart Suggestions)

### 📚 USER_GUIDE.md
**Guide utilisateur détaillé avec pas à pas**
- Premiers pas (inscription, configuration)
- Gestion des parcelles et encépagement
- Journal cultural et registre phyto
- Vendanges et encuvage
- Gestion des cuves et soutirages
- Analyses œnologiques
- Assemblages et mises en bouteille
- Gestion des clients
- Cycle de vente complet
- Préparation DRM
- Alertes et rappels
- Paramètres utilisateur

### 🔌 API_REFERENCE.md
**Documentation technique de l'API REST**
- Authentification (session, token)
- API Organisation et Utilisateurs
- API Aide IA et Smart Suggestions
- API Clients
- API Catalogue et Stocks
- API DRM
- Webhooks
- Codes d'erreur et rate limiting
- Exemples cURL, JavaScript, Python

### 📋 CONTEXTUAL_HELP_INDEX.json
**Index structuré pour l'aide contextuelle**
- Mapping URL → contenu d'aide
- Descriptions et tips par page
- Raccourcis par contexte
- Glossaire intégré
- FAQ rapide

### 📖 GLOSSARY.md
**Glossaire complet des termes**
- Termes viticoles (vigne, cépages, travaux)
- Termes de vinification
- Termes d'élevage
- Termes de conditionnement
- Termes réglementaires (DRM, CRD)
- Termes commerciaux
- Termes techniques MonChai
- Unités de mesure

### ❓ FAQ.md
**Questions fréquemment posées**
- Démarrage et inscription
- Production (parcelles, vendanges, chai)
- Conditionnement
- Clients et ventes
- DRM et réglementation
- Stocks et inventaire
- Paramètres et configuration
- Problèmes courants
- Application mobile
- Sécurité
- Support

### ⌨️ SHORTCUTS.md
**Raccourcis clavier complets**
- Raccourcis globaux
- Navigation formulaires
- Navigation listes
- Recherche
- Tableaux et grilles
- Modals et panneaux
- Sélecteurs de date
- Raccourcis par module

---

## 🔄 Maintenance de la Documentation

### Mise à jour
La documentation doit être mise à jour à chaque :
- Ajout de nouvelle fonctionnalité
- Modification d'URL
- Changement d'interface utilisateur
- Ajout d'endpoint API

### Format
- Markdown pour tous les fichiers texte
- JSON pour les données structurées
- UTF-8 avec BOM pour compatibilité Windows

### Conventions
- Titres en français
- Code en anglais
- URLs en minuscules avec tirets
- Emojis pour les titres de section

---

## 🤖 Intégration avec le Module d'Aide

### Aide Contextuelle
Le fichier `CONTEXTUAL_HELP_INDEX.json` est utilisé par le système d'aide pour :
1. Afficher l'aide appropriée selon la page courante
2. Proposer des suggestions contextuelles
3. Répondre aux requêtes de recherche

### API d'Aide
L'endpoint `/api/help/query` utilise cette documentation pour :
1. Trouver les réponses pertinentes
2. Suggérer des articles connexes
3. Proposer des actions rapides

### Recherche
La recherche globale (`Ctrl+K`) indexe cette documentation pour permettre de trouver rapidement :
- Pages et fonctionnalités
- Termes du glossaire
- Questions de la FAQ
- Raccourcis clavier

---

## 📞 Contact

- **Support utilisateur:** support@monchai.fr
- **Documentation technique:** docs@monchai.fr
- **Signalement de bugs:** bugs@monchai.fr
- **Suggestions:** feedback@monchai.fr

---

*Documentation MonChai v2.0 - Module d'aide ULTRA performant*

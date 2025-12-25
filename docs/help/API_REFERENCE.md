# 🔌 Référence API MonChai

> **Version:** 2.0  
> **Base URL:** `https://votre-domaine.monchai.fr`  
> **Authentification:** Bearer Token ou Session Cookie

---

## 🔐 Authentification

### Obtenir un Token CSRF

```http
GET /api/auth/csrf/
```

**Réponse:**
```json
{
  "csrfToken": "abc123xyz..."
}
```

### Connexion (Session)

```http
POST /api/auth/session/
Content-Type: application/json
X-CSRFToken: {csrf_token}

{
  "email": "user@example.com",
  "password": "monmotdepasse"
}
```

**Réponse succès:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Jean Dupont"
  },
  "organization": {
    "id": 1,
    "name": "Domaine des Vignes"
  }
}
```

**Réponse erreur:**
```json
{
  "success": false,
  "error": "invalid_credentials",
  "message": "Email ou mot de passe incorrect"
}
```

### Qui suis-je ?

```http
GET /api/auth/whoami/
Cookie: sessionid=xxx
```

**Réponse:**
```json
{
  "authenticated": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Jean Dupont",
    "role": "admin"
  },
  "organization": {
    "id": 1,
    "name": "Domaine des Vignes",
    "plan": "pro"
  }
}
```

### Déconnexion

```http
POST /api/auth/logout/
Cookie: sessionid=xxx
X-CSRFToken: {csrf_token}
```

**Réponse:**
```json
{
  "success": true,
  "message": "Déconnecté avec succès"
}
```

---

## 🔑 API Tokens (Bearer)

### Créer un Token API

Via l'interface : `/auth/tokens/create/`

### Utiliser un Token

```http
GET /api/v1/organization/
Authorization: Bearer mch_xxxxxxxxxxxx
```

### Scopes Disponibles

| Scope | Description |
|-------|-------------|
| `read` | Lecture seule |
| `write` | Lecture et écriture |
| `delete` | Suppression autorisée |
| `customers` | Accès clients |
| `orders` | Accès commandes |
| `products` | Accès produits |
| `analytics` | Accès statistiques |
| `webhooks` | Gestion webhooks |
| `all` | Accès complet |

---

## 📊 API v1 - Organisation

### Informations Organisation

```http
GET /api/v1/organization/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "id": 1,
  "name": "Domaine des Vignes",
  "display_name": "Domaine des Vignes d'Or",
  "type": "winery",
  "plan": "pro",
  "created_at": "2024-01-15T10:30:00Z",
  "settings": {
    "currency": "EUR",
    "timezone": "Europe/Paris",
    "language": "fr"
  }
}
```

### Liste des Utilisateurs

```http
GET /api/v1/users/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "email": "admin@domaine.fr",
      "name": "Jean Dupont",
      "role": "owner",
      "status": "active",
      "last_login": "2024-12-20T14:30:00Z"
    }
  ]
}
```

---

## 🤖 API Aide IA

### Assistant d'Aide

```http
GET /api/help/
```

**Réponse:** Page HTML de l'assistant

### Requête d'Aide

```http
POST /api/help/query
Content-Type: application/json

{
  "question": "Comment créer une parcelle ?",
  "context": {
    "page": "/production/parcelles/",
    "user_role": "admin"
  }
}
```

**Réponse:**
```json
{
  "answer": "Pour créer une parcelle...",
  "sources": [
    {
      "title": "Guide Parcelles",
      "url": "/docs/help/USER_GUIDE.md#parcelles"
    }
  ],
  "suggestions": [
    "Comment définir l'encépagement ?",
    "Comment voir la météo parcelle ?"
  ]
}
```

---

## 🌦️ Smart Suggestions API

### Alertes Météo Parcelle

```http
GET /api/smart/weather/parcelle/{parcelle_id}/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "parcelle": {
    "id": 1,
    "name": "Les Grands Coteaux"
  },
  "current": {
    "temperature": 18,
    "humidity": 65,
    "wind_speed": 12,
    "conditions": "partly_cloudy"
  },
  "alerts": [
    {
      "type": "rain",
      "severity": "warning",
      "message": "Pluie prévue demain - Risque lessivage traitement",
      "action": "Reporter le traitement prévu"
    }
  ],
  "forecast": [
    {
      "date": "2024-12-25",
      "temp_min": 5,
      "temp_max": 12,
      "precipitation": 80,
      "wind": 15
    }
  ]
}
```

### Prévisions Météo Globales

```http
GET /api/smart/weather/forecast/
Authorization: Bearer {token}
```

### Suggestions de Cuves

```http
GET /api/smart/cuves/?volume_l=5000&color=rouge
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "suggestions": [
    {
      "id": 1,
      "name": "Cuve 01",
      "capacity": 10000,
      "available": 8000,
      "score": 95,
      "highlight": "perfect",
      "reasons": [
        "Capacité suffisante",
        "Même couleur que lot source",
        "Propre et disponible"
      ]
    },
    {
      "id": 2,
      "name": "Cuve 02",
      "capacity": 5000,
      "available": 5000,
      "score": 70,
      "highlight": "good",
      "reasons": [
        "Juste la capacité nécessaire"
      ]
    }
  ]
}
```

### Alertes Analyse

```http
GET /api/smart/analyse/{lot_id}/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "lot": {
    "id": 123,
    "name": "Lot 2024-001"
  },
  "last_analysis": {
    "date": "2024-12-20",
    "tav": 13.2,
    "at": 5.1,
    "ph": 3.45,
    "av": 0.35,
    "so2_libre": 25,
    "so2_total": 85
  },
  "alerts": [
    {
      "type": "av_rising",
      "severity": "warning",
      "message": "AV en hausse (+0.08 cette semaine)",
      "action": "Prévoir filtration ou sulfitage"
    }
  ],
  "trends": {
    "av": "rising",
    "so2": "stable",
    "ph": "stable"
  }
}
```

### Statut DRM

```http
GET /api/smart/drm/?brouillon=true
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "current_period": "2024-12",
  "deadline": "2025-01-10",
  "days_remaining": 16,
  "status": "draft",
  "alerts": [
    {
      "type": "deadline_approaching",
      "severity": "info",
      "message": "Échéance DRM dans 16 jours"
    }
  ],
  "draft": {
    "entries_count": 45,
    "total_entries_hl": 1250.5,
    "total_exits_hl": 320.0,
    "balance_hl": 930.5,
    "missing_data": []
  }
}
```

### Suggestions Intrants

```http
GET /api/smart/intrants/?operation=sulfitage
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "operation": "sulfitage",
  "suggestions": [
    {
      "product": "SO2 liquide",
      "dose": "3 g/hL",
      "frequency": 8,
      "last_used": "2024-12-15",
      "label": "Basé sur votre historique"
    }
  ],
  "history": [
    {
      "date": "2024-12-15",
      "product": "SO2 liquide",
      "dose": "3 g/hL",
      "lot": "Lot 2024-001"
    }
  ]
}
```

### Contexte Intelligent

```http
GET /api/smart/context/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "user": {
    "name": "Jean Dupont",
    "role": "admin"
  },
  "organization": {
    "name": "Domaine des Vignes"
  },
  "current_context": {
    "active_lots": 12,
    "pending_tasks": 5,
    "alerts_count": 2,
    "drm_status": "draft"
  },
  "quick_actions": [
    {
      "label": "Voir les alertes",
      "url": "/production/alertes/",
      "badge": 2
    },
    {
      "label": "Préparer DRM",
      "url": "/drm/editer/"
    }
  ]
}
```

---

## 👥 API Clients

### Liste des Clients

```http
GET /referentiels/clients/api/
Authorization: Bearer {token}

Query params:
- search: Recherche texte
- type: particulier|professionnel|caviste|export
- status: prospect|active|inactive
- page: Numéro de page
- per_page: Items par page (max 100)
```

**Réponse:**
```json
{
  "count": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8,
  "results": [
    {
      "id": "uuid",
      "type": "professionnel",
      "name": "Cave du Centre",
      "email": "contact@caveducentre.fr",
      "phone": "+33 1 23 45 67 89",
      "status": "active",
      "ca_12m": 15000.00,
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### Suggestions Clients (Autocomplete)

```http
GET /referentiels/clients/api/suggestions/?q=cave
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "suggestions": [
    {
      "id": "uuid",
      "name": "Cave du Centre",
      "type": "caviste",
      "city": "Tours"
    },
    {
      "id": "uuid2",
      "name": "Cave & Vin",
      "type": "caviste",
      "city": "Blois"
    }
  ]
}
```

### Création Rapide Client

```http
POST /referentiels/clients/api/quick-create/
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "particulier",
  "name": "Martin Dupont",
  "email": "martin@email.fr",
  "phone": "+33 6 12 34 56 78"
}
```

**Réponse:**
```json
{
  "success": true,
  "client": {
    "id": "uuid",
    "name": "Martin Dupont",
    "type": "particulier"
  }
}
```

### Détection Doublons

```http
POST /referentiels/clients/api/duplicates/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Cave du Centre",
  "email": "contact@caveducentre.fr"
}
```

**Réponse:**
```json
{
  "duplicates_found": true,
  "matches": [
    {
      "id": "uuid",
      "name": "Cave du Centre",
      "email": "contact@caveducentre.fr",
      "similarity": 0.95,
      "reason": "Email identique"
    }
  ]
}
```

---

## 📦 API Catalogue

### Liste Catalogue

```http
GET /catalogue/api/catalogue/
Authorization: Bearer {token}

Query params:
- search: Recherche texte
- color: rouge|blanc|rose|petillant
- appellation: Code appellation
- millesime: Année
```

**Réponse:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "name": "Chinon Rouge 2022",
      "cuvee": "Les Graviers",
      "color": "rouge",
      "appellation": "AOC Chinon",
      "millesime": 2022,
      "price_ht": 8.50,
      "stock_available": 1200
    }
  ]
}
```

### Facettes Catalogue

```http
GET /catalogue/api/catalogue/facets/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "colors": [
    {"value": "rouge", "count": 15},
    {"value": "blanc", "count": 8},
    {"value": "rose", "count": 2}
  ],
  "appellations": [
    {"value": "AOC Chinon", "count": 10},
    {"value": "AOC Vouvray", "count": 8}
  ],
  "millesimes": [
    {"value": 2022, "count": 12},
    {"value": 2021, "count": 8},
    {"value": 2020, "count": 5}
  ]
}
```

### Détail Produit Catalogue

```http
GET /catalogue/api/catalogue/{cuvee_id}/
Authorization: Bearer {token}
```

---

## 📊 API Stocks

### Dashboard Stock

```http
GET /stocks/api/inventaire/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "summary": {
    "total_vrac_hl": 1250.5,
    "total_bottles": 45000,
    "alerts_count": 3
  },
  "by_color": {
    "rouge": {"vrac_hl": 800, "bottles": 30000},
    "blanc": {"vrac_hl": 350, "bottles": 12000},
    "rose": {"vrac_hl": 100.5, "bottles": 3000}
  }
}
```

### Liste Alertes Stock

```http
GET /stocks/api/alertes/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "alerts": [
    {
      "id": 1,
      "type": "low_stock",
      "severity": "warning",
      "product": "Chinon Rouge 2022",
      "current": 50,
      "threshold": 100,
      "message": "Stock sous le seuil minimum"
    }
  ]
}
```

### Acquitter Alerte

```http
POST /stocks/api/alertes/acknowledge/
Authorization: Bearer {token}
Content-Type: application/json

{
  "alert_id": 1
}
```

### Badge Count Alertes

```http
GET /stocks/api/alertes/badge-count/
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "count": 3,
  "critical": 1,
  "warning": 2
}
```

---

## 📝 API DRM

### Recherche Codes INAO

```http
GET /drm/api/inao/?q=chinon
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "results": [
    {
      "code": "1B371",
      "name": "CHINON",
      "type": "AOC",
      "region": "Val de Loire",
      "colors": ["rouge", "blanc", "rose"]
    }
  ]
}
```

---

## 🔧 API Référentiels v2

### Recherche Unifiée

```http
GET /referentiels/api/v2/search/?q=cabernet&type=cepage
Authorization: Bearer {token}
```

**Réponse:**
```json
{
  "query": "cabernet",
  "type": "cepage",
  "count": 3,
  "results": [
    {
      "id": 1,
      "type": "cepage",
      "name": "Cabernet Franc",
      "code": "CABF"
    },
    {
      "id": 2,
      "type": "cepage",
      "name": "Cabernet Sauvignon",
      "code": "CABS"
    }
  ]
}
```

### Suggestions Autocomplete

```http
GET /referentiels/api/v2/suggestions/?q=cab&type=cepage
Authorization: Bearer {token}
```

### Facettes

```http
GET /referentiels/api/v2/facets/?type=parcelle
Authorization: Bearer {token}
```

### Édition Inline

```http
GET /referentiels/api/v2/{entity_type}/{entity_id}/cell/{field_name}/
Authorization: Bearer {token}
```

```http
POST /referentiels/api/v2/{entity_type}/{entity_id}/cell/{field_name}/save/
Authorization: Bearer {token}
Content-Type: application/json

{
  "value": "Nouvelle valeur"
}
```

### Annuler Édition

```http
POST /referentiels/api/v2/undo/
Authorization: Bearer {token}
Content-Type: application/json

{
  "edit_id": "uuid"
}
```

---

## 🔗 Webhooks

### Événements Disponibles

| Événement | Description |
|-----------|-------------|
| `customer.created` | Nouveau client créé |
| `customer.updated` | Client modifié |
| `order.created` | Nouvelle commande |
| `order.validated` | Commande validée |
| `invoice.created` | Facture créée |
| `invoice.paid` | Facture payée |
| `stock.low` | Stock sous seuil |
| `lot.created` | Lot technique créé |
| `analysis.alert` | Alerte analyse |

### Format Webhook

```json
{
  "event": "order.created",
  "timestamp": "2024-12-24T10:30:00Z",
  "organization_id": 1,
  "data": {
    "order_id": "uuid",
    "customer_id": "uuid",
    "total_ht": 1250.00,
    "lines_count": 5
  },
  "signature": "sha256=xxxx"
}
```

### Vérification Signature

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## 📄 Codes d'Erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé (permissions) |
| 404 | Ressource non trouvée |
| 422 | Erreur de validation |
| 429 | Trop de requêtes (rate limit) |
| 500 | Erreur serveur |

### Format Erreur

```json
{
  "error": "validation_error",
  "message": "Les données fournies sont invalides",
  "details": {
    "email": ["Ce champ est requis"],
    "phone": ["Format invalide"]
  }
}
```

---

## ⚡ Rate Limiting

- **Authentifié** : 1000 requêtes / minute
- **Non authentifié** : 60 requêtes / minute
- **Webhooks** : 100 requêtes / minute

Headers de réponse :
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1703412000
```

---

## 📚 SDKs & Exemples

### cURL

```bash
# Obtenir CSRF
curl -c cookies.txt https://monchai.fr/api/auth/csrf/

# Login
curl -b cookies.txt -c cookies.txt \
  -H "X-CSRFToken: TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"xxx"}' \
  https://monchai.fr/api/auth/session/

# API avec Bearer
curl -H "Authorization: Bearer mch_xxxx" \
  https://monchai.fr/api/v1/organization/
```

### JavaScript (fetch)

```javascript
// Avec session cookie
const response = await fetch('/api/auth/whoami/', {
  credentials: 'include'
});
const data = await response.json();

// Avec Bearer token
const response = await fetch('/api/v1/organization/', {
  headers: {
    'Authorization': 'Bearer mch_xxxx'
  }
});
```

### Python (requests)

```python
import requests

# Session
session = requests.Session()
csrf = session.get('https://monchai.fr/api/auth/csrf/').json()
session.post('https://monchai.fr/api/auth/session/', 
    json={'email': 'user@example.com', 'password': 'xxx'},
    headers={'X-CSRFToken': csrf['csrfToken']})

# Bearer
response = requests.get('https://monchai.fr/api/v1/organization/',
    headers={'Authorization': 'Bearer mch_xxxx'})
```

---

*Référence API MonChai v2.0 - Mise à jour Décembre 2024*

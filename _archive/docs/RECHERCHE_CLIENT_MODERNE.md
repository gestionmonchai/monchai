# Recherche Client Moderne - Formulaire Devis

## 🎯 Objectif

Remplacer l'ancienne interface de sélection client (dropdown + autocomplétion basique) par une **recherche moderne en temps réel** inspirée de la page liste clients.

---

## ✨ Nouvelles Fonctionnalités

### 1. **Recherche en Temps Réel**

```
┌─────────────────────────────────────────────────────┐
│ 🔍 Recherchez un client par nom, ville, email...   │
│                                            [spinner]│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ℹ️  5 client(s) trouvé(s)                           │
├─────────────────────────────────────────────────────┤
│ 👤 Domaine du Soleil              [Professionnel]  │
│    📍 Bordeaux                                      │
├─────────────────────────────────────────────────────┤
│ 👤 Cave Martin                    [Particulier]    │
│    📍 Lyon                                          │
└─────────────────────────────────────────────────────┘
```

**Caractéristiques**:
- ✅ Debounce 300ms pour éviter surcharge serveur
- ✅ Spinner pendant la recherche
- ✅ Recherche dès 2 caractères
- ✅ Recherche sur nom, ville, code postal
- ✅ Affichage jusqu'à 50 résultats
- ✅ Scroll automatique si > 300px

---

### 2. **Carte Client Sélectionné**

```
┌─────────────────────────────────────────────────────┐
│ ✅ Domaine du Soleil [Professionnel]    Bordeaux   │
│                                    [❌ Changer]     │
└─────────────────────────────────────────────────────┘
```

**Avantages**:
- ✅ Visibilité claire du client sélectionné
- ✅ Badge avec le type de client
- ✅ Ville affichée
- ✅ Bouton "Changer" pour modifier

---

### 3. **Résultats Enrichis**

Chaque résultat affiche:
- **Nom du client** (en gras)
- **Ville** (avec icône 📍)
- **Type** (badge coloré)

**Exemple de carte résultat**:
```html
┌─────────────────────────────────────────┐
│ 👤 Restaurant Le Gourmet               │
│    📍 Paris              [Pro]          │
└─────────────────────────────────────────┘
```

---

## 🔧 Implémentation Technique

### API Améliorée

**Endpoint**: `/ventes/devis/api/sales-customers/suggestions/`

**Paramètres**:
- `q` : Terme de recherche
- `limit` : Nombre max de résultats (défaut: 10, max: 50)

**Recherche sur**:
- `legal_name` (nom du client)
- `billing_city` (ville)
- `billing_postal_code` (code postal)

**Réponse enrichie**:
```json
{
  "success": true,
  "query": "Domaine",
  "suggestions": [
    {
      "id": "uuid-123",
      "name": "Domaine du Soleil",
      "type": "Professionnel",
      "city": "Bordeaux",
      "postal_code": "33000"
    }
  ]
}
```

---

### Structure HTML

```html
<!-- Client sélectionné (caché par défaut) -->
<div id="selected_customer_card" style="display:none;">
  <div class="card border-success">
    <div class="card-body py-2">
      <i class="bi bi-person-check-fill text-success"></i>
      <strong id="selected_customer_name"></strong>
      <span class="badge" id="selected_customer_type"></span>
      <span id="selected_customer_city"></span>
      <button id="clear_customer">Changer</button>
    </div>
  </div>
</div>

<!-- Zone de recherche -->
<div id="customer_search_wrapper">
  <!-- Input avec spinner -->
  <input id="cust_search" placeholder="Recherchez...">
  <i class="bi bi-search" id="cust-search-icon"></i>
  <div class="spinner-border" id="cust-search-spinner"></div>
  
  <!-- Résultats -->
  <div id="customer_results">
    <div class="card">
      <div class="card-header">
        <span id="customer_results_count">0</span> client(s)
      </div>
      <div id="customer_results_list">
        <!-- Résultats injectés ici -->
      </div>
    </div>
  </div>
  
  <!-- Bouton création -->
  <button id="cust_quick_new">+ Créer un nouveau client</button>
</div>
```

---

### JavaScript Moderne

```javascript
// Configuration
const DEBOUNCE_MS = 300;
let searchTimeout;

// Recherche AJAX
function performCustomerSearch() {
  const query = custSearch.value.trim();
  
  if (query.length < 2) {
    resultsDiv.style.display = 'none';
    return;
  }
  
  // Afficher spinner
  searchIcon.classList.add('d-none');
  searchSpinner.classList.remove('d-none');
  
  // Requête AJAX
  fetch(suggestUrl + "?q=" + encodeURIComponent(query) + "&limit=20")
    .then(r => r.json())
    .then(data => {
      displayCustomerResults(data.suggestions || []);
    })
    .finally(() => {
      searchIcon.classList.remove('d-none');
      searchSpinner.classList.add('d-none');
    });
}

// Affichage des résultats
function displayCustomerResults(customers) {
  resultsList.innerHTML = '';
  resultsCount.textContent = customers.length;
  
  customers.forEach(customer => {
    const item = document.createElement('div');
    item.className = 'list-group-item customer-result-item';
    item.innerHTML = `
      <div class="fw-semibold">
        <i class="bi bi-person"></i> ${customer.name}
      </div>
      <small class="text-muted">
        <i class="bi bi-geo-alt"></i> ${customer.city}
      </small>
      <span class="badge">${customer.type}</span>
    `;
    
    item.addEventListener('click', () => {
      selectCustomer(customer.id, customer.name, customer.type, customer.city);
    });
    
    resultsList.appendChild(item);
  });
  
  resultsDiv.style.display = 'block';
}

// Sélection
function selectCustomer(id, name, type, city) {
  // Mettre à jour le select caché
  custSelect.value = id;
  
  // Afficher la carte
  selectedName.textContent = name;
  selectedType.textContent = type;
  selectedCity.textContent = city;
  
  selectedCard.style.display = 'block';
  searchWrapper.style.display = 'none';
}

// Événements
custSearch.addEventListener('input', () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(performCustomerSearch, DEBOUNCE_MS);
});
```

---

### CSS

```css
/* Résultats de recherche */
.customer-result-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.customer-result-item:hover {
  background-color: #f8f9fa;
}

.customer-result-item.active {
  background-color: #e7f3ff;
  border-left: 3px solid #0d6efd;
}
```

---

## 📊 Comparaison Avant/Après

### ❌ Avant

```
┌────────────────────────────────┐
│ Client: [▼ Sélectionner...]    │
│ [Rechercher...] [Nouveau]      │
│ • Domaine du Soleil            │
│ • Cave Martin                  │
└────────────────────────────────┘
```

**Problèmes**:
- Dropdown peu ergonomique
- Pas de recherche sur ville
- Pas d'infos contextuelles
- Interface confuse

### ✅ Après

```
┌─────────────────────────────────────────┐
│ 🔍 Recherchez un client...              │
│                                          │
│ ℹ️  2 client(s) trouvé(s)                │
│ ┌─────────────────────────────────────┐ │
│ │ 👤 Domaine du Soleil  [Pro]         │ │
│ │    📍 Bordeaux                      │ │
│ ├─────────────────────────────────────┤ │
│ │ 👤 Cave Martin       [Part.]        │ │
│ │    📍 Lyon                          │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ [+ Créer un nouveau client]              │
└─────────────────────────────────────────┘
```

**Avantages**:
- ✅ Recherche en temps réel
- ✅ Infos riches (ville, type)
- ✅ Interface moderne
- ✅ Feedback visuel (spinner)

---

## 🎯 Workflow Utilisateur

### 1. **Recherche d'un client**

```
1. Utilisateur tape "Domaine"
   ↓
2. Debounce 300ms
   ↓
3. Requête AJAX vers API
   ↓
4. Affichage spinner
   ↓
5. Réception résultats
   ↓
6. Affichage cartes cliquables
```

### 2. **Sélection**

```
1. Clic sur une carte
   ↓
2. Mise à jour select caché
   ↓
3. Affichage carte sélection
   ↓
4. Masquage zone recherche
```

### 3. **Changement**

```
1. Clic sur "Changer"
   ↓
2. Masquage carte sélection
   ↓
3. Affichage zone recherche
   ↓
4. Focus sur input
```

---

## 🧪 Tests

### Test 1: Recherche par nom
```
Input: "Domaine"
Expected: 1 résultat "Domaine du Soleil"
Status: ✅
```

### Test 2: Recherche par ville
```
Input: "Bordeaux"
Expected: Tous les clients de Bordeaux
Status: ✅
```

### Test 3: Recherche vide
```
Input: "" (moins de 2 caractères)
Expected: Masquage des résultats
Status: ✅
```

### Test 4: Aucun résultat
```
Input: "XYZ123"
Expected: Message "Aucun client trouvé"
Status: ✅
```

### Test 5: Sélection
```
Action: Clic sur "Domaine du Soleil"
Expected: Carte verte affichée, recherche masquée
Status: ✅
```

### Test 6: Changement
```
Action: Clic sur "Changer"
Expected: Retour à la recherche, focus sur input
Status: ✅
```

---

## 🚀 Améliorations Futures

### Court terme
- [ ] Afficher l'email dans les résultats
- [ ] Ajouter un filtre par type de client
- [ ] Historique des derniers clients sélectionnés

### Moyen terme
- [ ] Recherche sur email et téléphone
- [ ] Tri des résultats (pertinence, alphabétique)
- [ ] Pagination si > 50 résultats

### Long terme
- [ ] Favoris clients
- [ ] Suggestions intelligentes (clients fréquents)
- [ ] Intégration avec module clients complet

---

## 📁 Fichiers Modifiés

```
apps/sales/
├── views_quotes.py              ✅ API enrichie

templates/ventes/
├── devis_form.html              ✅ Interface moderne
│   ├── HTML restructuré
│   ├── CSS pour résultats
│   └── JavaScript AJAX

docs/
└── RECHERCHE_CLIENT_MODERNE.md  ✅ Cette doc
```

---

## 🎓 Inspiration

Cette implémentation s'inspire de:
- **Page liste clients** (`templates/clients/customers_list.html`)
- **Patterns UX modernes** (Google, Amazon)
- **Best practices** (debounce, spinner, feedback)

---

## 📝 Notes Techniques

### Debounce
- **300ms** : Équilibre entre réactivité et charge serveur
- Annulation si nouvelle saisie
- Recherche immédiate sur Enter

### Performance
- Limite 50 résultats max
- Scroll si > 300px
- Pas de recherche si < 2 caractères

### Accessibilité
- Focus automatique après "Changer"
- Enter pour rechercher
- Escape pour fermer (à implémenter)

---

*Document créé le: 29/10/2024*
*Version: 1.0*
*Inspiré de: templates/clients/customers_list.html*

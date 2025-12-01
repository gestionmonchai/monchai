# 🔧 Correction Performance Module d'Aide

## 🔍 Problème Identifié

**Modèle actuel** : `monchai-help:latest` (4.4 GB) 🔴
- Temps moyen : 14,8s
- Temps max : 28,7s
- **Beaucoup trop lent !**

## ✅ Solution Appliquée

### 1. Changement de Modèle

**Avant** :
```python
HELP_MODEL = 'monchai-help'  # 4.4 GB, très lent
```

**Après** :
```python
HELP_MODEL = 'phi3:mini'  # 2.2 GB, rapide (1-3s)
```

**Alternative ultra-rapide** :
```python
HELP_MODEL = 'gemma3:1b'  # 815 MB, ultra rapide (<1s)
```

---

### 2. Augmentation du Cache

**Avant** :
```python
HELP_CACHE_TTL = 180  # 3 minutes
```

**Après** :
```python
HELP_CACHE_TTL = 3600  # 1 heure
```

---

### 3. Pré-chargement du Modèle

**Avant** :
```python
OLLAMA_KEEP_ALIVE = '30m'  # 30 minutes
```

**Après** :
```python
OLLAMA_KEEP_ALIVE = '60m'  # 1 heure
```

---

### 4. Timeout Adapté

**Avant** :
```python
HELP_TIMEOUT = 15  # 15 secondes
```

**Après** :
```python
HELP_TIMEOUT = 10  # 10 secondes (suffisant pour phi3:mini)
```

---

## 📝 Modifications à Appliquer

### Option A : Via .env (Recommandé)

Créer/modifier le fichier `.env` :

```env
# Modèle rapide
HELP_MODEL=phi3:mini

# Cache 1 heure
HELP_CACHE_TTL=3600

# Keep alive 1 heure
OLLAMA_KEEP_ALIVE=60m

# Timeout 10s
HELP_TIMEOUT=10
```

### Option B : Via settings.py

Modifier `monchai/settings.py` :

```python
# AI Help / Ollama configuration
OLLAMA_URL = config('OLLAMA_URL', default='http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3.2:1b')
HELP_MODEL = config('HELP_MODEL', default='phi3:mini')  # ← CHANGÉ
HELP_RATE_LIMIT_CALLS = config('HELP_RATE_LIMIT_CALLS', default=10, cast=int)
HELP_RATE_LIMIT_WINDOW = config('HELP_RATE_LIMIT_WINDOW', default=300, cast=int)
HELP_TIMEOUT = config('HELP_TIMEOUT', default=10, cast=int)  # ← CHANGÉ
OLLAMA_KEEP_ALIVE = config('OLLAMA_KEEP_ALIVE', default='60m')  # ← CHANGÉ
HELP_NUM_PREDICT = config('HELP_NUM_PREDICT', default=256, cast=int)
# Robustness tunables
OLLAMA_CONNECT_TIMEOUT = config('OLLAMA_CONNECT_TIMEOUT', default=3, cast=int)
HELP_OLLAMA_RETRIES = config('HELP_OLLAMA_RETRIES', default=2, cast=int)
HELP_CACHE_TTL = config('HELP_CACHE_TTL', default=3600, cast=int)  # ← CHANGÉ
HELP_MAX_HINTS_CHARS = config('HELP_MAX_HINTS_CHARS', default=800, cast=int)
HELP_MAX_DOCS_CHARS = config('HELP_MAX_DOCS_CHARS', default=1200, cast=int)
HELP_HTTP_POOL_SIZE = config('HELP_HTTP_POOL_SIZE', default=20, cast=int)
```

---

## 🧪 Tests Après Correction

### Test 1 : Vérifier le modèle chargé

```bash
python manage.py help_healthcheck
```

**Résultat attendu** : Réponse en < 2s

---

### Test 2 : Test de performance complet

```bash
python test_help_performance.py
```

**Résultats attendus** :
- Temps moyen : < 3s ✅
- Temps max : < 5s ✅
- Tous les tests réussis : 3/3 ✅

---

### Test 3 : Test depuis le site

1. Ouvrir le site : http://localhost:8000
2. Cliquer sur le widget d'aide (coin bas-droite)
3. Poser une question : "Comment créer un client ?"
4. **Résultat attendu** : Réponse en < 3s

---

## 📊 Comparaison Avant/Après

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Temps moyen** | 14 838 ms | ~2 000 ms | **-86%** 🎉 |
| **Temps max** | 28 689 ms | ~3 000 ms | **-90%** 🎉 |
| **Cache TTL** | 180s | 3600s | **+1900%** |
| **Keep alive** | 30m | 60m | **+100%** |
| **Modèle** | 4.4 GB | 2.2 GB | **-50%** |

---

## 🚀 Résultat Final

### Avant
- 🔴 Temps moyen : 14,8s (inacceptable)
- 🔴 Temps max : 28,7s (catastrophique)
- 🔴 UX : très mauvaise
- 🔴 Utilisateurs : frustrés

### Après
- 🟢 Temps moyen : ~2s (acceptable)
- 🟢 Temps max : ~3s (bon)
- 🟢 UX : bonne
- 🟢 Utilisateurs : satisfaits

---

## 🎯 Actions Immédiates

1. **Modifier `.env`** ou **`settings.py`** avec les nouvelles valeurs
2. **Redémarrer le serveur Django**
   ```bash
   python manage.py runserver
   ```
3. **Tester** avec `python test_help_performance.py`
4. **Vérifier** depuis le site

---

## 💡 Optimisations Futures (Optionnel)

### Si encore trop lent, essayer gemma3:1b

```env
HELP_MODEL=gemma3:1b
HELP_TIMEOUT=5
```

**Résultat attendu** : < 1s par requête

---

### Si qualité insuffisante, revenir à phi3:mini

```env
HELP_MODEL=phi3:mini
HELP_TIMEOUT=10
```

**Résultat attendu** : 1-3s par requête avec bonne qualité

---

## 📋 Checklist de Déploiement

- [ ] Modifier `.env` ou `settings.py`
- [ ] Redémarrer le serveur
- [ ] Tester avec `help_healthcheck`
- [ ] Tester avec `test_help_performance.py`
- [ ] Tester depuis le site
- [ ] Vérifier les logs
- [ ] Valider avec les utilisateurs

---

*Correction créée le : 29/10/2024*
*Problème : Modèle trop lourd (4.4 GB)*
*Solution : Modèle plus léger (2.2 GB) + cache + keep_alive*
*Amélioration attendue : -86% temps de réponse*

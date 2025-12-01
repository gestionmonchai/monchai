# 🔍 Diagnostic Performance Module d'Aide

## 📊 Résultats des Tests

### Temps de Réponse Mesurés
- **Temps moyen** : 14 838 ms (14,8 secondes) 🔴
- **Temps min** : 1 531 ms (1,5 secondes)
- **Temps max** : 28 689 ms (28,7 secondes) 🔴🔴🔴
- **Taux de succès** : 3/3 (100%)
- **Mode dégradé** : 0/3 (0%)

### Détail par Question

| Question | Temps (ms) | Longueur Réponse |
|----------|------------|------------------|
| Comment créer un client ? | 1 531 ms | 16 caractères |
| Comment faire un devis ? | 28 689 ms | 163 caractères |
| Comment gérer le stock ? | 14 295 ms | 210 caractères |

## 🔴 Problèmes Identifiés

### 1. **Ollama Trop Lent** (Critique)
- Temps de réponse > 10s inacceptable pour l'UX
- Variation énorme (1,5s à 28s) = instabilité
- Probablement dû au modèle trop lourd

### 2. **Pas de Cache Efficace**
- Première requête : 1,5s (cache vide)
- Deuxième requête : 28s (pas de cache hit)
- Le cache Redis ne semble pas fonctionner correctement

### 3. **Timeout Trop Court**
- Timeout actuel : 12s
- Temps max observé : 28s
- → Certaines requêtes vont timeout

## 🎯 Solutions Proposées

### Solution 1 : Modèle Plus Léger (Recommandé)

**Problème** : Le modèle actuel est probablement trop lourd (ex: llama3:8b, mistral:7b)

**Solution** : Utiliser un modèle plus rapide
```python
# settings.py
OLLAMA_MODEL = 'phi3:mini'  # 3.8B params, très rapide
# ou
OLLAMA_MODEL = 'tinyllama'  # 1.1B params, ultra rapide
# ou
OLLAMA_MODEL = 'gemma:2b'   # 2B params, bon compromis
```

**Avantages** :
- ✅ Réponse < 2s
- ✅ Moins de RAM
- ✅ Meilleure UX

**Inconvénients** :
- ⚠️ Qualité réponses légèrement inférieure

---

### Solution 2 : Augmenter le Timeout

**Problème** : Timeout 12s trop court pour le modèle actuel

**Solution** : Augmenter à 30s
```python
# settings.py
HELP_TIMEOUT = 30  # Au lieu de 12
```

**Avantages** :
- ✅ Évite les timeouts
- ✅ Pas de changement de modèle

**Inconvénients** :
- ❌ UX toujours mauvaise (attente longue)
- ❌ Ne résout pas le problème de fond

---

### Solution 3 : Cache Agressif (Complémentaire)

**Problème** : Cache actuel (5 min) pas assez long

**Solution** : Augmenter le TTL du cache
```python
# settings.py
HELP_CACHE_TTL = 3600  # 1 heure au lieu de 5 min
```

**Avantages** :
- ✅ Réponses instantanées si déjà en cache
- ✅ Réduit la charge Ollama

**Inconvénients** :
- ⚠️ Réponses moins à jour
- ⚠️ Ne résout pas la première requête

---

### Solution 4 : Pré-chargement du Modèle

**Problème** : Cold start Ollama lent

**Solution** : Garder le modèle en mémoire
```python
# settings.py
OLLAMA_KEEP_ALIVE = '60m'  # Garde le modèle 60 min
```

**Avantages** :
- ✅ Évite le cold start
- ✅ Réponses plus rapides

**Inconvénients** :
- ⚠️ Consomme de la RAM en permanence

---

### Solution 5 : Mode Dégradé Plus Rapide (Fallback)

**Problème** : Attente trop longue avant fallback

**Solution** : Timeout plus court avec fallback immédiat
```python
# views.py
try:
    answer = ollama_generate(..., timeout=5)  # 5s max
except OllamaError:
    # Fallback immédiat
    return degraded_answer()
```

**Avantages** :
- ✅ Réponse garantie < 5s
- ✅ UX acceptable

**Inconvénients** :
- ⚠️ Plus de fallbacks
- ⚠️ Qualité variable

---

## 🚀 Plan d'Action Recommandé

### Phase 1 : Quick Win (Immédiat)

1. **Changer de modèle** (phi3:mini ou gemma:2b)
   ```bash
   ollama pull phi3:mini
   ```
   ```python
   # settings.py
   OLLAMA_MODEL = 'phi3:mini'
   HELP_MODEL = 'phi3:mini'
   ```

2. **Augmenter le cache**
   ```python
   HELP_CACHE_TTL = 3600  # 1 heure
   ```

3. **Pré-charger le modèle**
   ```python
   OLLAMA_KEEP_ALIVE = '60m'
   ```

**Résultat attendu** : Temps de réponse < 3s

---

### Phase 2 : Optimisation (Court terme)

4. **Réduire la taille des prompts**
   - Déjà fait : max_hints=400, max_docs=600
   - ✅ OK

5. **Augmenter le pool HTTP**
   - Déjà fait : pool_size=20
   - ✅ OK

6. **Tester les performances**
   ```bash
   python test_help_performance.py
   ```

**Résultat attendu** : Temps de réponse < 2s

---

### Phase 3 : Robustesse (Moyen terme)

7. **Fallback plus rapide**
   ```python
   HELP_TIMEOUT = 5  # 5s max avant fallback
   ```

8. **Monitoring**
   - Logger les temps de réponse
   - Alertes si > 5s

9. **Tests de charge**
   - Simuler 10 utilisateurs simultanés
   - Vérifier la stabilité

**Résultat attendu** : Système stable et rapide

---

## 📋 Checklist de Vérification

### Avant Optimisation
- [x] Temps moyen : 14,8s 🔴
- [x] Temps max : 28,7s 🔴🔴🔴
- [x] Variation : 1,5s - 28s (instable)
- [x] Cache : inefficace
- [x] UX : inacceptable

### Après Optimisation (Objectifs)
- [ ] Temps moyen : < 3s ✅
- [ ] Temps max : < 5s ✅
- [ ] Variation : < 2s (stable)
- [ ] Cache : efficace (hit rate > 50%)
- [ ] UX : acceptable

---

## 🔧 Commandes Utiles

### Tester Ollama directement
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Comment créer un client ?",
  "stream": false
}'
```

### Télécharger un modèle plus léger
```bash
ollama pull phi3:mini
ollama pull gemma:2b
ollama pull tinyllama
```

### Lister les modèles disponibles
```bash
ollama list
```

### Tester les performances
```bash
python test_help_performance.py
```

---

## 📊 Comparaison Modèles

| Modèle | Taille | Vitesse | Qualité | Recommandé |
|--------|--------|---------|---------|------------|
| **llama3:8b** | 4.7 GB | 🔴 Lent (10-30s) | ⭐⭐⭐⭐⭐ | ❌ |
| **mistral:7b** | 4.1 GB | 🔴 Lent (8-25s) | ⭐⭐⭐⭐⭐ | ❌ |
| **phi3:mini** | 2.3 GB | 🟢 Rapide (1-3s) | ⭐⭐⭐⭐ | ✅ |
| **gemma:2b** | 1.4 GB | 🟢 Rapide (1-2s) | ⭐⭐⭐⭐ | ✅ |
| **tinyllama** | 637 MB | 🟢 Ultra rapide (<1s) | ⭐⭐⭐ | ⚠️ |

---

## 🎯 Conclusion

**Diagnostic** : Le modèle actuel est trop lourd pour une utilisation interactive.

**Solution recommandée** : 
1. Passer à `phi3:mini` (bon compromis vitesse/qualité)
2. Augmenter le cache à 1 heure
3. Pré-charger le modèle avec `keep_alive=60m`

**Résultat attendu** : Temps de réponse < 3s (vs 14,8s actuellement)

---

*Diagnostic effectué le : 29/10/2024*
*Tests : 3/3 réussis*
*Problème : Modèle trop lourd*
*Solution : Modèle plus léger + cache + keep_alive*

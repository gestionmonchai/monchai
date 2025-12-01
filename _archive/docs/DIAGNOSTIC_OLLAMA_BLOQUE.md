# 🔴 DIAGNOSTIC : Ollama Bloqué / Non Réactif

## 🔍 Problème Identifié

**Symptômes** :
- ❌ Ollama timeout après 30 secondes
- ❌ Aucune réponse (ni phi3:mini, ni monchai-help)
- ❌ Mode dégradé activé systématiquement
- ✅ Ollama API répond (curl /api/tags fonctionne)
- ✅ Modèles présents (ollama list fonctionne)

**Diagnostic** : Ollama est **démarré** mais **bloqué** lors de la génération.

---

## 🎯 Causes Possibles

### 1. **Ollama Surchargé / Bloqué** (Probable)
- Processus Ollama figé
- Modèle chargé en mémoire mais non réactif
- GPU/CPU surchargé

### 2. **Modèle Corrompu** (Possible)
- Modèle mal téléchargé
- Cache corrompu

### 3. **Mémoire Insuffisante** (Possible)
- RAM saturée
- Swap excessif

### 4. **Conflit de Processus** (Possible)
- Plusieurs instances Ollama
- Conflit de ports

---

## 🔧 Solutions

### Solution 1 : Redémarrer Ollama (Recommandé)

#### Windows

```powershell
# Arrêter Ollama
taskkill /F /IM ollama.exe

# Attendre 5 secondes
Start-Sleep -Seconds 5

# Redémarrer Ollama
Start-Process ollama serve
```

#### Ou via Services Windows

1. Ouvrir "Services" (services.msc)
2. Chercher "Ollama"
3. Clic droit → Redémarrer

---

### Solution 2 : Vider le Cache Ollama

```bash
# Supprimer le cache
ollama rm phi3:mini
ollama rm monchai-help

# Re-télécharger
ollama pull phi3:mini
```

---

### Solution 3 : Vérifier la Mémoire

```powershell
# Vérifier la RAM disponible
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory, TotalVisibleMemorySize

# Vérifier les processus Ollama
Get-Process ollama
```

**Action** : Si RAM < 2 GB libre, fermer d'autres applications

---

### Solution 4 : Utiliser un Modèle Plus Léger

Si phi3:mini (2.2 GB) est trop lourd :

```bash
# Télécharger gemma3:1b (815 MB)
ollama pull gemma3:1b
```

Puis modifier `.env` :
```env
HELP_MODEL=gemma3:1b
```

---

### Solution 5 : Mode Dégradé Permanent (Fallback)

Si Ollama ne fonctionne vraiment pas, désactiver l'IA :

```env
# Dans .env
HELP_MODEL=none
```

Puis modifier `apps/ai/views.py` pour toujours utiliser le fallback :

```python
def help_query(request):
    # ... code existant ...
    
    # Forcer le mode dégradé
    text = degraded_answer()
    resp = {
        'text': text,
        'page_effective': page_effective,
        'degraded': True,
    }
    return JsonResponse(resp, status=200)
```

---

## 🧪 Tests de Vérification

### Test 1 : Ollama répond-il ?

```bash
curl http://localhost:11434/api/tags
```

**Résultat attendu** : Liste des modèles en < 1s

---

### Test 2 : Génération simple

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Bonjour",
  "stream": false
}'
```

**Résultat attendu** : Réponse en < 5s

---

### Test 3 : Test Python direct

```bash
python test_ollama_direct.py
```

**Résultat attendu** : Réponse en < 5s

---

### Test 4 : Test complet

```bash
python test_help_performance.py
```

**Résultat attendu** : 
- Temps moyen < 5s
- Mode dégradé : 0/3

---

## 📋 Procédure de Résolution Complète

### Étape 1 : Diagnostic

```powershell
# Vérifier si Ollama tourne
Get-Process ollama

# Vérifier la RAM
Get-CimInstance Win32_OperatingSystem | Select FreePhysicalMemory

# Tester l'API
curl http://localhost:11434/api/tags
```

---

### Étape 2 : Redémarrage

```powershell
# Arrêter Ollama
taskkill /F /IM ollama.exe

# Attendre
Start-Sleep -Seconds 5

# Redémarrer
Start-Process ollama serve

# Attendre le démarrage
Start-Sleep -Seconds 10
```

---

### Étape 3 : Test Simple

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3:mini",
  "prompt": "Test",
  "stream": false
}'
```

**Si ça marche** : Passer à l'étape 4
**Si ça ne marche pas** : Passer à l'étape 5

---

### Étape 4 : Test Complet

```bash
python test_help_performance.py
```

**Si ça marche** : ✅ Problème résolu !
**Si ça ne marche pas** : Passer à l'étape 5

---

### Étape 5 : Modèle Plus Léger

```bash
# Télécharger gemma3:1b
ollama pull gemma3:1b
```

Modifier `.env` :
```env
HELP_MODEL=gemma3:1b
HELP_TIMEOUT=5
```

Retester :
```bash
python test_help_performance.py
```

---

### Étape 6 : Mode Dégradé (Dernier Recours)

Si rien ne fonctionne, désactiver Ollama temporairement.

Créer un fichier `apps/ai/views_fallback.py` :

```python
from django.http import JsonResponse

def help_query_fallback(request):
    """Version fallback sans Ollama."""
    import json
    data = json.loads(request.body.decode('utf-8') or '{}')
    page_url = data.get('page_url', '/')
    question = data.get('question', '')
    
    # Réponse générique
    text = f"""Aide rapide
    
Pour {question}, voici la procédure générale :

1) Identifier le module concerné
2) Ouvrir le module depuis le menu
3) Créer ou chercher l'élément
4) Compléter les informations
5) Enregistrer

Pour une aide plus détaillée, consultez la documentation ou contactez le support.
"""
    
    return JsonResponse({
        'text': text,
        'page_effective': page_url,
        'degraded': True,
    })
```

Modifier `apps/ai/urls.py` :
```python
from .views_fallback import help_query_fallback

urlpatterns = [
    path('help/query', help_query_fallback, name='help_query'),  # Utiliser fallback
    # ...
]
```

---

## 🎯 Résumé des Actions

### Actions Immédiates

1. ✅ **Redémarrer Ollama**
   ```powershell
   taskkill /F /IM ollama.exe
   Start-Sleep -Seconds 5
   Start-Process ollama serve
   ```

2. ✅ **Tester**
   ```bash
   python test_ollama_direct.py
   ```

3. ✅ **Si ça ne marche pas : Modèle plus léger**
   ```bash
   ollama pull gemma3:1b
   ```
   ```env
   HELP_MODEL=gemma3:1b
   ```

---

### Actions de Secours

4. ⚠️ **Si toujours bloqué : Vider le cache**
   ```bash
   ollama rm phi3:mini
   ollama pull phi3:mini
   ```

5. ⚠️ **Si vraiment rien ne marche : Mode dégradé**
   - Utiliser `views_fallback.py`
   - Désactiver Ollama temporairement

---

## 📊 Checklist de Résolution

- [ ] Ollama redémarré
- [ ] Test simple réussi (curl)
- [ ] Test Python réussi
- [ ] Test complet réussi
- [ ] Temps de réponse < 5s
- [ ] Mode dégradé : 0/3
- [ ] UX acceptable

---

## 💡 Recommandations Finales

### Court Terme
1. Redémarrer Ollama
2. Utiliser gemma3:1b (plus léger)
3. Augmenter le cache (3600s)

### Moyen Terme
1. Monitorer la RAM
2. Redémarrer Ollama quotidiennement
3. Utiliser un modèle stable

### Long Terme
1. Envisager un serveur dédié Ollama
2. Utiliser une API externe (OpenAI, Anthropic)
3. Implémenter un système de fallback robuste

---

*Diagnostic créé le : 29/10/2024*
*Problème : Ollama bloqué / timeout 30s*
*Solution immédiate : Redémarrer Ollama*
*Solution alternative : Modèle plus léger (gemma3:1b)*

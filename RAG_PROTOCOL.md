# Protocole reproductible d'amélioration RAG

## 1. Objectifs
- Garantir que l'assistant répond uniquement à partir des extraits pertinents (pas d'improvisation).
- Mesurer la qualité des réponses sur les requêtes critiques (Côtes de Duras pour l'instant).
- Boucler sur des itérations courtes : récupérer les métriques, appliquer un correctif, vérifier la régression, documenter.

## 2. Données de référence
| Catégorie | Question | Réponse attendue | Source RAG |
|-----------|----------|------------------|------------|
| Charges | « Quelles sont les charges maximales par hectare pour les blancs Côtes de Duras ? » | 12 000 kg/ha | Chapitre IV §4.1 « Rendement maximum en production » |
| Densité | « Quelle densité minimale est requise pour les nouvelles parcelles rouges Côtes de Duras ? » | 3 300 pieds/ha | Chapitre III §3.2 « Densité de plantation » |
| Richesse | « Quelles richesses en sucre sont demandées pour un liquoreux Côtes de Duras ? » | 255 g/L minimum de sucres fermentescibles | Chapitre V §5.3 |
| Vendanges | « Quels créneaux de récolte sont autorisés pour les rosés Côtes de Duras ? » | Vendanges manuelles ou mécanisées après maturité fixée par l’ODG, avec interdiction avant annonce officielle | Chapitre II §2.4 |
> Ajouter une ligne par nouvelle appellation / thématique.

## 3. Script de test
Commande à lancer avant/après chaque modification :
```bash
python manage.py shell -c "from django.test import Client;import json;tests={...};client=Client(); ..."
```
Créer un fichier `scripts/rag_test_suite.py` (à venir) pour encapsuler ces tests. Pour l'instant, sauvegarder les sorties dans `tests/logs/rag_<date>.txt`.

## 4. Critères d'évaluation
1. **Exactitude numérique / textuelle** : l'unité et la valeur doivent correspondre à la table ci-dessus.
2. **Citation** : présence du préfixe `[DOCUMENT: ... | SECTION: ...]`.
3. **Conformité directives** : réponse « Je ne sais pas à partir des extraits fournis » si le contexte n'existe pas.
4. **Stabilité** : répéter chaque demande 3 fois; score attendu ≥ 3/3 pour passer.

## 5. Boucle d'amélioration**
1. **Collecte** : exécuter la suite de tests, noter les écarts.
2. **Diagnostic** : inspecter `apps/ai/rag.py`, `apps/ai/rag_duras.py`, `apps/ai/views.py` pour identifier la cause (mauvaise sélection doc, chunk insuffisant, prompt faible).
3. **Correction** : appliquer un changement isolé (ex : alias doc, heuristique scoring, guardrail prompt).
4. **Validation** : relancer les tests et enregistrer les sorties dans `tests/logs`.
5. **Journal** : mettre à jour `STATUS.txt` section « RAG » avec date, changement, résultat.
6. **Reboucle** tant que score < 100 %.

## 6. Checklist par itération
- [ ] Nettoyage cache (`python manage.py clearsessions` + `cache.clear()` si disponible).
- [ ] Tests Côtes de Duras (charges, densité, richesse, vendanges).
- [ ] Tests non-Duras (ex : Montreuil) pour vérifier absence de fuite.
- [ ] Vérifier log `ai.help` pour anomalies.
- [ ] Documenter résultat.

## 7. Extension future
- Ajouter de nouvelles fiches d'appellation dans la table §2.
- Automatiser la suite via `pytest -k rag` avec asserts.
- Brancher l'évaluation à une pipeline CI (GitHub Actions) pour rejet automatique si score < 100 %.

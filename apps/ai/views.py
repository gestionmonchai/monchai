from __future__ import annotations
import json
import hashlib
import re
import time
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache

from .ratelimit import check_rate_limit, RateLimitExceeded
from .ollama_client import ollama_generate, OllamaError
from .router import resolve_page_effective, BASES
from .intents import intent_for
from .rag import rag_engine

logger = logging.getLogger('ai.help')


@csrf_exempt  # TODO: sécuriser CSRF pour production si nécessaire
def help_assistant(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    # JSON only
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Corps JSON invalide'}, status=400)

    message = (data.get('message') or '').strip()
    # Unrestricted mode (chat-like)
    free_raw = str(data.get('free') or data.get('FREE') or data.get('mode') or '').lower()
    unrestricted = bool(
        getattr(settings, 'HELP_UNRESTRICTED', False)
        or free_raw in ('1', 'true', 'yes', 'y', 'free')
    )
    # Inputs from widget (accept several variants for robustness)
    effective_page = (data.get('effective_page') or '').strip()
    page_url = (data.get('page_url') or data.get('PAGE_URL') or '').strip()
    context_str = (data.get('context') or '').strip()
    page_hints = (data.get('pageHints') or data.get('PAGE_HINTS') or '').strip()
    doc_snippets = (data.get('docSnippets') or data.get('DOC_SNIPPETS') or '').strip()
    if not message:
        return JsonResponse({'error': 'message requis'}, status=400)

    # Rate limit (skip in unrestricted mode or if globally disabled)
    if not unrestricted:
        try:
            check_rate_limit(request)
        except RateLimitExceeded:
            return JsonResponse({'error': 'Trop de requêtes, réessayez plus tard.'}, status=429)

    # Helpers
    def _module_from_effective(url: str) -> str:
        for name, base in BASES.items():
            if url.startswith(base):
                return name
        return 'app'

    def _degraded_text(eff: str, steps: list[str] | None, see: str) -> str:
        mod = _module_from_effective(eff)
        title_map = {
            'clients': 'Aide rapide — Clients',
            'cuvees': 'Aide rapide — Cuvées',
            'ventes': 'Aide rapide — Ventes',
            'produits': 'Aide rapide — Produits',
            'stocks': 'Aide rapide — Stocks',
            'drm': 'Aide rapide — DRM',
            'app': 'Aide rapide — Mon‑Chai',
        }
        defaults = {
            'clients': [
                'Ouvrir Clients → Liste.',
                'Rechercher le client ou cliquer sur Nouveau client.',
                'Ouvrir la fiche et compléter Identité, Contacts, Adresses.',
                'Vérifier l’onglet Conditions (liste de prix, remise, TVA).',
                'Enregistrer.',
            ],
            'cuvees': [
                'Aller à Produits → Cuvées.',
                'Sélectionner la cuvée puis Éditer.',
                'Mettre à jour nom, millésime, appellation.',
                'Onglet Assemblage : ajuster les lots techniques.',
                'Onglet Conformité : vérifier les mentions légales, puis Enregistrer.',
            ],
            'ventes': [
                'Aller à Ventes → Commandes.',
                'Cliquer Nouveau devis/commande.',
                'Ajouter le client et les lignes (produits finis).',
                'Vérifier tarifs/remises et adresses de livraison/facturation.',
                'Enregistrer et valider si nécessaire.',
            ],
            'produits': [
                'Ouvrir Catalogue → Produits.',
                'Créer/éditer un produit fini et ses attributs.',
                'Renseigner tarifs, code barre/CRD si utile.',
                'Lier aux cuvées ou lots si pertinent.',
                'Enregistrer.',
            ],
            'stocks': [
                'Aller à Stocks.',
                'Consulter inventaires et mouvements.',
                'Créer un mouvement si nécessaire (entrée/sortie/transfert).',
                'Vérifier la cohérence des quantités.',
                'Enregistrer.',
            ],
            'drm': [
                'Aller à DRM.',
                'Ouvrir le brouillon du mois.',
                'Vérifier encours, entrées/sorties et stocks.',
                'Compléter les rubriques manquantes.',
                'Valider et exporter si nécessaire.',
            ],
            'app': [
                'Identifier le module concerné (Clients, Cuvées, Ventes, Produits, Stocks, DRM).',
                'Ouvrir le module depuis le menu.',
                'Chercher/Créer l’élément concerné.',
                'Compléter les informations puis enregistrer.',
            ],
        }
        title = title_map.get(mod, 'Aide rapide — Mon‑Chai')
        use_steps = steps if steps else defaults.get(mod, defaults['app'])
        body = [
            title,
            'Le service d’aide IA est momentanément indisponible. Voici une procédure rapide adaptée à votre page.',
        ]
        body.extend([f"{i+1}) {s}" for i, s in enumerate(use_steps[:6])])
        if see:
            body.append(f"Voir aussi : {see}")
        return "\n".join(body)

    def _extract_responses_only(s: str) -> str:
        """Return only the content after a 'RESPONSES:' label if present; otherwise the original text.
        Case-insensitive; tolerant to metadata prefix like 'file.md#anchor'.
        """
        try:
            m = re.search(r"(?is)\b(?:responses?|answers?|reponses?|réponses?)\s*:\s*(.*?)(?:\n[A-Z][A-Z0-9 _\-]{2,}\s*:|$)", s)
            if m:
                return m.group(1).strip()
        except Exception:
            pass
        return s

    # Call Ollama with graceful degradation
    # Contexte par défaut si non fourni (URL courante + referer)
    if not (effective_page or page_url or context_str):
        ref = request.META.get('HTTP_REFERER', '')
        context_str = f"URL: {request.path} | Referer: {ref}".strip()

    # Construire prompt conforme au template runtime (sans tokens spéciaux)
    url_value = (page_url or effective_page or context_str or request.path).strip()
    eff_value = (effective_page or url_value).strip()

    intent_match = (data.get('intentMatch') or data.get('INTENT_MATCH') or 'N/A').strip()
    intent_steps_raw = data.get('intentSteps') or data.get('INTENT_STEPS') or []
    if isinstance(intent_steps_raw, str):
        # Split on newlines if a single string is provided
        intent_steps_list = [s.strip(' -\t') for s in intent_steps_raw.split('\n') if s.strip()]
    else:
        intent_steps_list = [str(s).strip() for s in intent_steps_raw if str(s).strip()]
    see_also = (data.get('seeAlso') or data.get('SEE_ALSO') or '').strip()

    # Trim oversized inputs to reduce latency / token count (réduit de 50%)
    max_hints = int(getattr(settings, 'HELP_MAX_HINTS_CHARS', 400))
    max_docs = int(getattr(settings, 'HELP_MAX_DOCS_CHARS', 600))
    if page_hints:
        page_hints = page_hints[:max_hints]
    if doc_snippets:
        doc_snippets = doc_snippets[:max_docs]

    if unrestricted:
        # Minimal prompt: plain question only (terminal-like chat)
        prompt_text = message
    else:
        parts = []
        parts.append(f"PAGE_URL: {url_value}")
        parts.append(f"PAGE_EFFECTIVE: {eff_value}")
        parts.append("")
        parts.append(f"QUESTION: {message}")
        parts.append("")
        parts.append("PAGE_HINTS:")
        parts.append(page_hints or "N/A")
        parts.append("")
        parts.append("DOC_SNIPPETS:")
        parts.append(doc_snippets or "N/A")
        parts.append("")
        parts.append("INTENT_MATCH:")
        parts.append(intent_match or "N/A")
        parts.append("")
        parts.append("INTENT_STEPS:")
        if intent_steps_list:
            parts.extend([f"- {s}" for s in intent_steps_list][:6])
        else:
            parts.append("N/A")
        parts.append("")
        parts.append(f"SEE_ALSO: {see_also}")
        prompt_text = "\n".join(parts)

    # Cache lookup (per mode + message + page + intent + model)
    try:
        model_name = getattr(settings, 'HELP_MODEL', None) or getattr(settings, 'OLLAMA_MODEL', '')
        key_base = "|".join([
            'assistant' + ('_free' if unrestricted else ''), eff_value, message, intent_match,
            ",".join(intent_steps_list) if intent_steps_list else '', see_also, str(model_name)
        ])
        # Cache plus long pour réduire les appels Ollama
        cache_ttl = int(getattr(settings, 'HELP_CACHE_TTL', 300))  # 5 min au lieu de 1 min
        ckey = 'aihelp:' + hashlib.sha1(key_base.encode('utf-8')).hexdigest()
        cached = cache.get(ckey)
        if cached:
            return JsonResponse(cached)

        # Model selection
        if unrestricted:
            model_name = getattr(settings, 'HELP_FREE_MODEL', None) or getattr(settings, 'OLLAMA_MODEL', None)
            system_prompt = None
        else:
            # Prefer HELP_MODEL (custom Modelfile embeds system) to reduce prompt size
            _help_model = getattr(settings, 'HELP_MODEL', None)
            model_name = _help_model or getattr(settings, 'OLLAMA_MODEL', None)
            # Force usage of system prompt from settings to ensure strictness
            system_prompt = getattr(settings, 'HELP_SYSTEM_PROMPT', '') if not unrestricted else None
        t0 = time.perf_counter()
        answer = ollama_generate(
            prompt_text,
            model=model_name,
            system=system_prompt,
            options=getattr(settings, 'OLLAMA_OPTIONS', None),
            timeout=int(getattr(settings, 'HELP_TIMEOUT', 12)),  # Réduit de 20s à 12s
        )
        dur_ms = int((time.perf_counter() - t0) * 1000)
        # Sanitize and extract RESPONSES section if present
        answer = answer.replace('<|assistant|>', '').replace('<|user|>', '').replace('[CONTRAINDICE]', '').strip()
        answer = _extract_responses_only(answer)
        resp = {'answer': answer, 'page_effective': eff_value}
        try:
            logger.info("help_assistant ok model=%s ms=%d unrestricted=%s", str(model_name), dur_ms, str(unrestricted))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp)
    except OllamaError:
        text = _degraded_text(eff_value, intent_steps_list, see_also or eff_value)
        resp = {'answer': text, 'page_effective': eff_value, 'degraded': True}
        try:
            logger.warning("help_assistant degraded (ollama) model=%s", str(model_name))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp, status=200)
    except Exception:
        text = _degraded_text(eff_value, intent_steps_list, see_also or eff_value)
        resp = {'answer': text, 'page_effective': eff_value, 'degraded': True}
        try:
            logger.warning("help_assistant degraded (error) model=%s", str(model_name))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp, status=200)


@csrf_exempt  # POST-only proxy to Ollama with PAGE_EFFECTIVE routing
def help_query(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Corps JSON invalide'}, status=400)

    # Unrestricted mode (chat-like): bypass constraints for terminal-style discussion
    free_raw = str(data.get('free') or data.get('FREE') or data.get('mode') or '').lower()
    unrestricted = bool(
        getattr(settings, 'HELP_UNRESTRICTED', False)
        or free_raw in ('1', 'true', 'yes', 'y', 'free')
    )

    page_url = (data.get('page_url') or data.get('PAGE_URL') or '/').strip()
    question = (data.get('question') or data.get('QUESTION') or '').strip()
    
    # Handle history which might be a list of messages or a string
    history_raw = data.get('history') or data.get('HISTORY') or ''
    if isinstance(history_raw, list):
        # Convert list to string representation (join simple strings or repr objects)
        history_text = "\n".join(str(x) for x in history_raw).strip()
    else:
        history_text = str(history_raw).strip()

    if not question:
        return JsonResponse({'error': 'question requise'}, status=400)

    # Rate limit (skip in unrestricted mode or if globally disabled)
    if not unrestricted:
        try:
            check_rate_limit(request)
        except RateLimitExceeded:
            return JsonResponse({'error': 'Trop de requêtes, réessayez plus tard.'}, status=429)

    # Resolve effective page from dashboard/root
    page_effective = resolve_page_effective(page_url, question)
    if getattr(settings, 'DEBUG', False):
        try:
            q_prev = (question[:80] + "…") if len(question) > 80 else question
            print("[help]", {"path": page_url, "effective": page_effective, "question": q_prev})
        except Exception:
            pass

    # Optional RAG-light intent steps
    intent = intent_for(question)
    intent_steps = intent.get('steps') if intent else []
    see_also = intent.get('see_also') if intent else ''

    # RAG: Retrieve doc snippets
    rag_docs = rag_engine.retrieve(question)
    if rag_docs:
        # If we have specific docs, they might be more useful than intents for general Q&A
        pass

    def module_from_effective(url: str) -> str:
        for name, base in BASES.items():
            if url.startswith(base):
                return name
        return 'app'

    def degraded_answer() -> str:
        mod = module_from_effective(page_effective)
        title_map = {
            'clients': 'Aide rapide — Clients',
            'cuvees': 'Aide rapide — Cuvées',
            'ventes': 'Aide rapide — Ventes',
            'produits': 'Aide rapide — Produits',
            'stocks': 'Aide rapide — Stocks',
            'drm': 'Aide rapide — DRM',
            'app': 'Aide rapide — Mon‑Chai',
        }
        title = title_map.get(mod, 'Aide rapide — Mon‑Chai')
        if intent_steps:
            steps = intent_steps
        else:
            defaults = {
                'clients': [
                    'Ouvrir Clients → Liste.',
                    'Rechercher le client ou cliquer sur Nouveau client.',
                    'Ouvrir la fiche et compléter Identité, Contacts, Adresses.',
                    'Vérifier l’onglet Conditions (liste de prix, remise, TVA).',
                    'Enregistrer.',
                ],
                'cuvees': [
                    'Aller à Produits → Cuvées.',
                    'Sélectionner la cuvée puis Éditer.',
                    'Mettre à jour nom, millésime, appellation.',
                    'Onglet Assemblage : ajuster les lots techniques.',
                    'Onglet Conformité : vérifier les mentions légales, puis Enregistrer.',
                ],
                'ventes': [
                    'Aller à Ventes → Commandes.',
                    'Cliquer Nouveau devis/commande.',
                    'Ajouter le client et les lignes (produits finis).',
                    'Vérifier tarifs/remises et adresses de livraison/facturation.',
                    'Enregistrer et valider si nécessaire.',
                ],
                'produits': [
                    'Ouvrir Catalogue → Produits.',
                    'Créer/éditer un produit fini et ses attributs.',
                    'Renseigner tarifs, code barre/CRD si utile.',
                    'Lier aux cuvées ou lots si pertinent.',
                    'Enregistrer.',
                ],
                'stocks': [
                    'Aller à Stocks.',
                    'Consulter inventaires et mouvements.',
                    'Créer un mouvement si nécessaire (entrée/sortie/transfert).',
                    'Vérifier la cohérence des quantités.',
                    'Enregistrer.',
                ],
                'drm': [
                    'Aller à DRM.',
                    'Ouvrir le brouillon du mois.',
                    'Vérifier encours, entrées/sorties et stocks.',
                    'Compléter les rubriques manquantes.',
                    'Valider et exporter si nécessaire.',
                ],
                'app': [
                    'Identifier le module concerné (Clients, Cuvées, Ventes, Produits, Stocks, DRM).',
                    'Ouvrir le module depuis le menu.',
                    'Chercher/Créer l’élément concerné.',
                    'Compléter les informations puis enregistrer.',
                ],
            }
            steps = defaults.get(mod, defaults['app'])
        see = see_also or page_effective
        body = [
            title,
            'Le service d’aide IA est momentanément indisponible. Voici une procédure rapide adaptée à votre page.',
        ]
        body.extend([f"{i+1}) {s}" for i, s in enumerate(steps[:6])])
        if see:
            body.append(f"Voir aussi : {see}")
        return "\n".join(body)

    # Compose prompt
    if unrestricted:
        # En mode 'unrestricted' mais 'helpful', on injecte quand même le contexte s'il est pertinent
        parts = []
        if history_text:
            parts.append("HISTORIQUE CONVERSATION:")
            parts.append(history_text)
            parts.append("")
        if rag_docs:
            parts.append("CONTEXTE DOCUMENTAIRE:")
            parts.append(rag_docs)
            parts.append("")
        parts.append(question)
        prompt = "\n".join(parts)
    else:
        parts = [
            f"PAGE_URL: {page_url}",
            f"PAGE_EFFECTIVE: {page_effective}",
            "HISTORIQUE CONVERSATION:",
            history_text or "N/A",
            "",
            f"QUESTION: {question}",
            "",
            "DOC_SNIPPETS:",  # RAG injection point
            rag_docs or "N/A",
            "",
            "INTENT_STEPS:",
        ]
        if intent_steps:
            parts.extend([f"- {s}" for s in intent_steps][:6])
        else:
            parts.append("N/A")
        parts.extend(["", f"SEE_ALSO: {see_also}"])
        prompt = "\n".join(parts)

    # Cache lookup (per mode + question + effective page + model)
    try:
        model_name = getattr(settings, 'HELP_MODEL', None) or getattr(settings, 'OLLAMA_MODEL', '')
        # Include history hash in cache key to avoid serving context-blind answers
        import hashlib
        history_hash = hashlib.md5(history_text.encode('utf-8')).hexdigest() if history_text else 'nohist'
        
        key_base = "|".join(['query' + ('_free' if unrestricted else ''), page_effective, question, history_hash, ",".join(intent_steps) if intent_steps else '', str(model_name)])
        # Cache plus long pour réduire les appels Ollama
        cache_ttl = int(getattr(settings, 'HELP_CACHE_TTL', 300))  # 5 min au lieu de 1 min
        ckey = 'aihelp:' + hashlib.sha1(key_base.encode('utf-8')).hexdigest()
        cached = cache.get(ckey)
        if cached:
            return JsonResponse(cached)

        # Model selection
        if unrestricted:
            model_name = getattr(settings, 'HELP_FREE_MODEL', None) or getattr(settings, 'OLLAMA_MODEL', None)
            system_prompt = None
        else:
            _help_model = getattr(settings, 'HELP_MODEL', None)
            model_name = _help_model or getattr(settings, 'OLLAMA_MODEL', None)
            # Force usage of system prompt from settings to ensure strictness
            system_prompt = getattr(settings, 'HELP_SYSTEM_PROMPT', '') if not unrestricted else None

        t0 = time.perf_counter()
        text = ollama_generate(
            prompt,
            model=model_name,
            system=system_prompt,
            options=getattr(settings, 'OLLAMA_OPTIONS', None),
            timeout=int(getattr(settings, 'HELP_TIMEOUT', 12)),  # Réduit de 20s à 12s
        )
        dur_ms = int((time.perf_counter() - t0) * 1000)
        # Sanitize a bit and extract RESPONSES section if present
        text = text.replace('<|assistant|>', '').replace('<|user|>', '').replace('[CONTRAINDICE]', '').strip()
        def _extract_responses_only(s: str) -> str:
            try:
                m = re.search(r"(?is)\b(?:responses?|answers?|reponses?|réponses?)\s*:\s*(.*?)(?:\n[A-Z][A-Z0-9 _\-]{2,}\s*:|$)", s)
                if m:
                    return m.group(1).strip()
            except Exception:
                pass
            return s
        text = _extract_responses_only(text)
        resp = {
            'text': text,
            'page_effective': page_effective,
            'see_also': see_also,
        }
        try:
            logger.info("help_query ok model=%s ms=%d unrestricted=%s", str(model_name), dur_ms, str(unrestricted))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp)
    except OllamaError:
        # Degraded mode: return actionable fallback instead of 502
        text = degraded_answer()
        resp = {
            'text': text,
            'page_effective': page_effective,
            'see_also': see_also or page_effective,
            'degraded': True,
        }
        try:
            logger.warning("help_query degraded (ollama) model=%s", str(model_name))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp, status=200)
    except Exception:
        # Unknown error: still try to help with degraded mode
        text = degraded_answer()
        resp = {
            'text': text,
            'page_effective': page_effective,
            'see_also': see_also or page_effective,
            'degraded': True,
        }
        try:
            logger.warning("help_query degraded (error) model=%s", str(model_name))
        except Exception:
            pass
        cache.set(ckey, resp, cache_ttl)
        return JsonResponse(resp, status=200)

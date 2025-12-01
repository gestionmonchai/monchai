from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import List, Tuple
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.db.models import Q

from .models import LotTechnique, MouvementLot, Assemblage, AssemblageLigne
from .models import generate_lot_tech_code, generate_assemblage_code
from .services_cost import get_cmp_lot, set_snapshot_cmp_lot
from .services_stock import move_vrac
from apps.referentiels.models import Cuvee


@method_decorator(login_required, name='dispatch')
class AssemblageWizardView(View):
    template_step1 = "production/assemblage_wizard_step1.html"
    template_step2 = "production/assemblage_wizard_step2.html"
    template_step3 = "production/assemblage_wizard_step3.html"

    def _token(self, request):
        tok = request.session.get("asm_token")
        if not tok:
            tok = get_random_string(20)
            request.session["asm_token"] = tok
        return tok

    def get_org(self, request):
        return getattr(request, 'current_org', None)

    def get(self, request):
        step = int(request.GET.get("step", 1) or 1)
        org = self.get_org(request)
        
        if step == 1:
            # ÉTAPE 1 : Sélection des lots sources
            # Lots disponibles (même org), actifs et avec du volume
            lots_qs = LotTechnique.objects.none()
            if org:
                lots_qs = (LotTechnique.objects
                          .select_related('cuvee')
                          .filter(cuvee__organization=org, volume_l__gt=0)
                          .exclude(statut='epuise')
                          .order_by('-created_at'))
            
            # Pré-sélection param (ex: source depuis fiche lot)
            preselect = request.GET.getlist('source') or request.GET.getlist('sources')
            
            return render(request, self.template_step1, {
                "lots": lots_qs,
                "step": 1,
                "preselect_ids": set(preselect),
            })
            
        elif step == 2:
            # ÉTAPE 2 : Saisie des volumes
            source_ids = request.GET.getlist("sources")
            if len(source_ids) < 1: # On autorise 1 seul lot (ex: correction/dilution) ? Non, assemblage implique >1 souvent, mais techniquement possible
                messages.warning(request, "Veuillez sélectionner au moins 2 lots pour un assemblage.")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")
                
            sources_qs = LotTechnique.objects.none()
            if org:
                sources_qs = LotTechnique.objects.filter(cuvee__organization=org, id__in=source_ids).order_by('code')
                
            return render(request, self.template_step2, {
                "sources": sources_qs,
                "step": 2,
            })
            
        else:
            # ÉTAPE 3 : Destination
            # On doit avoir des volumes en session ou via POST step 2 (mais ici c'est GET step 3)
            # Idéalement on redirige si pas de session
            if not request.session.get("asm_pairs"):
                messages.warning(request, "Session expirée ou invalide. Veuillez recommencer.")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")

            # Récupérer les lots cibles potentiels (existants)
            target_lots = LotTechnique.objects.none()
            cuvees = Cuvee.objects.none()
            
            if org:
                # Lots cibles : 'en_cours' seulement, même org
                target_lots = LotTechnique.objects.filter(
                    cuvee__organization=org, 
                    statut='en_cours'
                ).order_by('-created_at')[:200]
                
                # Cuvées pour nouveau lot : même org
                cuvees = Cuvee.objects.filter(organization=org).order_by('name')[:200]

            # Estimation campagne par défaut (Majorité des lots sources)
            default_campagne = ""
            try:
                pairs = request.session.get("asm_pairs", [])
                src_ids = [p[0] for p in pairs]
                if src_ids:
                    sources = LotTechnique.objects.filter(id__in=src_ids)
                    camps = [l.campagne for l in sources if l.campagne]
                    if camps:
                        # Prendre la campagne la plus fréquente
                        default_campagne = Counter(camps).most_common(1)[0][0]
            except Exception:
                pass

            return render(request, self.template_step3, {
                "step": 3,
                "asm_token": self._token(request),
                "cuvees": cuvees,
                "target_lots": target_lots,
                "default_campagne": default_campagne,
            })

    @transaction.atomic
    def post(self, request):
        step = int(request.POST.get("step", 1) or 1)
        org = self.get_org(request)
        if not org:
             messages.error(request, "Aucune organisation active.")
             return redirect("production:production_home")

        if step == 1:
            ids = request.POST.getlist("sources")
            if len(ids) < 2:
                messages.error(request, "Sélectionnez au moins 2 lots sources")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")
            
            # Construction query string pour step 2
            q = "&".join([f"sources={x}" for x in ids])
            return redirect(f"{reverse('production:assemblage_wizard')}?step=2&{q}")

        elif step == 2:
            source_ids = request.POST.getlist("source_id")
            volum_strs = request.POST.getlist("volume_l")
            
            pairs: List[Tuple[str, Decimal]] = []
            total = Decimal("0")
            
            # Validation des entrées
            for sid, v in zip(source_ids, volum_strs):
                try:
                    vol = Decimal(str(v or "0")).quantize(Decimal('0.01'))
                except (InvalidOperation, Exception):
                    vol = Decimal('0')
                
                if vol < 0:
                    return self._render_step2_error(request, org, "Les volumes ne peuvent pas être négatifs.", source_ids)
                
                if vol > 0:
                    pairs.append((sid, vol))
                    total += vol
            
            if total <= 0:
                return self._render_step2_error(request, org, "La somme des volumes doit être supérieure à 0.", source_ids)

            # Vérification disponibilité stock (Lock)
            # On lock les lots sources pour s'assurer que le volume est dispo
            src_ids_clean = [p[0] for p in pairs]
            locked_lots = list(LotTechnique.objects.select_for_update().filter(
                cuvee__organization=org, 
                id__in=src_ids_clean
            ).order_by('id'))
            
            dispo_map = {str(l.id): l.volume_net_calculated() for l in locked_lots}
            
            for sid, vol in pairs:
                limit = dispo_map.get(str(sid), Decimal('0'))
                if vol > limit:
                     return self._render_step2_error(request, org, f"Volume demandé ({vol} L) supérieur au disponible ({limit} L) pour l'un des lots.", source_ids)

            # Tout est bon, on stocke en session
            request.session["asm_pairs"] = [(str(s), str(v)) for s, v in pairs]
            return redirect(f"{reverse('production:assemblage_wizard')}?step=3")

        elif step == 3:
            # Validation Token (Idempotence)
            token = request.POST.get("asm_token")
            if token != request.session.get("asm_token"):
                messages.error(request, "Session expirée ou formulaire déjà soumis.")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")

            # Récupération données session
            raw_pairs = request.session.get("asm_pairs", [])
            if not raw_pairs:
                messages.error(request, "Aucune donnée d'assemblage trouvée.")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")
                
            pairs: List[Tuple[str, Decimal]] = [(sid, Decimal(v)) for sid, v in raw_pairs]
            src_ids = [sid for sid, _ in pairs]

            # Reload et Lock sources
            sources = list(LotTechnique.objects.select_for_update().filter(
                cuvee__organization=org, 
                id__in=src_ids
            ).order_by('id'))

            # Calculs Volumes et CMP pondéré
            sum_v = Decimal('0')
            sum_vxcmp = Decimal('0')
            
            # Map pour accès rapide
            sources_map = {str(s.id): s for s in sources}
            
            valid_sources = [] # Liste (Lot, vol)
            
            for sid, vol in pairs:
                lot = sources_map.get(str(sid))
                if not lot:
                    continue # Should not happen if org filter is consistent
                
                # Re-vérif dispo ultime
                if vol > lot.volume_net_calculated():
                     messages.error(request, f"Le volume disponible pour {lot.code} a changé entre-temps.")
                     return redirect(f"{reverse('production:assemblage_wizard')}?step=2&" + "&".join([f"sources={s}" for s in src_ids]))

                cmp_s = Decimal(get_cmp_lot(lot.id) or 0)
                sum_v += vol
                sum_vxcmp += (cmp_s * vol)
                valid_sources.append((lot, vol))

            if sum_v <= 0:
                messages.error(request, "Volume total nul.")
                return redirect(f"{reverse('production:assemblage_wizard')}?step=1")

            cmp_target = (sum_vxcmp / sum_v).quantize(Decimal('0.0001'))

            # Gestion du Lot Cible
            target_mode = request.POST.get("target_mode", "new")
            contenant = (request.POST.get("contenant") or "Cuve assemblage").strip()
            
            target_lot = None
            
            if target_mode == "existing":
                target_id = request.POST.get("target_id")
                if not target_id:
                    messages.error(request, "Veuillez sélectionner un lot cible existant.")
                    return redirect(f"{reverse('production:assemblage_wizard')}?step=3")
                    
                target_lot = get_object_or_404(
                    LotTechnique.objects.select_for_update(), 
                    cuvee__organization=org, 
                    id=target_id
                )
            else:
                # Creation nouveau lot
                cuvee_id = request.POST.get("cuvee_id")
                if not cuvee_id:
                    messages.error(request, "Veuillez sélectionner une cuvée pour le nouveau lot.")
                    return redirect(f"{reverse('production:assemblage_wizard')}?step=3")
                
                cuvee_obj = get_object_or_404(Cuvee, organization=org, id=cuvee_id)
                
                # Détermination campagne
                camp = request.POST.get("campagne_manuelle")
                if not camp:
                    # Fallback logique millésime
                    try:
                        y = int(getattr(getattr(cuvee_obj, 'vintage', None), 'year', 0) or 0)
                        if y > 0:
                            camp = f"{y}-{y+1}"
                    except: pass
                
                if not camp:
                     from django.utils import timezone as _tz
                     y = _tz.now().year
                     camp = f"{y}-{y+1}"
                     
                code = generate_lot_tech_code(camp)
                
                target_lot = LotTechnique.objects.create(
                    code=code,
                    campagne=camp,
                    contenant=contenant,
                    volume_l=Decimal('0.00'),
                    statut='en_cours',
                    cuvee=cuvee_obj,
                )

            # Création de l'Assemblage (Ticket)
            asm = Assemblage.objects.create(
                code=generate_assemblage_code(target_lot.campagne),
                campagne=target_lot.campagne,
                result_lot=target_lot,
                notes=request.POST.get("notes", "")
            )

            # Mouvements et Lignes
            for lot_src, vol in valid_sources:
                # Ligne assemblage
                AssemblageLigne.objects.create(assemblage=asm, lot_source=lot_src, volume_l=vol)
                
                # Mouvement Sortie
                MouvementLot.objects.create(
                    lot=lot_src, 
                    type='ASSEMBLAGE_OUT', 
                    volume_l=vol, 
                    meta={"wizard": True, "assemblage_id": str(asm.id)},
                    author=request.user
                )
                
                # Update Stock physique (Service)
                try:
                    move_vrac(lottech=lot_src, delta_l=-vol, reason='ASSEMBLAGE_OUT', user=request.user)
                except Exception:
                    pass # Log error?

                # Update Lot Source (Denorm)
                lot_src.volume_l = (lot_src.volume_l or Decimal('0')) - vol
                if lot_src.volume_l <= 0.01: # Tolérance zéro
                    lot_src.volume_l = Decimal('0')
                    lot_src.statut = 'epuise'
                lot_src.save(update_fields=['volume_l', 'statut'])

            # Mouvement Entrée Cible
            MouvementLot.objects.create(
                lot=target_lot, 
                type='ASSEMBLAGE_IN', 
                volume_l=sum_v, 
                meta={"wizard": True, "assemblage_id": str(asm.id)},
                author=request.user
            )
            
            try:
                move_vrac(lottech=target_lot, delta_l=sum_v, reason='ASSEMBLAGE_IN', user=request.user)
            except Exception:
                pass

            # Update Lot Cible (Denorm)
            target_lot.volume_l = (target_lot.volume_l or Decimal('0')) + sum_v
            if target_lot.contenant != contenant: # Update contenant if specified
                 target_lot.contenant = contenant
            target_lot.save()

            # Snapshot CMP Cible
            set_snapshot_cmp_lot(target_lot.id, cmp_target)

            # Clean session
            request.session.pop("asm_token", None)
            request.session.pop("asm_pairs", None)

            messages.success(request, f"Assemblage {asm.code} enregistré avec succès.")
            
            return redirect('production:lot_tech_detail', pk=target_lot.id)

        messages.error(request, "Étape inconnue")
        return redirect(f"{reverse('production:assemblage_wizard')}?step=1")

    def _render_step2_error(self, request, org, error: str, source_ids: List[str]):
        sources = LotTechnique.objects.none()
        if org:
            sources = LotTechnique.objects.filter(cuvee__organization=org, id__in=source_ids).order_by('code')
        return render(request, self.template_step2, {"sources": sources, "step": 2, "error": error})


@method_decorator(login_required, name='dispatch')
class AssemblageDetailView(View):
    template_name = 'production/assemblage_detail.html'

    def get(self, request, pk):
        asm = get_object_or_404(Assemblage, pk=pk)
        lignes = asm.lignes.select_related('lot_source').all()
        return render(request, self.template_name, {
            'assemblage': asm,
            'lignes': lignes,
            'result_lot': asm.result_lot,
            'page_title': f'Assemblage {asm.code}',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Assemblages', 'url': None},
                {'name': asm.code, 'url': None},
            ]
        })

from __future__ import annotations
from datetime import date as dt_date
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.urls import reverse

from apps.accounts.decorators import require_membership
from apps.referentiels.models import Parcelle
from .models_parcelle_journal import ParcelleOperationType
from .services_journal import log_parcelle_op


OP_META = {
    "traitement": {"label": "Traitement phyto", "icon": "bi-spray"},
    "taille": {"label": "Taille", "icon": "bi-scissors"},
    "travail_sol": {"label": "Travail du sol", "icon": "bi-shovel"},
    "palissage": {"label": "Palissage / Liage", "icon": "bi-crop"},
    "effeuillage": {"label": "Effeuillage", "icon": "bi-leaf"},
    "fertilisation": {"label": "Fertilisation / Amendements", "icon": "bi-droplet"},
    "irrigation": {"label": "Irrigation", "icon": "bi-water"},
    "autre": {"label": "Autre intervention", "icon": "bi-tools"},
}


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='editor'), name='dispatch')
class ParcelleQuickOpCreateView(View):
    template_name = "viticulture/parcelle_quick_op_form.html"

    def get_meta(self, code: str):
        meta = OP_META.get(code, {"label": code, "icon": "bi-gear"})
        return meta

    def get(self, request, pk: int, code: str):
        organization = request.current_org
        parcelle = get_object_or_404(Parcelle, pk=pk, organization=organization)
        # Vérifier type existant
        pot = get_object_or_404(ParcelleOperationType, code=code)
        ctx = {
            "page_title": f"{self.get_meta(code)['label']} — {parcelle.nom}",
            "parcelle": parcelle,
            "code": code,
            "meta": self.get_meta(code),
            "today": dt_date.today().isoformat(),
            "organization": organization,
            "form": {"surface_ha": str(parcelle.surface or "")},
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk: int, code: str):
        organization = request.current_org
        parcelle = get_object_or_404(Parcelle, pk=pk, organization=organization)
        # Validation simple
        date_str = (request.POST.get("date") or "").strip()
        resume = (request.POST.get("resume") or "").strip()
        notes = (request.POST.get("notes") or "").strip()
        surface_ha = (request.POST.get("surface_ha") or "").strip()
        cout_mo = (request.POST.get("cout_mo_eur") or "").strip()
        cout_ms = (request.POST.get("cout_matiere_eur") or "").strip()
        rangs = (request.POST.get("rangs") or "").strip()
        produit = (request.POST.get("produit") or "").strip()
        dose = (request.POST.get("dose") or "").strip()

        errors = []
        if not date_str:
            errors.append("La date est obligatoire.")
        # Créer un résumé auto si traitement
        if code == "traitement" and not resume:
            if produit or dose:
                resume = f"Traitement: {produit}{(' ' + dose) if dose else ''}".strip()
        if not resume:
            errors.append("Le résumé est obligatoire (au moins quelques mots).")

        # Parse date
        date_obj = None
        try:
            date_obj = dt_date.fromisoformat(date_str)
        except Exception:
            errors.append("Date invalide.")

        if errors:
            for e in errors:
                messages.error(request, e)
            ctx = {
                "page_title": f"{self.get_meta(code)['label']} — {parcelle.nom}",
                "parcelle": parcelle,
                "code": code,
                "meta": self.get_meta(code),
                "today": date_str or dt_date.today().isoformat(),
                "organization": organization,
                "form": request.POST,
            }
            return render(request, self.template_name, ctx)

        # Création entrée journal
        try:
            log_parcelle_op(
                org=organization,
                parcelle=parcelle,
                op_code=code,
                date=date_obj,
                resume=resume,
                notes=notes,
                surface_ha=surface_ha or None,
                rangs=rangs,
                cout_mo_eur=cout_mo or None,
                cout_matiere_eur=cout_ms or None,
            )
            messages.success(request, "Intervention enregistrée dans le journal.")
            return redirect("viticulture:parcelle_journal", pk=parcelle.pk)
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement: {e}")
            ctx = {
                "page_title": f"{self.get_meta(code)['label']} — {parcelle.nom}",
                "parcelle": parcelle,
                "code": code,
                "meta": self.get_meta(code),
                "today": date_str or dt_date.today().isoformat(),
                "organization": organization,
                "form": request.POST,
            }
            return render(request, self.template_name, ctx)

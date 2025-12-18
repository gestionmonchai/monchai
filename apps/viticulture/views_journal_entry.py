"""
Vues pour la gestion des entrées du journal cultural (détail, modification, suppression)
"""
from __future__ import annotations
from datetime import date as dt_date
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse

from apps.accounts.decorators import require_membership
from apps.referentiels.models import Parcelle
from .models_parcelle_journal import ParcelleJournalEntry, ParcelleOperationType


OP_META = {
    "traitement": {"label": "Traitement phyto", "icon": "bi-spray", "color": "warning"},
    "taille": {"label": "Taille", "icon": "bi-scissors", "color": "success"},
    "travail_sol": {"label": "Travail du sol", "icon": "bi-tools", "color": "secondary"},
    "palissage": {"label": "Palissage / Liage", "icon": "bi-diagram-3", "color": "info"},
    "effeuillage": {"label": "Effeuillage", "icon": "bi-leaf", "color": "success"},
    "fertilisation": {"label": "Fertilisation / Amendements", "icon": "bi-droplet-half", "color": "dark"},
    "irrigation": {"label": "Irrigation", "icon": "bi-moisture", "color": "info"},
    "rognage": {"label": "Rognage", "icon": "bi-scissors", "color": "success"},
    "observation": {"label": "Observation", "icon": "bi-eye", "color": "secondary"},
    "autre": {"label": "Autre intervention", "icon": "bi-gear", "color": "light"},
}


def get_op_meta(code: str) -> dict:
    """Retourne les métadonnées d'affichage pour un type d'opération."""
    return OP_META.get(code, {"label": code.replace("_", " ").title(), "icon": "bi-calendar-event", "color": "primary"})


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='viewer'), name='dispatch')
class JournalEntryDetailView(View):
    """Vue de détail d'une entrée du journal cultural."""
    template_name = "viticulture/journal_entry_detail.html"
    
    def get(self, request, pk):
        organization = request.current_org
        entry = get_object_or_404(
            ParcelleJournalEntry.objects.select_related('parcelle', 'op_type', 'source_ct'),
            pk=pk,
            organization=organization
        )
        
        meta = get_op_meta(entry.op_type.code)
        
        # Vérifier si l'entrée a un objet source lié (ex: VendangeReception)
        source_url = None
        source_label = None
        if entry.source_ct and entry.source_id:
            model_name = entry.source_ct.model
            if model_name == 'vendangereception':
                source_url = f"/production/vendanges/{entry.source_id}/"
                source_label = "Voir la fiche vendange"
            elif model_name == 'lottechnique':
                source_url = f"/production/lots-techniques/{entry.source_id}/"
                source_label = "Voir le lot technique"
            elif model_name == 'parcelleoperation':
                # Opération parcelle - pas de page dédiée, afficher ici
                source_label = "Opération parcelle"
        
        ctx = {
            "page_title": f"{entry.op_type.label} — {entry.parcelle.nom}",
            "entry": entry,
            "parcelle": entry.parcelle,
            "meta": meta,
            "organization": organization,
            "source_url": source_url,
            "source_label": source_label,
            "breadcrumb_items": [
                {"name": "Production", "url": "/production/"},
                {"name": "Journal cultural", "url": reverse("production:journal_cultural")},
                {"name": f"{entry.op_type.label} - {entry.date.strftime('%d/%m/%Y')}", "url": None},
            ],
        }
        return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='editor'), name='dispatch')
class JournalEntryUpdateView(View):
    """Vue de modification d'une entrée du journal cultural."""
    template_name = "viticulture/journal_entry_form.html"
    
    def get(self, request, pk):
        organization = request.current_org
        entry = get_object_or_404(
            ParcelleJournalEntry.objects.select_related('parcelle', 'op_type'),
            pk=pk,
            organization=organization
        )
        
        meta = get_op_meta(entry.op_type.code)
        op_types = ParcelleOperationType.objects.all().order_by('order', 'label')
        
        ctx = {
            "page_title": f"Modifier : {entry.op_type.label} — {entry.parcelle.nom}",
            "entry": entry,
            "parcelle": entry.parcelle,
            "meta": meta,
            "op_types": op_types,
            "is_edit": True,
            "organization": organization,
            "breadcrumb_items": [
                {"name": "Production", "url": "/production/"},
                {"name": "Journal cultural", "url": reverse("production:journal_cultural")},
                {"name": "Modifier", "url": None},
            ],
        }
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk):
        organization = request.current_org
        entry = get_object_or_404(
            ParcelleJournalEntry.objects.select_related('parcelle', 'op_type'),
            pk=pk,
            organization=organization
        )
        
        # Récupérer les données du formulaire
        date_str = (request.POST.get("date") or "").strip()
        op_type_code = (request.POST.get("op_type") or entry.op_type.code).strip()
        resume = (request.POST.get("resume") or "").strip()
        notes = (request.POST.get("notes") or "").strip()
        surface_ha = (request.POST.get("surface_ha") or "").strip()
        rangs = (request.POST.get("rangs") or "").strip()
        cout_mo = (request.POST.get("cout_mo_eur") or "").strip()
        cout_ms = (request.POST.get("cout_matiere_eur") or "").strip()
        
        errors = []
        
        # Validation
        if not date_str:
            errors.append("La date est obligatoire.")
        
        date_obj = None
        try:
            date_obj = dt_date.fromisoformat(date_str)
        except Exception:
            errors.append("Date invalide.")
        
        if not resume:
            errors.append("Le résumé est obligatoire.")
        
        # Vérifier le type d'opération
        op_type = None
        try:
            op_type = ParcelleOperationType.objects.get(code=op_type_code)
        except ParcelleOperationType.DoesNotExist:
            errors.append("Type d'opération invalide.")
        
        if errors:
            for e in errors:
                messages.error(request, e)
            meta = get_op_meta(entry.op_type.code)
            op_types = ParcelleOperationType.objects.all().order_by('order', 'label')
            ctx = {
                "page_title": f"Modifier : {entry.op_type.label} — {entry.parcelle.nom}",
                "entry": entry,
                "parcelle": entry.parcelle,
                "meta": meta,
                "op_types": op_types,
                "is_edit": True,
                "organization": organization,
                "form": request.POST,
            }
            return render(request, self.template_name, ctx)
        
        # Mise à jour de l'entrée
        try:
            entry.date = date_obj
            entry.op_type = op_type
            entry.resume = resume
            entry.notes = notes
            entry.rangs = rangs
            
            # Conversion des valeurs numériques
            if surface_ha:
                try:
                    entry.surface_ha = Decimal(surface_ha.replace(",", "."))
                except Exception:
                    entry.surface_ha = None
            else:
                entry.surface_ha = None
            
            if cout_mo:
                try:
                    entry.cout_mo_eur = Decimal(cout_mo.replace(",", "."))
                except Exception:
                    entry.cout_mo_eur = None
            else:
                entry.cout_mo_eur = None
            
            if cout_ms:
                try:
                    entry.cout_matiere_eur = Decimal(cout_ms.replace(",", "."))
                except Exception:
                    entry.cout_matiere_eur = None
            else:
                entry.cout_matiere_eur = None
            
            # Recalculer le coût total
            total = Decimal('0')
            if entry.cout_mo_eur:
                total += entry.cout_mo_eur
            if entry.cout_matiere_eur:
                total += entry.cout_matiere_eur
            entry.cout_total_eur = total if total > 0 else None
            
            entry.save()
            
            messages.success(request, "L'intervention a été modifiée avec succès.")
            return redirect("viticulture:journal_entry_detail", pk=entry.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {e}")
            meta = get_op_meta(entry.op_type.code)
            op_types = ParcelleOperationType.objects.all().order_by('order', 'label')
            ctx = {
                "page_title": f"Modifier : {entry.op_type.label} — {entry.parcelle.nom}",
                "entry": entry,
                "parcelle": entry.parcelle,
                "meta": meta,
                "op_types": op_types,
                "is_edit": True,
                "organization": organization,
                "form": request.POST,
            }
            return render(request, self.template_name, ctx)


@method_decorator(login_required, name='dispatch')
@method_decorator(require_membership(role_min='editor'), name='dispatch')
class JournalEntryDeleteView(View):
    """Vue de suppression d'une entrée du journal cultural."""
    
    def post(self, request, pk):
        organization = request.current_org
        entry = get_object_or_404(
            ParcelleJournalEntry.objects.select_related('parcelle'),
            pk=pk,
            organization=organization
        )
        
        parcelle = entry.parcelle
        entry_label = f"{entry.op_type.label} du {entry.date.strftime('%d/%m/%Y')}"
        
        try:
            entry.delete()
            messages.success(request, f"L'intervention « {entry_label} » a été supprimée.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {e}")
            return redirect("viticulture:journal_entry_detail", pk=pk)
        
        # Redirection vers le journal de la parcelle ou le journal global
        next_url = request.POST.get("next") or request.GET.get("next") or ""
        if next_url:
            return redirect(next_url)
        
        return redirect("viticulture:parcelle_journal", pk=parcelle.pk)

"""
Vues pour les paramètres - Roadmap 09
Pages /settings/billing et /settings/general avec mise à jour automatique checklist
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .decorators import require_membership
from .utils import checklist_service, ChecklistService
from .forms import OrganizationBillingForm, OrganizationGeneralForm, OrgBillingForm, OrgSettingsForm
from .models import OrgSettings


@require_membership(role_min='admin')
@require_http_methods(["GET", "POST"])
def billing_settings(request):
    """
    Paramètres de facturation - Roadmap 11
    Gestion des informations légales, fiscales et de facturation
    """
    organization = request.current_org
    
    # Obtenir ou créer l'enregistrement de facturation
    try:
        billing = organization.billing
    except:
        from .models import OrgBilling
        billing = OrgBilling.objects.create(
            organization=organization,
            legal_name='',
            billing_address_line1='',
            billing_postal_code='',
            billing_city='',
            billing_country='France',
            vat_status='not_subject_to_vat'
        )
    
    if request.method == 'POST':
        form = OrgBillingForm(request.POST, instance=billing)
        if form.is_valid():
            billing = form.save()
            
            # Mise à jour automatique de la checklist selon roadmap 11
            if billing.has_complete_company_info():
                checklist_service.checklist_update(organization, 'company_info', True)
            if billing.has_complete_tax_info():
                checklist_service.checklist_update(organization, 'taxes', True)
            
            messages.success(request, 'Informations de facturation mises à jour avec succès.')
            return redirect('auth:billing_settings')
    else:
        form = OrgBillingForm(instance=billing)
    
    context = {
        'form': form,
        'billing': billing,
        'organization': organization,
        'page_title': 'Informations de facturation'
    }
    
    return render(request, 'accounts/settings/billing.html', context)


@require_membership(role_min='admin')
@require_http_methods(["GET", "POST"])
def general_settings(request):
    """
    Paramètres généraux - Roadmap 12
    Gestion devise, formats et CGV avec mise à jour checklist
    """
    organization = request.current_org
    settings, created = OrgSettings.objects.get_or_create(organization=organization)
    
    if request.method == 'POST':
        form = OrgSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            # Nettoyer ancien fichier si remplacé
            old_file = None
            if settings.terms_file and form.cleaned_data.get('terms_file'):
                old_file = settings.terms_file
            
            settings = form.save()
            
            # Supprimer ancien fichier
            if old_file and old_file != settings.terms_file:
                old_file.delete(save=False)
            
            # Mettre à jour la checklist selon roadmap 12
            checklist_service = ChecklistService()
            
            # currency_format = done si devise et formats définis
            if settings.currency and settings.date_format and settings.number_format:
                checklist_service.checklist_update(organization, 'currency_format', 'done')
            
            # terms = done si CGV définies (URL ou fichier)
            if settings.has_terms():
                checklist_service.checklist_update(organization, 'terms', 'done')
            
            messages.success(request, 'Les paramètres généraux ont été enregistrés avec succès.')
            return redirect('auth:general_settings')
    else:
        form = OrgSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'organization': organization,
        'format_preview': settings.get_format_preview(),
        'page_title': 'Paramètres généraux'
    }
    
    return render(request, 'accounts/general_settings.html', context)

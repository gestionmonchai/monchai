from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import require_membership
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
from datetime import date as dt_date

from .models import (
    Cuvee as ViticultureCuvee,
    UnitOfMeasure,
    Appellation,
    Vintage,
    CuveeDetail,
    VineyardPlot,
    GrapeVariety,
)
from apps.referentiels.models import Unite


@login_required
@require_membership()
def cuvee_change(request, pk):
    """Page de modification d'une cuvée (même formulaire que la création, préchargé)."""
    organization = request.current_org
    cuvee = get_object_or_404(ViticultureCuvee, id=pk, organization=organization)

    # Référentiels pour le template
    appellations = Appellation.objects.filter(organization=organization, is_active=True)
    vintages = Vintage.objects.filter(organization=organization, is_active=True)
    parcelles = VineyardPlot.objects.filter(organization=organization, is_active=True)
    cepages = GrapeVariety.objects.filter(organization=organization)
    current_year = dt_date.today().year
    suggested_vintages = [y for y in range(current_year + 1, current_year - 10, -1)]
    baseline_appellations = [
        'Bordeaux AOC', 'Côtes du Rhône AOC', "IGP Pays d'Oc", 'VSIG',
    ]
    existing_names = list(appellations.values_list('name', flat=True)[:10])
    appellation_suggestions = list(dict.fromkeys(existing_names + baseline_appellations))

    # Initial à partir de l'objet existant
    initial = {
        'name': cuvee.name or '',
        'code': cuvee.code or '',
        'vintage_year': str(cuvee.vintage.year) if cuvee.vintage else '',
        'appellation_name': cuvee.appellation.name if cuvee.appellation else '',
        'is_active': cuvee.is_active,
    }
    if cuvee.default_uom:
        initial['default_uom_id'] = str(cuvee.default_uom.id)
        try:
            lu_match = Unite.objects.filter(organization=organization, symbole__iexact=cuvee.default_uom.code).first()
            if lu_match:
                initial['default_unit_id'] = str(lu_match.id)
        except Exception:
            pass
    # Prefill with detail fields if present
    try:
        detail = CuveeDetail.objects.filter(cuvee=cuvee).first()
        if detail:
            initial.update({
                'type_vin': detail.type_vin or '',
                'statut': detail.statut or '',
                'volume_total_hl': str(detail.volume_total_hl or ''),
                'date_vendange_debut': detail.date_vendange_debut.isoformat() if detail.date_vendange_debut else '',
                'date_vendange_fin': detail.date_vendange_fin.isoformat() if detail.date_vendange_fin else '',
                'methode_vendange': detail.methode_vendange or '',
                'methode_vinification': detail.methode_vinification or '',
                'duree_elevage_mois': str(detail.duree_elevage_mois or ''),
                'contenant_elevage': detail.contenant_elevage or '',
                'degre_alcool_potentiel': str(detail.degre_alcool_potentiel or ''),
                'degre_alcool_final': str(detail.degre_alcool_final or ''),
                'sucres_residuels': str(detail.sucres_residuels or ''),
                'ph': str(detail.ph or ''),
                'acidite_totale': str(detail.acidite_totale or ''),
                'so2_libre': str(detail.so2_libre or ''),
                'so2_total': str(detail.so2_total or ''),
                'prix_revient_estime': str(detail.prix_revient_estime or ''),
                'certifications': detail.certifications or '',
                'notes_internes': detail.notes_internes or '',
                'notes_degustation': detail.notes_degustation or '',
            })
    except Exception:
        pass

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        appellation_name = (request.POST.get('appellation_name') or '').strip()
        vintage_year = (request.POST.get('vintage_year') or '').strip()
        default_uom_id = (request.POST.get('default_uom') or request.POST.get('default_unit') or None)
        is_active = bool(request.POST.get('is_active'))
        # Détails
        type_vin = request.POST.get('type_vin') or None
        statut = request.POST.get('statut') or None
        volume_total_hl = request.POST.get('volume_total_hl') or None
        date_vendange_debut = request.POST.get('date_vendange_debut') or None
        date_vendange_fin = request.POST.get('date_vendange_fin') or None
        methode_vendange = request.POST.get('methode_vendange') or ''
        methode_vinification = request.POST.get('methode_vinification') or ''
        duree_elevage_mois = request.POST.get('duree_elevage_mois') or None
        contenant_elevage = request.POST.get('contenant_elevage') or ''
        degre_alcool_potentiel = request.POST.get('degre_alcool_potentiel') or None
        degre_alcool_final = request.POST.get('degre_alcool_final') or None
        sucres_residuels = request.POST.get('sucres_residuels') or None
        ph = request.POST.get('ph') or None
        acidite_totale = request.POST.get('acidite_totale') or None
        so2_libre = request.POST.get('so2_libre') or None
        so2_total = request.POST.get('so2_total') or None
        prix_revient_estime = request.POST.get('prix_revient_estime') or None
        certifications = request.POST.get('certifications', '').strip()
        notes_internes = request.POST.get('notes_internes', '').strip()
        notes_degustation = request.POST.get('notes_degustation', '').strip()
        etiquette_image = request.FILES.get('etiquette_image')

        errors = []
        if not name:
            errors.append("Le nom de la cuvée est obligatoire.")
        if not vintage_year:
            errors.append("Le millésime est obligatoire.")
        if not default_uom_id:
            errors.append("L'unité par défaut est obligatoire.")

        if errors:
            for e in errors:
                messages.error(request, e)
            initial_error = {
                **initial,
                'name': name,
                'code': code,
                'appellation_name': appellation_name,
                'vintage_year': vintage_year,
                'default_uom_id': default_uom_id or '',
                'default_unit_id': default_uom_id or '',
                'is_active': is_active,
                'type_vin': type_vin or '',
                'statut': statut or '',
                'volume_total_hl': volume_total_hl or '',
                'date_vendange_debut': date_vendange_debut or '',
                'date_vendange_fin': date_vendange_fin or '',
                'methode_vendange': methode_vendange or '',
                'methode_vinification': methode_vinification or '',
                'duree_elevage_mois': duree_elevage_mois or '',
                'contenant_elevage': contenant_elevage or '',
                'degre_alcool_potentiel': degre_alcool_potentiel or '',
                'degre_alcool_final': degre_alcool_final or '',
                'sucres_residuels': sucres_residuels or '',
                'ph': ph or '',
                'acidite_totale': acidite_totale or '',
                'so2_libre': so2_libre or '',
                'so2_total': so2_total or '',
                'prix_revient_estime': prix_revient_estime or '',
                'certifications': certifications or '',
                'notes_internes': notes_internes or '',
                'notes_degustation': notes_degustation or '',
            }
        else:
            try:
                # Vintage
                vintage = cuvee.vintage
                if vintage_year:
                    try:
                        y = int(vintage_year)
                        vintage, _ = Vintage.objects.get_or_create(organization=organization, year=y)
                    except Exception:
                        vintage = None
                # Appellation
                appellation = cuvee.appellation
                if appellation_name:
                    appellation = Appellation.objects.filter(organization=organization, name__iexact=appellation_name).first()
                    if not appellation:
                        appellation = Appellation.objects.create(
                            organization=organization, name=appellation_name, type='autre'
                        )
                else:
                    appellation = None
                # UoM (UUID or legacy referentiels.Unite id)
                uom = None
                try:
                    uom = UnitOfMeasure.objects.get(id=default_uom_id, organization=organization)
                except Exception:
                    uom = None
                if uom is None:
                    try:
                        rid = int(default_uom_id)
                        lu = Unite.objects.get(id=rid, organization=organization)
                        code_map = (lu.symbole or (lu.nom or '')[:10]).strip().upper()[:10]
                        ratio = Decimal(str(lu.facteur_conversion)) if lu.facteur_conversion is not None else None
                        if not code_map or ratio is None:
                            raise ValueError('Unité legacy invalide')
                        uom = UnitOfMeasure.objects.filter(organization=organization, code__iexact=code_map).first()
                        if not uom:
                            uom = UnitOfMeasure.objects.create(
                                organization=organization, code=code_map, name=(lu.nom or code_map)[:50], base_ratio_to_l=ratio
                            )
                    except Exception:
                        uom = None
                if uom is None:
                    raise ValueError("Unité introuvable")

                # Update cuvée
                cuvee.name = name
                cuvee.code = code
                cuvee.vintage = vintage
                cuvee.appellation = appellation
                cuvee.default_uom = uom
                cuvee.is_active = is_active
                cuvee.save()
                # Update/Créer détail
                detail, _ = CuveeDetail.objects.get_or_create(
                    cuvee=cuvee, defaults={'organization': organization}
                )
                if type_vin:
                    detail.type_vin = type_vin
                if statut:
                    detail.statut = statut
                detail.volume_total_hl = Decimal(volume_total_hl) if volume_total_hl else None
                # Dates
                try:
                    detail.date_vendange_debut = dt_date.fromisoformat(date_vendange_debut) if date_vendange_debut else None
                except Exception:
                    pass
                try:
                    detail.date_vendange_fin = dt_date.fromisoformat(date_vendange_fin) if date_vendange_fin else None
                except Exception:
                    pass
                detail.methode_vendange = methode_vendange
                detail.methode_vinification = methode_vinification
                detail.duree_elevage_mois = int(duree_elevage_mois) if duree_elevage_mois else None
                detail.contenant_elevage = contenant_elevage
                detail.degre_alcool_potentiel = Decimal(degre_alcool_potentiel) if degre_alcool_potentiel else None
                detail.degre_alcool_final = Decimal(degre_alcool_final) if degre_alcool_final else None
                detail.sucres_residuels = Decimal(sucres_residuels) if sucres_residuels else None
                detail.ph = Decimal(ph) if ph else None
                detail.acidite_totale = Decimal(acidite_totale) if acidite_totale else None
                detail.so2_libre = Decimal(so2_libre) if so2_libre else None
                detail.so2_total = Decimal(so2_total) if so2_total else None
                detail.prix_revient_estime = Decimal(prix_revient_estime) if prix_revient_estime else None
                detail.certifications = certifications
                detail.notes_internes = notes_internes
                detail.notes_degustation = notes_degustation
                if etiquette_image:
                    detail.etiquette_image = etiquette_image
                detail.save()
                messages.success(request, "Cuvée mise à jour avec succès !")
                return redirect('catalogue:cuvee_detail', pk=cuvee.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la mise à jour: {e}")
            initial_error = {
                **initial,
                'name': name,
                'code': code,
                'appellation_name': appellation_name,
                'vintage_year': vintage_year,
                'default_uom_id': default_uom_id or '',
                'default_unit_id': default_uom_id or '',
                'is_active': is_active,
            }

        context = {
            'page_title': f"Modifier la Cuvée",
            'appellations': appellations,
            'vintages': vintages,
            'suggested_vintages': suggested_vintages,
            'appellation_suggestions': appellation_suggestions,
            'parcelles': parcelles,
            'cepages': cepages,
            'type_vin_choices': CuveeDetail.TYPE_VIN_CHOICES,
            'statut_choices': CuveeDetail.STATUT_CHOICES,
            'vendange_choices': getattr(CuveeDetail, 'VENDANGE_CHOICES', []),
            'vinification_choices': getattr(CuveeDetail, 'VINIFICATION_CHOICES', []),
            'elevage_choices': getattr(CuveeDetail, 'ELEVAGE_CHOICES', []),
            'initial': initial_error,
            'is_edit': True,
            'breadcrumb_items': [
                {'name': 'Catalogue', 'url': reverse('catalogue:products_dashboard')},
                {'name': 'Cuvées', 'url': reverse('catalogue:products_cuvees')},
                {'name': cuvee.name, 'url': reverse('catalogue:cuvee_detail', kwargs={'pk': cuvee.id})},
                {'name': 'Modifier', 'url': None},
            ],
        }
        return render(request, 'catalogue/cuvee_form.html', context)

    # GET context (edit mode)
    context = {
        'page_title': f"Modifier la Cuvée",
        'appellations': appellations,
        'vintages': vintages,
        'suggested_vintages': suggested_vintages,
        'appellation_suggestions': appellation_suggestions,
        'parcelles': parcelles,
        'cepages': cepages,
        'type_vin_choices': CuveeDetail.TYPE_VIN_CHOICES,
        'statut_choices': CuveeDetail.STATUT_CHOICES,
        'vendange_choices': getattr(CuveeDetail, 'VENDANGE_CHOICES', []),
        'vinification_choices': getattr(CuveeDetail, 'VINIFICATION_CHOICES', []),
        'elevage_choices': getattr(CuveeDetail, 'ELEVAGE_CHOICES', []),
        'initial': initial,
        'is_edit': True,
        'breadcrumb_items': [
            {'name': 'Catalogue', 'url': reverse('catalogue:products_dashboard')},
            {'name': 'Cuvées', 'url': reverse('catalogue:products_cuvees')},
            {'name': cuvee.name, 'url': reverse('catalogue:cuvee_detail', kwargs={'pk': cuvee.id})},
            {'name': 'Modifier', 'url': None},
        ],
    }
    return render(request, 'catalogue/cuvee_form.html', context)

# Create your views here.


# (journal de parcelle lecture seule déplacé vers views_parcelle_journal.py)

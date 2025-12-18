from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, RedirectView
from . import views as prod_views
from . import views_containers as cont_views
from .views_assemblage import AssemblageWizardView, AssemblageDetailView
from .views_inventory import (
    InventoryHomeView,
    InventoryVracTable,
    InventoryFinishedTable,
    InventoryMSTable,
    InventoryLotsCommerciaux,
    InventoryRedirectView,
)
from .views_inventory_ms import MSReceiveModal, MSTransferModal, MSAdjustModal, MSItemCreateModal
from .views_vue_cuvee import VueCuveeView, LotTechniqueVueCuveeStatsAPI, LotTechniqueVueCuveeDetailsAPI
from .views_vinification import VinificationHomeView, VinificationOperationCreateView
from .views_vinification_filters import VinificationTableView
from .views_operations import (
    OperationCreateView, OperationDetailView, OperationEditView,
    OperationDeleteView, AlertFromOperationView,
)
from .views_soutirage import SoutirageHomeView, SoutirageCreateView, SoutirageTableView
from .views_assemblage_list import AssemblageListView, AssemblageTableView
from .views_analyses import (
    AnalysesOenoListView, AnalysesOenoTableView,
    AnalyseCreateView, AnalyseUpdateView, AnalyseDeleteView, AnalyseDuplicateView,
)
from .views_alerts import (
    AlertsListView, AlertCreateView, AlertUpdateView, AlertDeleteView,
    AlertCompleteView, AlertDismissView, AlertSnoozeView,
)
from apps.produits import views as prodt_views
from apps.referentiels.views import (
    parcelle_create as ref_parcelle_create,
    parcelle_detail as ref_parcelle_detail,
    parcelle_update as ref_parcelle_update,
)

app_name = 'production'

# Simple placeholder view factory

def page(title, crumbs=None, cta_href=None):
    extra = {'page_title': title}
    if crumbs is None:
        crumbs = [
            {'name': 'Production', 'url': '/production/'},
            {'name': title, 'url': None},
        ]
    extra['breadcrumb_items'] = crumbs
    if cta_href is not None:
        extra['cta_href'] = cta_href
    return login_required(TemplateView.as_view(template_name='production/placeholder.html', extra_context=extra))

urlpatterns = [
    # Production home (Vue d'ensemble)
    path('', prod_views.ProductionHomeView.as_view(), name='production_home'),

    # --- DASHBOARDS PAR PILIER ---
    path('vigne/', prod_views.ProductionVigneView.as_view(), name='dash_vigne'),
    path('chai/', prod_views.ProductionChaiView.as_view(), name='dash_chai'),
    path('elevage/', prod_views.ProductionElevageView.as_view(), name='dash_elevage'),
    path('conditionnement/', prod_views.ProductionConditionnementView.as_view(), name='dash_conditionnement'),

    # Encuvages & Pressurages
    path('encuvages/', prod_views.EncuvageListView.as_view(), name='encuvages_list'),
    path('encuvages/table/', prod_views.EncuvageTableView.as_view(), name='encuvages_table'),
    path('pressurages/', page('Pressurages', cta_href='/production/lots-techniques/'), name='pressurages_list'),
    
    path('vinification/', VinificationHomeView.as_view(), name='vinification_home'),
    path('vinification/table/', VinificationTableView.as_view(), name='vinification_table'),
    path('vinification/operation/create/', VinificationOperationCreateView.as_view(), name='vinification_op_create'),
    
    # Opérations de cave (NOUVEAU - formulaires spécialisés)
    path('operations/nouvelle/', OperationCreateView.as_view(), name='operation_create'),
    path('operations/<int:pk>/', OperationDetailView.as_view(), name='operation_detail'),
    path('operations/<int:pk>/modifier/', OperationEditView.as_view(), name='operation_edit'),
    path('operations/<int:pk>/supprimer/', OperationDeleteView.as_view(), name='operation_delete'),
    path('operations/<int:pk>/creer-alerte/', AlertFromOperationView.as_view(), name='alert_from_operation'),
    
    path('soutirages/', SoutirageHomeView.as_view(), name='soutirages_list'),
    path('soutirages/table/', SoutirageTableView.as_view(), name='soutirages_table'),
    path('soutirages/nouveau/', SoutirageCreateView.as_view(), name='soutirage_create'),
    
    path('assemblages/', AssemblageListView.as_view(), name='assemblages_list'),
    path('assemblages/table/', AssemblageTableView.as_view(), name='assemblages_table'),
    path('analyses/', page('Analyses', cta_href='/production/lots-elevage/analyses/'), name='analyses_home'),

    # Parcelles (alias vers vues Référentiels)
    path('parcelles/', prod_views.ParcelleListView.as_view(), name='parcelles_list'),
    path('parcelles/table/', prod_views.ParcelleTableView.as_view(), name='parcelles_table'),
    path('parcelles/nouveau/', ref_parcelle_create, name='parcelle_new'),
    path('parcelles/<int:pk>/', ref_parcelle_detail, name='parcelle_detail'),
    path('parcelles/<int:pk>/modifier/', ref_parcelle_update, name='parcelle_update'),
    
    # Bloc VIGNE - Journal cultural unifié (fusionne cahier, phyto, maturité)
    path('journal-cultural/', prod_views.JournalCulturalView.as_view(), name='journal_cultural'),
    path('journal-cultural/table/', prod_views.JournalCulturalTableView.as_view(), name='journal_cultural_table'),
    # Anciennes routes conservées pour compatibilité (redirections)
    path('cahier-cultural/', RedirectView.as_view(url='/production/journal-cultural/?tab=interventions', permanent=False), name='cahier_cultural'),
    path('registre-phyto/', RedirectView.as_view(url='/production/journal-cultural/?tab=phyto', permanent=False), name='registre_phyto'),
    path('suivi-maturite/', RedirectView.as_view(url='/production/journal-cultural/?tab=maturite', permanent=False), name='suivi_maturite'),

    # Vendanges
    path('vendanges/', prod_views.VendangeListView.as_view(), name='vendanges_list'),
    path('vendanges/table/', prod_views.VendangesTableView.as_view(), name='vendanges_table'),
    path('vendanges/nouveau/', prod_views.VendangeCreateView.as_view(), name='vendange_new'),
    path('vendanges/carte/', prod_views.VendangeMapView.as_view(), name='vendanges_map'),
    path('vendanges/parcelle/prefill/', prod_views.ParcellePrefillPartial.as_view(), name='vendange_parcelle_prefill'),
    path('vendanges/<int:pk>/', prod_views.VendangeDetailView.as_view(), name='vendange_detail'),
    path('vendanges/<int:pk>/modifier/', prod_views.VendangeUpdateView.as_view(), name='vendange_update'),
    path('vendanges/<int:pk>/affecter-cuvee/', prod_views.VendangeAffecterCuveeView.as_view(), name='vendange_affecter_cuvee'),
    path('vendanges/<int:pk>/encuvage/', prod_views.EncuvageWizardView.as_view(), name='vendange_encuvage'),

    # Lots techniques
    # path('lots-techniques/', prod_views.LotTechniqueListView.as_view(), name='lots_tech_list'), # Legacy
    path('lots-techniques/', VueCuveeView.as_view(), name='lots_tech_list'),
    path('lots-techniques/liste/', prod_views.LotTechniqueListView.as_view(), name='lots_tech_list_legacy'),
    
    path('lots-techniques/table/', prod_views.LotTechniqueTableView.as_view(), name='lots_tech_table'),
    path('lots-techniques/nouveau/', prod_views.LotTechniqueCreateView.as_view(), name='lot_tech_new'),
    path('lots-techniques/<int:pk>/', prod_views.LotTechniqueDetailView.as_view(), name='lot_tech_detail'),
    path('lots-techniques/<int:pk>/mouvements/export/', prod_views.lot_mouvements_export, name='lot_mouvements_export'),

    # API Vue Cuvée
    path('api/lots-techniques/vue-cuvee/', LotTechniqueVueCuveeStatsAPI.as_view(), name='api_lot_vue_cuvee_stats'),
    path('api/lots-techniques/par-cuvee/', LotTechniqueVueCuveeDetailsAPI.as_view(), name='api_lot_vue_cuvee_details'),

    # Lots & Élevage (alias to canonical list: scope=elevage)
    path(
        'lots-elevage/',
        RedirectView.as_view(url='/production/lots-techniques/?scope=elevage', permanent=False),
        name='lots_elevage_home',
    ),
    path('lots-elevage/table/', prod_views.LotsElevageList.as_view(), name='lots_elevage_table'),
    path('lots-elevage/journal/', prod_views.JournalVracListView.as_view(), name='lots_elevage_journal'),
    path('lots-elevage/journal/table/', prod_views.JournalVracTableView.as_view(), name='lots_elevage_journal_table'),
    # Analyses œnologiques (nouveau système complet)
    path('lots-elevage/analyses/', AnalysesOenoListView.as_view(), name='analyses_oeno_list'),
    path('lots-elevage/analyses/table/', AnalysesOenoTableView.as_view(), name='analyses_oeno_table'),
    path('lots-elevage/analyses/nouvelle/', AnalyseCreateView.as_view(), name='analyse_oeno_new'),
    path('lots-elevage/analyses/<int:pk>/', AnalyseUpdateView.as_view(), name='analyse_oeno_edit'),
    path('lots-elevage/analyses/<int:pk>/supprimer/', AnalyseDeleteView.as_view(), name='analyse_oeno_delete'),
    path('lots-elevage/analyses/<int:pk>/dupliquer/', AnalyseDuplicateView.as_view(), name='analyse_oeno_duplicate'),
    # Legacy aliases for old routes
    path('lots-elevage/analyses/legacy/', prod_views.AnalysesHomeView.as_view(), name='lots_elevage_analyses'),
    path('lots-elevage/analyses/legacy/table/', prod_views.AnalysesTableView.as_view(), name='lots_elevage_analyses_table'),
    # Contenants (top-level)
    path('contenants/', cont_views.ContenantListView.as_view(), name='contenants_list'),
    path('contenants/nouveau/', cont_views.ContenantCreateView.as_view(), name='contenants_new'),
    path('contenants/<int:pk>/', cont_views.ContenantDetailView.as_view(), name='contenants_detail'),
    path('contenants/<int:pk>/edit/', cont_views.ContenantUpdateView.as_view(), name='contenants_edit'),
    # Actions Contenant
    path('contenants/<int:pk>/occupancy/recalc/', cont_views.contenant_recalc_occupancy, name='contenants_recalc'),
    path('contenants/<int:pk>/actions/affecter-lot/', cont_views.ContenantAffecterLotView.as_view(), name='contenants_affecter_lot'),
    path('contenants/<int:pk>/actions/vidange/', cont_views.ContenantVidangeView.as_view(), name='contenants_vidange'),
    path('contenants/<int:pk>/actions/nettoyage/', cont_views.ContenantNettoyageView.as_view(), name='contenants_nettoyage'),

    # Backward-compat redirects from old nested paths
    path('lots-elevage/contenants/', RedirectView.as_view(url='/production/contenants/', permanent=False), name='lots_contenants'),
    path('lots-elevage/contenants/nouveau/', RedirectView.as_view(url='/production/contenants/nouveau/', permanent=False)),
    path('services/entry/', prod_views.ServiceEntryModal.as_view(), name='service_entry'),

    # Assemblages
    path('assemblages/nouveau/', AssemblageWizardView.as_view(), name='assemblage_wizard'),
    path('assemblages/<int:pk>/', AssemblageDetailView.as_view(), name='assemblage_detail'),

    # Mises (views in apps.produits)
    path('mises/', prodt_views.MiseListView.as_view(), name='mises_list'),
    path('mises/nouveau/', prodt_views.MiseWizardView.as_view(), name='mise_new'),
    # Alias name for the wizard route to support new naming without breaking existing links
    path('mises/nouveau/', prodt_views.MiseWizardView.as_view(), name='mise_wizard'),
    path('mises/<uuid:pk>/', prodt_views.MiseDetailView.as_view(), name='mise_detail'),

    # Actions sur lots techniques (MVP)
    path('lots-techniques/<int:pk>/action/<str:action>/', prod_views.LotTechniqueActionView.as_view(), name='lot_tech_action'),

    # Affectation cuvée sur lot technique
    path('lots-techniques/<int:pk>/affecter-cuvee/', prod_views.LotTechAffecterCuveeView.as_view(), name='lot_tech_affecter_cuvee'),
    
    # Wizards & opérations
    path('lots-techniques/<int:pk>/soutirage/', prod_views.SoutirageWizardView.as_view(), name='lot_tech_soutirage'),
    path('lots-techniques/<int:pk>/pressurage/', prod_views.PressurageWizardView.as_view(), name='lot_tech_pressurage'),
    path('lots-techniques/<int:pk>/vinif/measure/add/', prod_views.lot_vinif_add_measure, name='lot_vinif_add_measure'),
    path('lots-techniques/<int:pk>/vinif/intervention/add/', prod_views.lot_vinif_add_intervention, name='lot_vinif_add_intervention'),

    # APIs (HTMX/JSON) for Mise wizard smart calculations
    path('api/mise/calc/step1/', prodt_views.mise_calc_step1, name='mise_calc_step1'),
    path('api/mise/calc/step2/', prodt_views.mise_calc_step2, name='mise_calc_step2'),
    path('api/mise/validate/', prodt_views.mise_validate_preview, name='mise_validate_preview'),
    path('api/mise/save-step2/', prodt_views.mise_save_step2, name='mise_save_step2'),

    # Paramètres & Rapports (placeholders)
    path('parametres/', page('Paramètres'), name='production_settings'),
    path('rapports/', page('Rapports & DRM'), name='production_reports'),
    
    # Bloc REGISTRES - Export des registres obligatoires
    path('registres/', login_required(TemplateView.as_view(
        template_name='production/registres_home.html',
        extra_context={
            'page_title': 'Registres obligatoires',
            'breadcrumb_items': [
                {'name': 'Production', 'url': '/production/'},
                {'name': 'Registres', 'url': None},
            ]
        }
    )), name='registres_home'),
    # Inventaire (HTMX tabs)
    path('inventaire/', InventoryHomeView.as_view(), name='inventaire'),
    path('inventaire/tab/vrac/', InventoryVracTable.as_view(), name='inventaire_vrac'),
    path('inventaire/tab/produits/', InventoryFinishedTable.as_view(), name='inventaire_produits'),
    path('inventaire/tab/lots-commerciaux/', InventoryLotsCommerciaux.as_view(), name='inventaire_lots_commerciaux'),
    path('inventaire/tab/ms/', InventoryMSTable.as_view(), name='inventaire_ms'),
    # Legacy/alias: Stock (vrac) → redirect to Inventaire onglet Vrac
    path('stock-vrac/', InventoryRedirectView.as_view(), name='stock_vrac'),
    path('inventaire/ms/entree/', MSReceiveModal.as_view(), name='inventaire_ms_entree'),
    path('inventaire/ms/transfert/', MSTransferModal.as_view(), name='inventaire_ms_transfert'),
    path('inventaire/ms/ajustement/', MSAdjustModal.as_view(), name='inventaire_ms_ajustement'),
    path('inventaire/ms/item/create/', MSItemCreateModal.as_view(), name='inventaire_ms_item_create'),
    
    # ========== ALERTES & RAPPELS ==========
    path('alertes/', AlertsListView.as_view(), name='alerts_list'),
    path('alertes/nouvelle/', AlertCreateView.as_view(), name='alert_create'),
    path('alertes/<int:pk>/modifier/', AlertUpdateView.as_view(), name='alert_update'),
    path('alertes/<int:pk>/supprimer/', AlertDeleteView.as_view(), name='alert_delete'),
    path('alertes/<int:pk>/terminer/', AlertCompleteView.as_view(), name='alert_complete'),
    path('alertes/<int:pk>/ignorer/', AlertDismissView.as_view(), name='alert_dismiss'),
    path('alertes/<int:pk>/reporter/', AlertSnoozeView.as_view(), name='alert_snooze'),
]

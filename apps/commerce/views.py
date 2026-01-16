from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.db import models
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

from .models import CommercialDocument, CommercialLine, Payment
from .forms import CommercialDocumentForm, CommercialLineForm, PaymentForm, InvoiceForm, InvoiceLineFormSet
from apps.accounts.decorators import require_membership
from apps.partners.models import Partner


@login_required
def client_search_htmx(request):
    """Recherche de clients via HTMX pour les formulaires de facture/devis"""
    q = request.GET.get('q', '').strip()
    org = getattr(request, 'current_org', None)
    
    clients = Partner.objects.filter(
        organization=org,
        roles__code='client',
        is_active=True
    ).order_by('name')
    
    if q:
        clients = clients.filter(
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(code__icontains=q)
        )
    
    clients = clients[:20]  # Limiter à 20 résultats
    
    return render(request, 'commerce/_client_search_results.html', {
        'clients': clients
    })

def get_namespace(side):
    return 'ventes' if side == 'sale' else 'achats'

@require_membership(role_min='read_only')
def dashboard(request, side='sale'):
    """
    Tableau de bord unifié (Achats ou Ventes).
    """
    org = request.current_org
    ns = get_namespace(side)
    today = timezone.now().date()
    
    # KPIs
    docs = CommercialDocument.objects.filter(organization=org, side=side)
    
    # Factures impayées (Issued et non payées)
    unpaid_invoices = docs.filter(
        type=CommercialDocument.TYPE_INVOICE,
        status=CommercialDocument.STATUS_ISSUED
    ).exclude(amount_paid__gte=models.F('total_ttc'))
    
    total_due = sum(d.amount_due for d in unpaid_invoices)
    count_due = unpaid_invoices.count()
    
    # Commandes en cours (Validées mais non exécutées/facturées complètement)
    pending_orders = docs.filter(
        type=CommercialDocument.TYPE_ORDER,
        status=CommercialDocument.STATUS_VALIDATED
    )
    
    # Devis à relancer (Envoyés, pas encore validés/refusés)
    pending_quotes = docs.filter(
        type=CommercialDocument.TYPE_QUOTE,
        status=CommercialDocument.STATUS_SENT
    )

    # To-do list (exemples)
    todos = []
    if count_due > 0:
        todos.append({
            'label': f"{count_due} factures à {'encaisser' if side == 'sale' else 'payer'}",
            'value': f"{total_due:.2f} €",
            'url': f"{reverse(f'{ns}:invoices_list')}?status=issued"
        })
    
    if pending_orders.exists():
        todos.append({
            'label': f"{pending_orders.count()} commandes à traiter",
            'url': f"{reverse(f'{ns}:orders_list')}?status=validated"
        })

    context = {
        'side': side,
        'namespace': ns,
        'page_title': f"Tableau de bord {'Ventes' if side == 'sale' else 'Achats'}",
        'kpis': {
            'unpaid_amount': total_due,
            'unpaid_count': count_due,
            'orders_count': pending_orders.count(),
            'quotes_count': pending_quotes.count(),
        },
        'todos': todos,
        'recent_docs': docs.order_by('-updated_at')[:5],
    }
    return render(request, 'commerce/dashboard.html', context)


class DocumentListView(LoginRequiredMixin, ListView):
    model = CommercialDocument
    template_name = 'commerce/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        side = self.kwargs.get('side', 'sale')
        qs = CommercialDocument.objects.filter(organization=org, side=side)
        
        # Filtres
        # Priorité au type forcé dans l'URL (kwargs), sinon GET param
        doc_type = self.kwargs.get('doc_type') or self.request.GET.get('type')
        if doc_type:
            qs = qs.filter(type=doc_type)
            
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
            
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(number__icontains=q) | 
                Q(client__name__icontains=q) |
                Q(reference__icontains=q)
            )
            
        return qs.select_related('client')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        side = self.kwargs.get('side', 'sale')
        ctx['side'] = side
        
        # Titre contextuel selon le type forcé
        doc_type = self.kwargs.get('doc_type') or self.request.GET.get('type')
        if doc_type:
            # Récupérer le label du type
            type_label = dict(CommercialDocument.TYPE_CHOICES).get(doc_type, doc_type)
            ctx['page_title'] = f"{type_label}s ({'Ventes' if side == 'sale' else 'Achats'})"
            ctx['current_type'] = doc_type
        else:
            ctx['page_title'] = f"Documents {'Ventes' if side == 'sale' else 'Achats'}"
            
        ctx['type_choices'] = CommercialDocument.TYPE_CHOICES
        ctx['status_choices'] = CommercialDocument.STATUS_CHOICES
        ctx['namespace'] = 'ventes' if side == 'sale' else 'achats'
        return ctx


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = CommercialDocument
    form_class = CommercialDocumentForm
    template_name = 'commerce/document_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        kwargs['side'] = self.kwargs.get('side', 'sale')
        return kwargs
        
    def form_valid(self, form):
        form.instance.organization = getattr(self.request, 'current_org', None)
        form.instance.side = self.kwargs.get('side', 'sale')
        form.instance.type = self.kwargs.get('type', 'quote')
        form.instance.created_by = self.request.user
        # Génération numéro (basique pour l'instant)
        last_doc = CommercialDocument.objects.filter(
            organization=form.instance.organization, 
            side=form.instance.side,
            type=form.instance.type
        ).order_by('number').last()
        
        # TODO: implémenter un sequenceur plus robuste
        prefix = form.instance.type[:2].upper()
        form.instance.number = f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{str(timezone.now().timestamp())[-4:]}"
        
        return super().form_valid(form)

    def get_success_url(self):
        ns = 'ventes' if self.object.side == 'sale' else 'achats'
        # Pour le detail, on utilise le nom de vue générique mappé dans les urls (quote_detail, order_detail etc)
        # Mais comme c'est polymorphe, le plus simple est d'avoir une URL générique 'document_detail' dans chaque namespace
        # Dans urls_achats.py, j'ai mis quote_detail, order_detail... C'est embêtant pour le polymorphisme.
        # Je vais unifier les noms dans urls_*.py pour avoir un fallback ou alors utiliser une logique ici.
        # D'après mes urls, j'ai quote_detail, order_detail...
        # Je vais mapper le type vers le nom d'url suffixe.
        type_map = {
            'quote': 'quote_detail',
            'order': 'order_detail',
            'delivery': 'delivery_detail',
            'invoice': 'invoice_detail',
            'credit_note': 'credit_note_detail'
        }
        url_name = type_map.get(self.object.type, 'quote_detail')
        return reverse(f'{ns}:{url_name}', args=[self.object.id])
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        side = self.kwargs.get('side', 'sale')
        doc_type = self.kwargs.get('type', 'quote')
        ctx['page_title'] = f"Nouveau {doc_type} ({side})"
        ctx['side'] = side
        ctx['namespace'] = 'ventes' if side == 'sale' else 'achats'
        return ctx


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = CommercialDocument
    form_class = InvoiceForm
    template_name = 'commerce/invoice_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        kwargs['side'] = 'sale'
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        # Précharger le client depuis l'URL param ?client=UUID ou display_id
        client = self._get_client_from_param()
        if client:
            initial['client'] = str(client.pk)
        return initial
    
    def _get_client_from_param(self):
        """Récupère le client depuis le param ?client= (UUID ou display_id)"""
        client_id = self.request.GET.get('client')
        if not client_id:
            return None
        
        from apps.partners.models import Partner
        import uuid
        
        org = self.request.current_org
        
        # Essayer d'abord comme UUID
        try:
            uuid.UUID(client_id)
            return Partner.objects.filter(pk=client_id, organization=org).first()
        except (ValueError, TypeError):
            pass
        
        # Sinon essayer comme display_id (entier)
        try:
            display_id = int(client_id)
            return Partner.objects.filter(display_id=display_id, organization=org).first()
        except (ValueError, TypeError):
            pass
        
        return None
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Nouvelle Facture"
        ctx['side'] = 'sale'
        ctx['namespace'] = 'ventes'
        
        # Charger la liste des clients pour le sélecteur
        from apps.partners.models import Partner
        org = getattr(self.request, 'current_org', None)
        ctx['clients'] = Partner.objects.filter(
            organization=org,
            roles__code='client',
            is_active=True
        ).order_by('name')
        
        # Précharger les infos client pour le template
        client = self._get_client_from_param()
        if client:
            ctx['preloaded_client'] = client
            # Récupérer l'adresse de facturation
            billing_addr = client.addresses.filter(address_type='billing').first() or client.addresses.first()
            ctx['preloaded_client_address'] = billing_addr
        
        if self.request.POST:
            ctx['lines'] = InvoiceLineFormSet(self.request.POST, form_kwargs={'organization': self.request.current_org})
        else:
            ctx['lines'] = InvoiceLineFormSet(form_kwargs={'organization': self.request.current_org})
        return ctx

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        
        if form.is_valid() and lines.is_valid():
            self.object = form.save(commit=False)
            self.object.organization = getattr(self.request, 'current_org', None)
            self.object.side = 'sale'
            self.object.type = CommercialDocument.TYPE_INVOICE
            self.object.created_by = self.request.user
            
            # Simple number generation logic (placeholder)
            prefix = "FAC"
            self.object.number = f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{str(timezone.now().timestamp())[-4:]}"
            self.object.save()
            
            lines.instance = self.object
            lines.save()
            
            # Recalculate totals
            total_ht = sum(l.amount_ht for l in self.object.lines.all())
            total_tax = sum(l.amount_tax for l in self.object.lines.all())
            total_ttc = sum(l.amount_ttc for l in self.object.lines.all())
            self.object.total_ht = total_ht
            self.object.total_tax = total_tax
            self.object.total_ttc = total_ttc
            self.object.save()
            
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('ventes:invoice_detail', args=[self.object.id])


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = CommercialDocument
    template_name = 'commerce/document_detail.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        return CommercialDocument.objects.filter(organization=getattr(self.request, 'current_org', None))
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['lines'] = self.object.lines.all().select_related('sku')
        ctx['payments'] = self.object.payments.all()
        ctx['line_form'] = CommercialLineForm(organization=self.request.current_org)
        ctx['payment_form'] = PaymentForm()
        ctx['side'] = self.object.side
        ctx['namespace'] = 'ventes' if self.object.side == 'sale' else 'achats'
        return ctx


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = CommercialDocument
    form_class = CommercialDocumentForm
    template_name = 'commerce/document_form.html'
    
    def get_queryset(self):
        return CommercialDocument.objects.filter(organization=getattr(self.request, 'current_org', None))
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        kwargs['side'] = self.object.side
        return kwargs

    def get_success_url(self):
        ns = 'ventes' if self.object.side == 'sale' else 'achats'
        type_map = {
            'quote': 'quote_detail',
            'order': 'order_detail',
            'delivery': 'delivery_detail',
            'invoice': 'invoice_detail',
            'credit_note': 'credit_note_detail'
        }
        url_name = type_map.get(self.object.type, 'quote_detail')
        return reverse(f'{ns}:{url_name}', args=[self.object.id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Modifier {self.object.number}"
        ctx['side'] = self.object.side
        ctx['namespace'] = 'ventes' if self.object.side == 'sale' else 'achats'
        return ctx


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = CommercialDocument
    template_name = 'commerce/document_confirm_delete.html'
    
    def get_queryset(self):
        return CommercialDocument.objects.filter(organization=getattr(self.request, 'current_org', None))

    def get_success_url(self):
        ns = 'ventes' if self.object.side == 'sale' else 'achats'
        # Redirection vers la liste du bon type
        type_map = {
            'quote': 'quotes_list',
            'order': 'orders_list',
            'delivery': 'deliveries_list',
            'invoice': 'invoices_list',
            'credit_note': 'credit_notes_list'
        }
        url_name = type_map.get(self.object.type, 'dashboard')
        return reverse(f'{ns}:{url_name}')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['namespace'] = 'ventes' if self.object.side == 'sale' else 'achats'
        return ctx


from .services import DocumentService

# ... (imports remain the same)

# ... (Dashboard and CRUD views remain the same)

# --- ACTIONS ---

@require_POST
@require_membership(role_min='editor')
def add_line(request, pk):
    # ... (remains same)
    doc = get_object_or_404(CommercialDocument, pk=pk, organization=request.current_org)
    form = CommercialLineForm(request.POST, organization=request.current_org)
    
    ns = 'ventes' if doc.side == 'sale' else 'achats'
    # Fallback map pour le detail
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    detail_url_name = type_map.get(doc.type, 'quote_detail')
    
    if form.is_valid():
        line = form.save(commit=False)
        line.document = doc
        line.save()
        
        # Update doc totals
        lines = doc.lines.all()
        doc.total_ht = sum(l.amount_ht for l in lines)
        doc.total_tax = sum(l.amount_tax for l in lines)
        doc.total_ttc = sum(l.amount_ttc for l in lines)
        doc.save()
        
        messages.success(request, "Ligne ajoutée")
    else:
        messages.error(request, "Erreur lors de l'ajout de la ligne")
        
    return redirect(f'{ns}:{detail_url_name}', pk=pk)


@require_POST
@require_membership(role_min='editor')
def delete_line(request, pk):
    # ... (remains same)
    line = get_object_or_404(CommercialLine, pk=pk, document__organization=request.current_org)
    doc = line.document
    line.delete()
    
    ns = 'ventes' if doc.side == 'sale' else 'achats'
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    detail_url_name = type_map.get(doc.type, 'quote_detail')

    # Update totals
    lines = doc.lines.all()
    doc.total_ht = sum(l.amount_ht for l in lines)
    doc.total_tax = sum(l.amount_tax for l in lines)
    doc.total_ttc = sum(l.amount_ttc for l in lines)
    doc.save()
    
    messages.success(request, "Ligne supprimée")
    return redirect(f'{ns}:{detail_url_name}', pk=doc.pk)


@require_POST
@require_membership(role_min='editor')
def transform_document(request, pk, target_type):
    """
    Transforme un document (ex: Devis -> Commande) via le service.
    """
    source = get_object_or_404(CommercialDocument, pk=pk, organization=request.current_org)
    ns = 'ventes' if source.side == 'sale' else 'achats'
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    source_detail_url = type_map.get(source.type, 'quote_detail')
    
    try:
        new_doc = DocumentService.transform_document(source, target_type, user=request.user)
        messages.success(request, f"Document transformé en {new_doc.get_type_display()}")
        
        target_detail_url = type_map.get(new_doc.type, 'quote_detail')
        return redirect(f'{ns}:{target_detail_url}', pk=new_doc.pk)
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect(f'{ns}:{source_detail_url}', pk=source.pk)

@require_POST
@require_membership(role_min='editor')
def validate_document(request, pk):
    doc = get_object_or_404(CommercialDocument, pk=pk, organization=request.current_org)
    ns = 'ventes' if doc.side == 'sale' else 'achats'
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    detail_url = type_map.get(doc.type, 'quote_detail')
    
    try:
        DocumentService.validate_order(doc, user=request.user)
        messages.success(request, "Document validé.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect(f'{ns}:{detail_url}', pk=pk)

@require_POST
@require_membership(role_min='editor')
def execute_document(request, pk):
    doc = get_object_or_404(CommercialDocument, pk=pk, organization=request.current_org)
    ns = 'ventes' if doc.side == 'sale' else 'achats'
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    detail_url = type_map.get(doc.type, 'quote_detail')

    try:
        DocumentService.execute_delivery(doc, user=request.user)
        messages.success(request, "Document exécuté (Stock mis à jour).")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect(f'{ns}:{detail_url}', pk=pk)

@require_POST
@require_membership(role_min='editor')
def add_payment(request, pk):
    doc = get_object_or_404(CommercialDocument, pk=pk, organization=request.current_org)
    form = PaymentForm(request.POST)
    
    ns = 'ventes' if doc.side == 'sale' else 'achats'
    type_map = {'quote': 'quote_detail', 'order': 'order_detail', 'delivery': 'delivery_detail', 'invoice': 'invoice_detail', 'credit_note': 'credit_note_detail'}
    detail_url = type_map.get(doc.type, 'quote_detail')
    
    if form.is_valid():
        payment = form.save(commit=False)
        payment.organization = request.current_org
        payment.document = doc
        payment.created_by = request.user
        payment.save()
        
        # Update document paid amount
        doc.amount_paid = sum(p.amount for p in doc.payments.all())
        
        # Check if fully paid
        if doc.amount_paid >= doc.total_ttc:
            doc.status = CommercialDocument.STATUS_PAID
            
        doc.save()
        
        messages.success(request, f"Paiement de {payment.amount}€ enregistré.")
    else:
        messages.error(request, "Erreur lors de l'enregistrement du paiement.")
        
    return redirect(f'{ns}:{detail_url}', pk=pk)


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'commerce/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        side = self.kwargs.get('side', 'sale')
        return Payment.objects.filter(
            organization=org, 
            document__side=side
        ).select_related('document', 'document__client').order_by('-date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['side'] = self.kwargs.get('side', 'sale')
        ctx['page_title'] = f"Paiements {'Reçus' if ctx['side'] == 'sale' else 'Effectués'}"
        ctx['namespace'] = 'ventes' if ctx['side'] == 'sale' else 'achats'
        return ctx


class PaymentScheduleView(LoginRequiredMixin, ListView):
    model = CommercialDocument
    template_name = 'commerce/payment_schedule.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        side = self.kwargs.get('side', 'sale')
        return CommercialDocument.objects.filter(
            organization=org,
            side=side,
            type=CommercialDocument.TYPE_INVOICE,
            status=CommercialDocument.STATUS_ISSUED
        ).exclude(amount_paid__gte=models.F('total_ttc')).order_by('date_due')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['side'] = self.kwargs.get('side', 'sale')
        ctx['page_title'] = f"Échéancier {'Clients' if ctx['side'] == 'sale' else 'Fournisseurs'}"
        ctx['namespace'] = 'ventes' if ctx['side'] == 'sale' else 'achats'
        return ctx

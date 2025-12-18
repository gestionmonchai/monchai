from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django import forms

from apps.catalogue.models import Article, ArticleCategory
from apps.catalogue.forms import ArticleForm

# --- FORMS SPÉCIFIQUES ---

class PurchaseArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'name', 'sku', 'category', 'article_type', 'description', 
            'purchase_price', 'vat_rate', 'unit', 'is_stock_managed',
            'is_buyable', 'is_sellable', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'article_type': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'placeholder': 'Ex: Bouteille, Carton...', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['purchase_price'].label = "Prix d'achat HT"
        # Hide internal flags
        self.fields['is_buyable'].widget = forms.HiddenInput()
        self.fields['is_sellable'].widget = forms.HiddenInput()
        self.fields['is_active'].widget = forms.HiddenInput()
        
        if organization:
            self.fields['category'].queryset = ArticleCategory.objects.filter(organization=organization)

class SalesArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'name', 'sku', 'category', 'article_type', 'description', 
            'price_ht', 'vat_rate', 'unit', 'is_stock_managed',
            'is_buyable', 'is_sellable', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'article_type': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'placeholder': 'Ex: Bouteille, Carton...', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'price_ht': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
    
    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price_ht'].label = "Prix de vente HT"
        # Hide internal flags
        self.fields['is_buyable'].widget = forms.HiddenInput()
        self.fields['is_sellable'].widget = forms.HiddenInput()
        self.fields['is_active'].widget = forms.HiddenInput()
        
        if organization:
            self.fields['category'].queryset = ArticleCategory.objects.filter(organization=organization)

class ResaleConfigForm(forms.ModelForm):
    """Mini formulaire pour activer la revente (Scénario 2)"""
    enable_resale = forms.BooleanField(
        label="Est-ce que tu revends aussi ce produit ?",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'})
    )
    
    class Meta:
        model = Article
        fields = ['price_ht', 'vat_rate']
        widgets = {
            'price_ht': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price_ht'].label = "Prix de vente HT"
        self.fields['price_ht'].required = False
        self.fields['vat_rate'].label = "Taux de TVA"
        self.fields['vat_rate'].required = False

class SourceConfigForm(forms.Form):
    """Formulaire pour définir la source (Scénario 3)"""
    SOURCE_CHOICES = [
        ('produced', 'Produit par moi (Vin, Service...)'),
        ('bought', 'Acheté puis revendu (Négoce, Accessoire...)')
    ]
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="D'où vient ce que tu vends ?"
    )

# --- VIEWS ACHATS ---

class PurchaseArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'commerce/articles/purchase_list.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        return Article.objects.filter(organization=org, is_buyable=True).order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Liste de tout ce que j'achète"
        ctx['side'] = 'purchase'
        return ctx

class PurchaseArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = PurchaseArticleForm
    template_name = 'commerce/articles/purchase_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Force le profil ACHAT
        initial['is_buyable'] = True
        initial['is_sellable'] = False 
        return initial

    def form_valid(self, form):
        form.instance.organization = getattr(self.request, 'current_org', None)
        # Force strict séparation initiale
        form.instance.is_buyable = True
        form.instance.is_sellable = False
        self.object = form.save()
        
        # Redirection vers l'étape "Revendre ?"
        return redirect('achats:article_resale_config', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Créer un article d'achat"
        ctx['side'] = 'purchase'
        return ctx

class PurchaseArticleResaleView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ResaleConfigForm
    template_name = 'commerce/articles/purchase_resale_step.html'
    
    def get_queryset(self):
        return Article.objects.filter(organization=self.request.current_org)

    def form_valid(self, form):
        # Si "enable_resale" est coché, on active la vente
        enable = form.cleaned_data.get('enable_resale')
        if enable:
            form.instance.is_sellable = True
            messages.success(self.request, "Article configuré pour l'achat et la revente.")
        else:
            form.instance.is_sellable = False
            messages.success(self.request, "Article d'achat créé.")
            
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('achats:article_list')

class PurchaseArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'commerce/articles/purchase_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(organization=self.request.current_org, is_buyable=True)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = self.object.name
        ctx['side'] = 'purchase'
        return ctx


# --- VIEWS VENTES ---

class SalesArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'commerce/articles/sales_list.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        return Article.objects.filter(organization=org, is_sellable=True).order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Liste de tout ce que je vends"
        ctx['side'] = 'sale'
        return ctx

class SalesArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = SalesArticleForm
    template_name = 'commerce/articles/sales_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Force le profil VENTE
        initial['is_sellable'] = True
        initial['is_buyable'] = False
        return initial

    def form_valid(self, form):
        form.instance.organization = getattr(self.request, 'current_org', None)
        # Force strict séparation initiale
        form.instance.is_sellable = True
        form.instance.is_buyable = False
        self.object = form.save()
        
        # Redirection vers l'étape "Source ?"
        return redirect('ventes:article_source_config', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Créer un article de vente"
        ctx['side'] = 'sale'
        return ctx

class SalesArticleSourceView(LoginRequiredMixin, FormView):
    form_class = SourceConfigForm
    template_name = 'commerce/articles/sales_source_step.html'
    
    def get_initial(self):
        return {'source': 'produced'} # Default

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        article = get_object_or_404(Article, pk=pk, organization=self.request.current_org)
        
        source = form.cleaned_data.get('source')
        if source == 'bought':
            article.is_buyable = True
            messages.success(self.request, "Article configuré comme 'Acheté et Revendu'.")
        else:
            article.is_buyable = False
            messages.success(self.request, "Article configuré comme 'Produit par moi'.")
        
        article.save()
        return redirect('ventes:article_list')
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['article'] = get_object_or_404(Article, pk=self.kwargs.get('pk'), organization=self.request.current_org)
        return ctx

class SalesArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = 'commerce/articles/sales_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(organization=self.request.current_org, is_sellable=True)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = self.object.name
        ctx['side'] = 'sale'
        return ctx

# --- ACTIVATION VIEWS (Magic Buttons) ---

class SalesArticleActivationView(LoginRequiredMixin, UpdateView):
    """
    Active la partie VENTE sur un article existant (qui vient des Achats).
    URL: /ventes/articles/<pk>/activer/
    """
    model = Article
    form_class = ResaleConfigForm
    template_name = 'commerce/articles/sales_activation.html'
    
    def get_queryset(self):
        # On autorise l'accès même si is_sellable=False (car c'est le but de la vue)
        return Article.objects.filter(organization=self.request.current_org)

    def get_initial(self):
        return {'enable_resale': True}

    def form_valid(self, form):
        form.instance.is_sellable = True
        messages.success(self.request, "Version VENTE activée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('ventes:article_detail', args=[self.object.pk])
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Activer la vente : {self.object.name}"
        ctx['side'] = 'sale'
        return ctx

class PurchaseArticleActivationView(LoginRequiredMixin, UpdateView):
    """
    Active la partie ACHAT sur un article existant (qui vient des Ventes).
    URL: /achats/articles/<pk>/activer/
    """
    model = Article
    form_class = SourceConfigForm # On peut réutiliser ou simplifier
    template_name = 'commerce/articles/purchase_activation.html'
    
    def get_queryset(self):
        return Article.objects.filter(organization=self.request.current_org)

    def get_form_class(self):
        # Formulaire simple pour confirmer
        class ActivationForm(forms.ModelForm):
            class Meta:
                model = Article
                fields = [] # Pas de champs, juste confirmation
        return ActivationForm

    def form_valid(self, form):
        form.instance.is_buyable = True
        messages.success(self.request, "Version ACHAT activée avec succès.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('achats:article_detail', args=[self.object.pk])
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Activer l'achat : {self.object.name}"
        ctx['side'] = 'purchase'
        return ctx

"""
Vues pour le catalogue - Articles et Inventaire
(Vues legacy lot_* supprimées - utiliser views_unified.py)
"""

from django.contrib import messages
from django.db.models import Q

# ===== CATALOGUE ARTICLES =====
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Article, ArticleStock, ArticleCategory
from .forms import ArticleForm

class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'catalogue/article_list.html'
    context_object_name = 'articles'
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        qs = Article.objects.filter(organization=org)
        
        # Filtres simples
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
            
        cat = self.request.GET.get('category')
        if cat:
            qs = qs.filter(category_id=cat)
            
        atype = self.request.GET.get('type')
        if atype:
            qs = qs.filter(article_type=atype)
            
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'current_org', None)
        ctx['page_title'] = "Catalogue Articles"
        ctx['categories'] = ArticleCategory.objects.filter(organization=org)
        return ctx

class PurchaseArticleListView(ArticleListView):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_buyable=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Articles Achetés (Fournisseurs)"
        ctx['is_purchase_view'] = True
        return ctx

class SalesArticleListView(ArticleListView):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_sellable=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Articles Vendus (Clients)"
        ctx['is_sales_view'] = True
        return ctx

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'catalogue/article_form.html'
    
    def get_success_url(self):
        # 1. Explicit 'next' param
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
            
        # 2. Context-aware fallback
        if self.object.is_buyable and not self.object.is_sellable:
            return reverse_lazy('catalogue:article_list_purchase')
        elif self.object.is_sellable and not self.object.is_buyable:
            return reverse_lazy('catalogue:article_list_sales')
        return reverse_lazy('catalogue:article_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Nouvel Article"
        ctx['next_url'] = self.request.GET.get('next')
        return ctx

class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'catalogue/article_form.html'
    
    def get_success_url(self):
        # 1. Explicit 'next' param
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url

        # 2. Context-aware fallback
        if self.object.is_buyable and not self.object.is_sellable:
            return reverse_lazy('catalogue:article_list_purchase')
        elif self.object.is_sellable and not self.object.is_buyable:
            return reverse_lazy('catalogue:article_list_sales')
        return reverse_lazy('catalogue:article_list')
    
    def get_queryset(self):
        return Article.objects.filter(organization=getattr(self.request, 'current_org', None))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = getattr(self.request, 'current_org', None)
        return kwargs
        
    def form_valid(self, form):
        messages.success(self.request, "Article mis à jour.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f"Modifier {self.object.name}"
        ctx['next_url'] = self.request.GET.get('next')
        return ctx

class InventoryListView(LoginRequiredMixin, ListView):
    model = ArticleStock
    template_name = 'catalogue/inventory_list.html'
    context_object_name = 'stocks'
    
    def get_queryset(self):
        org = getattr(self.request, 'current_org', None)
        return ArticleStock.objects.filter(organization=org).select_related('article', 'location').order_by('article__name')
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = "Inventaire & Stock"
        return ctx

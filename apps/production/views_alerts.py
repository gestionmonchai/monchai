"""
Views for Alert/Reminder system.
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages

from .models_alerts import Alert


class AlertsListView(LoginRequiredMixin, ListView):
    """
    List all active alerts for the current organization.
    """
    model = Alert
    template_name = 'production/alerts_list.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        qs = Alert.objects.filter(
            organization=self.request.current_org
        )
        
        # Filter by status
        status = self.request.GET.get('status', 'active')
        if status == 'active':
            qs = qs.filter(status='active')
        elif status == 'completed':
            qs = qs.filter(status='completed')
        elif status == 'all':
            pass  # No filter
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        
        return qs.order_by('-priority', 'due_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Alertes & Rappels'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Alertes', 'url': None},
        ]
        
        # Counts for tabs
        org = self.request.current_org
        ctx['active_count'] = Alert.objects.filter(organization=org, status='active').count()
        ctx['completed_count'] = Alert.objects.filter(organization=org, status='completed').count()
        ctx['overdue_count'] = Alert.objects.filter(
            organization=org, 
            status='active',
            due_date__lt=timezone.now().date()
        ).count()
        
        # Filter options
        ctx['categories'] = Alert.CATEGORY_CHOICES
        ctx['priorities'] = Alert.PRIORITY_CHOICES
        ctx['types'] = Alert.TYPE_CHOICES
        
        return ctx


class AlertCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new alert/reminder.
    """
    model = Alert
    template_name = 'production/alert_form.html'
    fields = ['title', 'description', 'alert_type', 'category', 'priority', 'due_date', 'due_time']
    success_url = reverse_lazy('production:alerts_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.current_org
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Alerte « {form.instance.title} » créée.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Nouvelle alerte'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Alertes', 'url': reverse_lazy('production:alerts_list')},
            {'name': 'Nouvelle', 'url': None},
        ]
        return ctx


class AlertUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing alert.
    """
    model = Alert
    template_name = 'production/alert_form.html'
    fields = ['title', 'description', 'alert_type', 'category', 'priority', 'due_date', 'due_time', 'status']
    success_url = reverse_lazy('production:alerts_list')
    
    def get_queryset(self):
        return Alert.objects.filter(organization=self.request.current_org)
    
    def form_valid(self, form):
        messages.success(self.request, f"Alerte « {form.instance.title} » mise à jour.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Modifier l\'alerte'
        ctx['breadcrumb_items'] = [
            {'name': 'Production', 'url': '/production/'},
            {'name': 'Alertes', 'url': reverse_lazy('production:alerts_list')},
            {'name': 'Modifier', 'url': None},
        ]
        return ctx


class AlertCompleteView(LoginRequiredMixin, View):
    """
    Mark alert as completed (HTMX compatible).
    """
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk, organization=request.current_org)
        alert.mark_completed()
        
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f'<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Terminée</span>',
                content_type='text/html'
            )
        
        messages.success(request, f"Alerte « {alert.title} » marquée comme terminée.")
        return redirect('production:alerts_list')


class AlertDismissView(LoginRequiredMixin, View):
    """
    Dismiss alert (HTMX compatible).
    """
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk, organization=request.current_org)
        alert.dismiss()
        
        if request.headers.get('HX-Request'):
            return HttpResponse('', status=200)
        
        messages.info(request, f"Alerte « {alert.title} » ignorée.")
        return redirect('production:alerts_list')


class AlertSnoozeView(LoginRequiredMixin, View):
    """
    Snooze alert for specified hours (HTMX compatible).
    """
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk, organization=request.current_org)
        hours = int(request.POST.get('hours', 24))
        alert.snooze(hours=hours)
        
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f'<span class="badge bg-secondary"><i class="bi bi-clock me-1"></i>Reportée</span>',
                content_type='text/html'
            )
        
        messages.info(request, f"Alerte « {alert.title} » reportée de {hours}h.")
        return redirect('production:alerts_list')


class AlertDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete an alert.
    """
    model = Alert
    success_url = reverse_lazy('production:alerts_list')
    
    def get_queryset(self):
        return Alert.objects.filter(organization=self.request.current_org)
    
    def delete(self, request, *args, **kwargs):
        alert = self.get_object()
        messages.success(request, f"Alerte « {alert.title} » supprimée.")
        return super().delete(request, *args, **kwargs)

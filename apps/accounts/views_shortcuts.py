from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import UserShortcut
import json

@login_required
@require_POST
def add_shortcut(request):
    try:
        data = json.loads(request.body)
        url = data.get('url')
        title = data.get('title')
        organization = getattr(request, 'current_org', None)
        
        if not organization:
             return JsonResponse({'error': 'Aucune organisation active'}, status=400)
        
        if not url or not title:
            return JsonResponse({'error': 'URL et titre requis'}, status=400)
            
        # Create shortcut
        # Check duplicates (max 20 per user/org to prevent spam)
        count = UserShortcut.objects.filter(user=request.user, organization=organization).count()
        if count >= 20:
             return JsonResponse({'error': 'Limite de 20 raccourcis atteinte'}, status=400)
             
        if UserShortcut.objects.filter(user=request.user, organization=organization, url=url).exists():
             return JsonResponse({'error': 'Ce raccourci existe déjà'}, status=400)
             
        shortcut = UserShortcut.objects.create(
            user=request.user,
            organization=organization,
            url=url,
            title=title
        )
        
        return JsonResponse({
            'id': shortcut.id,
            'title': shortcut.title,
            'url': shortcut.url,
            'icon': shortcut.icon
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def delete_shortcut(request, shortcut_id):
    try:
        shortcut = get_object_or_404(UserShortcut, id=shortcut_id, user=request.user)
        shortcut.delete()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

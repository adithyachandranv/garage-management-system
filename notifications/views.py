from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, pk):
    # Allow GET for marking read via link click if needed, but POST is better for API
    # Let's support both for versatility
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # If there's a next param or link, redirect there
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    if notification.link:
        return redirect(notification.link)
        
    return redirect('notification_list')

@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('notification_list')

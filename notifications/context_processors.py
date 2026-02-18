def user_notifications(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        latest_notifications = request.user.notifications.all()[:5]
        return {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifications
        }
    return {}

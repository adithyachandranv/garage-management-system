from .models import Notification

def create_notification(recipient, title, message, notification_type, related_job=None, link=None):
    """
    Creates a new notification for the given recipient.
    """
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        related_job=related_job,
        link=link
    )

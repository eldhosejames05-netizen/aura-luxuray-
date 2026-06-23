import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

@shared_task(name='accounts.tasks.send_welcome_email_task')
def send_welcome_email_task(user_id):
    """
    Asynchronously sends a welcome email to the registered user.
    """
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist.")
        return False

    try:
        subject = 'Welcome to Aura Luxury!'
        html_message = render_to_string('emails/welcome.html', {
            'user': user
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject,
            plain_message,
            None,  # automatically uses DEFAULT_FROM_EMAIL
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.exception(f"Error sending welcome email to user {user.email}: {e}")
        return False

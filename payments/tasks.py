import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from orders.models import Order

logger = logging.getLogger(__name__)

@shared_task(name='payments.tasks.send_order_confirmation_email_task')
def send_order_confirmation_email_task(order_id, points_earned):
    """
    Asynchronously sends an order confirmation email to the user.
    """
    User = get_user_model()
    try:
        order = Order.objects.select_related('user').get(id=order_id)
        user = order.user
    except Order.DoesNotExist:
        logger.error(f"Order with id {order_id} does not exist.")
        return False

    try:
        subject = f'Your order is successful and payment is also successful - Order #{order.id}'
        html_message = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'user': user,
            'points_earned': points_earned
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
        logger.exception(f"Error sending order confirmation email for order #{order.id}: {e}")
        return False

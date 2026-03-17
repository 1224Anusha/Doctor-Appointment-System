from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_email_notification(to_email, subject, message_body):
    """
    Sends an Email notification using Django's configured SMTP backend.
    """
    try:
        # Check if email is valid and provided
        if not to_email:
            logger.warning("Attempted to send email but no destination address was provided.")
            return False
            
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(f"Email Sent to {to_email}. Subject: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Email to {to_email}: {str(e)}")
        return False

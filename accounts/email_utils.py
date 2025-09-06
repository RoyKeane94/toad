from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import os
import base64


def send_verification_email(user, request=None):
    """
    Send email verification email to the user.
    """
    # Generate verification token
    token = user.generate_email_verification_token()
    
    # Build verification URL
    if request:
        verification_url = request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': token})
        )
    else:
        # Fallback for when request is not available
        verification_url = f"{settings.SITE_URL}/accounts/verify-email/{token}/"
    
    # Read and encode the image
    image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
    image_data = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Render email template
    html_message = render_to_string('accounts/email/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
        'toad_image_data': image_data,
    })
    
    # Plain text version
    text_message = f"""
Hi {user.first_name},

Welcome to Toad! We're excited to have you on board.

To get started with your task management journey, please verify your email address by clicking the link below:

{verification_url}

If the link doesn't work, you can copy and paste it into your browser.

Security Notice: This verification link will expire in 24 hours for your security. If you didn't create a Toad account, you can safely ignore this email.

Once verified, you'll have full access to create grids, organize tasks, and boost your productivity with Toad's powerful task management tools.

Thanks for choosing Toad!

This email was sent to {user.email}. If you have any questions, please contact our support team.

© 2024 Toad. All rights reserved.
    """
    
    # Send email
    try:
        # Log email attempt
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to send verification email to {user.email}")
        
        send_mail(
            subject='Verify Your Email - Welcome to Toad!',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent verification email to {user.email}")
        return True
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return False


def send_password_reset_email(user, request=None):
    """
    Send password reset email to the user.
    """
    # Generate password reset token
    token = user.generate_password_reset_token()
    
    # Build password reset URL
    if request:
        reset_url = request.build_absolute_uri(
            reverse('accounts:reset_password', kwargs={'token': token})
        )
    else:
        # Fallback for when request is not available
        reset_url = f"{settings.SITE_URL}/accounts/reset-password/{token}/"
    
    # Read and encode the image
    image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
    image_data = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Render email template
    html_message = render_to_string('accounts/email/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
        'toad_image_data': image_data,
    })
    
    # Plain text version
    text_message = f"""
Hi {user.first_name},

You requested a password reset for your Toad account.

To reset your password, please click the link below:

{reset_url}

If the link doesn't work, you can copy and paste it into your browser.

Security Notice: This password reset link will expire in 1 hour for your security. If you didn't request a password reset, you can safely ignore this email.

If you have any questions, please contact our support team.

This email was sent to {user.email}.

© 2024 Toad. All rights reserved.
    """
    
    # Send email
    try:
        # Log email attempt
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to send password reset email to {user.email}")
        
        send_mail(
            subject='Reset Your Password - Toad',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent password reset email to {user.email}")
        return True
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False 


def send_joining_email(user, request=None, cta_url=None):
    """
    Send the post-verification welcome email with hero image.
    Sends different emails based on user tier.
    """
    # Build a default CTA if not provided
    if not cta_url:
        # Try to send them to their first project or project list
        base_url = settings.SITE_URL.rstrip('/')
        cta_url = f"{base_url}/projects/"  # generic fallback

    # Read and encode the image
    image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
    image_data = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

    # Determine template and content based on user tier
    user_tier = getattr(user, 'tier', 'free')  # Default to 'free' if tier not set
    
    if user_tier == 'beta':
        template_name = 'accounts/email/joining_email_beta.html'
        subject = "Welcome to Toad Beta — You're all set!"
        text_intro = "Thanks for joining the private beta and helping shape a calmer way to plan."
    elif user_tier == 'personal':
        template_name = 'accounts/email/joining_email_personal.html'
        subject = "Welcome to Toad Personal — You're all set!"
        text_intro = "Thanks for upgrading to Personal and supporting our mission to make planning calmer and more effective."
    else:  # free tier
        template_name = 'accounts/email/joining_email_free.html'
        subject = "Welcome to Toad — You're all set!"
        text_intro = "Thanks for joining us and helping shape a calmer way to plan."

    html_message = render_to_string(template_name, {
        'user': user,
        'toad_image_data': image_data,
        'cta_url': cta_url,
    })

    text_message = f"""
Hi {user.first_name or user.get_short_name()},

Welcome to Toad! Your email is verified and you're all set.

{text_intro}

Your first grid is ready and waiting. Head here to get started:
{cta_url}

If you have any feedback, reply to this email—I read every message.

— Tom, Founder of Toad
"""

    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to send {user_tier} joining email to {user.email}")
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Successfully sent {user_tier} joining email to {user.email}")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send {user_tier} joining email to {user.email}: {e}")
        return False
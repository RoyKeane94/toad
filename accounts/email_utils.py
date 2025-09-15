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
    # Check if user is subscribed to emails (verification emails should always be sent)
    # if not getattr(user, 'email_subscribed', True):
    #     return False
    
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

Once verified, you'll have full access to create grids, organise tasks, and boost your productivity with Toad's powerful task management tools.

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
    # Check if user is subscribed to emails (password reset emails should always be sent)
    # if not getattr(user, 'email_subscribed', True):
    #     return False
    
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
    # Check if user is subscribed to emails
    if not getattr(user, 'email_subscribed', True):
        return False
    
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


def send_test_email(recipient_email, email_type='simple', user=None):
    """
    Send a test email to verify email functionality.
    
    Args:
        recipient_email (str): Email address to send test email to
        email_type (str): Type of test email ('simple', 'verification', 'password_reset', 'joining')
        user (User, optional): User object for user-specific emails
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Load the Toad image
    image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
    image_data = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    
    if email_type == 'simple':
        return _send_simple_test_email(recipient_email, image_data)
    elif email_type == 'verification' and user:
        return _send_test_verification_email(user, recipient_email)
    elif email_type == 'password_reset' and user:
        return _send_test_password_reset_email(user, recipient_email)
    elif email_type == 'joining' and user:
        return _send_test_joining_email(user, recipient_email)
    else:
        logger.error(f"Invalid email type '{email_type}' or missing user for user-specific email")
        return False


def _send_simple_test_email(recipient_email, image_data):
    """
    Send a simple test email to verify email system functionality.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    subject = "Test Email - Toad Email System"
    
    text_message = f"""
Hi there!

This is a test email from the Toad email system.

If you're receiving this email, it means the email configuration is working correctly.

Email Details:
- From: {settings.DEFAULT_FROM_EMAIL}
- Backend: {settings.EMAIL_BACKEND}
- Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}
- Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}
- Site URL: {settings.SITE_URL}

This is an automated test email sent to verify the email system is functioning properly.

Best regards,
Toad Email System

© 2024 Toad. All rights reserved.
    """
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Email - Toad</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
        .content {{ padding: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 8px; font-size: 12px; color: #666; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .details {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .logo {{ max-width: 100px; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐸 Test Email - Toad Email System</h1>
        </div>
        
        <div class="content">
            <p>Hi there!</p>
            
            <p>This is a test email from the Toad email system.</p>
            
            <p class="success">✓ If you're receiving this email, it means the email configuration is working correctly.</p>
            
            <div class="details">
                <h3>Email Configuration Details:</h3>
                <ul>
                    <li><strong>From:</strong> {settings.DEFAULT_FROM_EMAIL}</li>
                    <li><strong>Backend:</strong> {settings.EMAIL_BACKEND}</li>
                    <li><strong>Host:</strong> {getattr(settings, 'EMAIL_HOST', 'Not set')}</li>
                    <li><strong>Port:</strong> {getattr(settings, 'EMAIL_PORT', 'Not set')}</li>
                    <li><strong>Site URL:</strong> {settings.SITE_URL}</li>
                </ul>
            </div>
            
            <p>This is an automated test email sent to verify the email system is functioning properly.</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>Toad Email System</p>
            <p>© 2024 Toad. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    """
    
    try:
        logger.info(f"Attempting to send test email to {recipient_email}")
        
        # Use test email sender if configured, otherwise fall back to default
        from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent test email to {recipient_email} from {from_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test email to {recipient_email}: {e}")
        return False


def _send_test_verification_email(user, recipient_email):
    """
    Send a test verification email using the test sender.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Generate verification token
    token = user.generate_email_verification_token()
    
    # Build verification URL
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

Once verified, you'll have full access to create grids, organise tasks, and boost your productivity with Toad's powerful task management tools.

Thanks for choosing Toad!

This email was sent to {recipient_email}. If you have any questions, please contact our support team.

© 2024 Toad. All rights reserved.
    """
    
    try:
        logger.info(f"Attempting to send test verification email to {recipient_email}")
        
        # Use test email sender if configured, otherwise fall back to default
        from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
        
        send_mail(
            subject='[TEST] Verify Your Email - Welcome to Toad!',
            message=text_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent test verification email to {recipient_email} from {from_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test verification email to {recipient_email}: {e}")
        return False


def _send_test_password_reset_email(user, recipient_email):
    """
    Send a test password reset email using the test sender.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Generate password reset token
    token = user.generate_password_reset_token()
    
    # Build password reset URL
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

This email was sent to {recipient_email}.

© 2024 Toad. All rights reserved.
    """
    
    try:
        logger.info(f"Attempting to send test password reset email to {recipient_email}")
        
        # Use test email sender if configured, otherwise fall back to default
        from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
        
        send_mail(
            subject='[TEST] Reset Your Password - Toad',
            message=text_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent test password reset email to {recipient_email} from {from_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test password reset email to {recipient_email}: {e}")
        return False


def _send_test_joining_email(user, recipient_email):
    """
    Send a test joining email using the test sender.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Build a default CTA
    base_url = settings.SITE_URL.rstrip('/')
    cta_url = f"{base_url}/projects/"
    
    # Read and encode the image
    image_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Toad Email Image.png')
    image_data = ""
    if os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine template and content based on user tier
    user_tier = getattr(user, 'tier', 'free')
    
    if user_tier == 'beta':
        template_name = 'accounts/email/joining_email_beta.html'
        subject = "[TEST] Welcome to Toad Beta — You're all set!"
        text_intro = "Thanks for joining the private beta and helping shape a calmer way to plan."
    elif user_tier == 'personal':
        template_name = 'accounts/email/joining_email_personal.html'
        subject = "[TEST] Welcome to Toad Personal — You're all set!"
        text_intro = "Thanks for upgrading to Personal and supporting our mission to make planning calmer and more effective."
    else:  # free tier
        template_name = 'accounts/email/joining_email_free.html'
        subject = "[TEST] Welcome to Toad — You're all set!"
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

This email was sent to {recipient_email}.
"""
    
    try:
        logger.info(f"Attempting to send test {user_tier} joining email to {recipient_email}")
        
        # Use test email sender if configured, otherwise fall back to default
        from_email = getattr(settings, 'TEST_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Successfully sent test {user_tier} joining email to {recipient_email} from {from_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test {user_tier} joining email to {recipient_email}: {e}")
        return False
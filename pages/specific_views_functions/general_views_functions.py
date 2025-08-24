from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from ..models import ContactSubmission
import logging

logger = logging.getLogger(__name__)

# Contact Form Helper Functions

def validate_contact_form_data(form_data):
    """Validate contact form data and return cleaned data or errors"""
    name = form_data.get('name', '').strip()
    email = form_data.get('email', '').strip()
    category = form_data.get('category', 'general')
    subject = form_data.get('subject', '').strip()
    message = form_data.get('message', '').strip()
    
    # Basic validation
    errors = []
    if not name:
        errors.append('Name is required')
    if not email:
        errors.append('Email is required')
    elif '@' not in email:  # Basic email validation
        errors.append('Please enter a valid email address')
    if not subject:
        errors.append('Subject is required')
    if not message:
        errors.append('Message is required')
    
    if errors:
        return False, errors, None
    
    return True, None, {
        'name': name,
        'email': email,
        'category': category,
        'subject': subject,
        'message': message
    }

def create_contact_submission(validated_data, user=None):
    """Create a contact submission with validated data"""
    try:
        submission = ContactSubmission.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            category=validated_data['category'],
            subject=validated_data['subject'],
            message=validated_data['message'],
            user=user if user and user.is_authenticated else None
        )
        
        logger.info(f"New contact submission from {validated_data['email']}: {validated_data['subject']}")
        return True, submission
        
    except Exception as e:
        logger.error(f"Error creating contact submission: {str(e)}")
        return False, None

def handle_contact_form_success(request, is_htmx=False):
    """Handle successful contact form submission"""
    success_message = 'Thank you for your message! We\'ll get back to you within 24 hours.'
    
    if is_htmx:
        return render(request, 'pages/general/bumf/contact_us.html', {
            'success': True,
            'message': success_message
        })
    else:
        messages.success(request, success_message)
        return render(request, 'pages/general/bumf/contact_us.html', {
            'success': True
        })

def handle_contact_form_error(request, error_message, form_data=None, is_htmx=False):
    """Handle contact form errors"""
    context = {
        'error': error_message,
        'form_data': form_data or {}
    }
    
    if is_htmx:
        return render(request, 'pages/general/bumf/contact_us.html', context)
    else:
        messages.error(request, error_message)
        return render(request, 'pages/general/bumf/contact_us.html', context)

def process_contact_form_submission(request):
    """Process the entire contact form submission workflow"""
    # Validate form data
    is_valid, errors, validated_data = validate_contact_form_data(request.POST)
    
    if not is_valid:
        error_message = 'Please correct the following errors: ' + ', '.join(errors)
        return handle_contact_form_error(
            request, 
            error_message, 
            request.POST, 
            request.headers.get('HX-Request')
        )
    
    # Create contact submission
    success, submission = create_contact_submission(validated_data, request.user)
    
    if success:
        return handle_contact_form_success(request, request.headers.get('HX-Request'))
    else:
        error_message = 'Sorry, there was an error sending your message. Please try again.'
        return handle_contact_form_error(
            request, 
            error_message, 
            request.POST, 
            request.headers.get('HX-Request')
        )

# Template Rendering Helpers

def render_simple_template(request, template_name, context=None):
    """Render a simple template with optional context"""
    if context is None:
        context = {}
    
    # Ensure user is always in context for authentication checks
    if 'user' not in context:
        context['user'] = request.user
    
    return render(request, template_name, context)

def get_contact_form_context():
    """Get default context for contact form"""
    return {
        'categories': [
            ('general', 'General Inquiry'),
            ('bug_report', 'Bug Report'),
            ('feature_request', 'Feature Request'),
            ('account_help', 'Account Help'),
            ('technical_support', 'Technical Support'),
            ('other', 'Other')
        ]
    }

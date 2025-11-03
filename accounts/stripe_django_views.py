import stripe
import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
import json
import logging

logger = logging.getLogger(__name__)

# Set your secret key from environment variable
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Check if Stripe is properly configured
if not stripe.api_key:
    logger.error("STRIPE_SECRET_KEY environment variable is not set!")

@login_required
def stripe_checkout_view(request):
    """
    Display the Stripe checkout page for Toad Personal subscription
    """
    logger.info(f"Stripe checkout view accessed by user: {request.user.email}")
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured - cannot display checkout page")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('pages:project_list')
        
        logger.info("Stripe API key is configured, proceeding...")
        
        # Test template rendering
        logger.info("Rendering Stripe checkout template...")
        response = render(request, 'accounts/pages/stripe/toad_personal_stripe_checkout.html')
        logger.info("Template rendered successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in stripe_checkout_view: {e}", exc_info=True)
        # Return a simple error page instead of raising
        from django.http import HttpResponse
        return HttpResponse(f"Error loading checkout page: {str(e)}", status=500)

@login_required
def create_checkout_session(request):
    """
    Create a Stripe checkout session for Toad Personal subscription
    """
    if request.method != 'POST':
        return redirect('accounts:stripe_checkout')
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('accounts:stripe_checkout')
        
        # Get the price ID from the form (for live mode)
        price_id = request.POST.get('price_id', 'price_1S308oImvDyA3xukKtKWjXPI')
        
        # For live mode, we'll use the price ID directly instead of lookup key
        # Get the price from Stripe
        try:
            price = stripe.Price.retrieve(price_id, expand=['product'])
        except stripe.error.InvalidRequestError:
            # Fallback to lookup key method for backward compatibility
            lookup_key = request.POST.get('lookup_key', 'Toad_-_Personal-c6aa14b')
            prices = stripe.Price.list(
                lookup_keys=[lookup_key],
                expand=['data.product']
            )
            if not prices.data:
                messages.error(request, 'Subscription plan not found. Please contact support.')
                return redirect('accounts:stripe_checkout')
            price = prices.data[0]
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('accounts:stripe_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('accounts:stripe_cancel')),
            customer_email=request.user.email,  # Pre-fill email
            metadata={
                'user_id': str(request.user.id),
                'user_email': request.user.email,
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_checkout_session: {e}")
        messages.error(request, 'There was an error processing your payment. Please try again.')
        return redirect('accounts:stripe_checkout')
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('accounts:stripe_checkout')

@login_required
def stripe_success_view(request):
    """
    Handle successful Stripe checkout
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session. Please contact support.')
        return redirect('pages:project_list')
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify the session belongs to the current user
        if session.metadata.get('user_id') != str(request.user.id):
            messages.error(request, 'Session verification failed.')
            return redirect('pages:project_list')
        
        # Update user tier to personal
        request.user.tier = 'personal'
        request.user.save()
        
        # Send joining email after successful payment (user is already verified)
        try:
            from .email_utils import send_joining_email
            import threading
            
            def send_email_async():
                try:
                    # Build CTA URL for their first grid
                    from django.urls import reverse
                    project_list_path = reverse('pages:project_list')
                    base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                    cta_url = f"{base_url}{project_list_path}" if base_url else None
                    
                    email_sent = send_joining_email(request.user, request, cta_url)
                    logger.info(f"Joining email sent after payment: {email_sent} for {request.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send joining email after payment to {request.user.email}: {e}")
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start email thread after payment for {request.user.email}: {e}")
        
        # Log the successful subscription
        logger.info(f"User {request.user.email} successfully subscribed to Personal plan. Session: {session_id}")
        
        messages.success(request, 'Welcome to Toad Personal! Your subscription is now active. Check your email for your welcome message!')
        
        return render(request, 'accounts/pages/stripe/toad_personal_stripe_success.html', {
            'session_id': session_id,
            'user': request.user
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in stripe_success_view: {e}")
        messages.error(request, 'There was an error verifying your payment. Please contact support.')
        return redirect('pages:project_list')
    except Exception as e:
        logger.error(f"Unexpected error in stripe_success_view: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('pages:project_list')

@login_required
def stripe_cancel_view(request):
    """
    Handle cancelled Stripe checkout
    """
    # Ensure user stays on free tier if they cancel
    if hasattr(request.user, 'tier') and request.user.tier != 'free':
        request.user.tier = 'free'
        request.user.save()
        logger.info(f'User {request.user.email} tier reset to free after canceling checkout')
    
    return render(request, 'accounts/pages/stripe/toad_personal_cancel.html')

@login_required
def create_portal_session(request):
    """
    Create a Stripe customer portal session for managing billing
    """
    if request.method != 'POST':
        return redirect('accounts:account_settings')
    
    session_id = request.POST.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session. Please contact support.')
        return redirect('accounts:account_settings')
    
    try:
        # Retrieve the checkout session to get customer ID
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify the session belongs to the current user
        if checkout_session.metadata.get('user_id') != str(request.user.id):
            messages.error(request, 'Session verification failed.')
            return redirect('accounts:account_settings')
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=checkout_session.customer,
            return_url=request.build_absolute_uri(reverse('accounts:account_settings')),
        )
        
        return redirect(portal_session.url, code=303)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_portal_session: {e}")
        messages.error(request, 'There was an error accessing your billing portal. Please contact support.')
        return redirect('accounts:account_settings')
    except Exception as e:
        logger.error(f"Unexpected error in create_portal_session: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('accounts:account_settings')

@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhooks
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_12345')
    
    # Check if webhook secret is configured
    if endpoint_secret == 'whsec_12345':
        logger.error("STRIPE_WEBHOOK_SECRET not properly configured")
        return HttpResponse(status=400)
    
    # Log webhook received
    logger.info(f"Webhook received: {request.META.get('HTTP_STRIPE_SIGNATURE', 'No signature')}")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f"Webhook event type: {event['type']}")
    except ValueError:
        logger.error("Invalid payload in webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        logger.info('🔔 Payment succeeded!')
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('user_id')
        plan_type = session.get('metadata', {}).get('plan_type', 'personal')
        
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
                
                # Update tier based on plan_type in metadata, default to personal for backward compatibility
                if plan_type == 'pro':
                    user.tier = 'pro'
                    logger.info(f'User {user.email} tier updated to pro via webhook')
                else:
                    user.tier = 'personal'
                    logger.info(f'User {user.email} tier updated to personal via webhook')
                
                user.save()
            except User.DoesNotExist:
                logger.error(f'User with ID {user_id} not found in webhook')
            except Exception as e:
                logger.error(f'Error updating user tier in webhook: {e}')
        
    elif event['type'] == 'customer.subscription.created':
        logger.info(f'Subscription created: {event["id"]}')
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        if customer_id:
            try:
                # Find user by customer ID in metadata or by email
                from django.contrib.auth import get_user_model
                User = get_user_model()
                # You might need to store customer_id in user model or find by email
                # For now, we'll rely on checkout.session.completed
                logger.info(f'Subscription created for customer: {customer_id}')
            except Exception as e:
                logger.error(f'Error handling subscription created: {e}')
        
    elif event['type'] == 'customer.subscription.updated':
        logger.info(f'Subscription updated: {event["id"]}')
        subscription = event['data']['object']
        status = subscription.get('status')
        
        if status == 'active':
            # Subscription is active, ensure user has personal tier
            customer_id = subscription.get('customer')
            logger.info(f'Subscription active for customer: {customer_id}')
        elif status in ['canceled', 'unpaid', 'past_due']:
            # Subscription is inactive, you might want to downgrade user
            customer_id = subscription.get('customer')
            logger.info(f'Subscription inactive for customer: {customer_id}')
        
    elif event['type'] == 'customer.subscription.deleted':
        logger.info(f'Subscription canceled: {event["id"]}')
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        if customer_id:
            try:
                # Find user and downgrade to free tier
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Try to find user by customer_id in metadata or by email
                # For now, we'll log it and handle manually if needed
                logger.info(f'Subscription canceled for customer: {customer_id}')
                logger.warning('Manual intervention may be needed to downgrade user tier')
            except Exception as e:
                logger.error(f'Error handling subscription deletion: {e}')
        
    elif event['type'] == 'entitlements.active_entitlement_summary.updated':
        logger.info(f'Active entitlement summary updated: {event["id"]}')
    
    return JsonResponse({'status': 'success'})


# Pro Plan Stripe Views

@login_required
def stripe_checkout_pro_view(request):
    """
    Display the Stripe checkout page for Toad Pro subscription
    """
    logger.info(f"Stripe Pro checkout view accessed by user: {request.user.email}")
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured - cannot display checkout page")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('pages:project_list')
        
        logger.info("Stripe API key is configured, proceeding...")
        
        # Test template rendering
        logger.info("Rendering Stripe Pro checkout template...")
        response = render(request, 'accounts/pages/stripe/toad_pro_stripe_checkout.html')
        logger.info("Template rendered successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in stripe_checkout_pro_view: {e}", exc_info=True)
        from django.http import HttpResponse
        return HttpResponse(f"Error loading checkout page: {str(e)}", status=500)

@login_required
def create_checkout_session_pro(request):
    """
    Create a Stripe checkout session for Toad Pro subscription
    """
    if request.method != 'POST':
        return redirect('accounts:stripe_checkout_pro')
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('accounts:stripe_checkout_pro')
        
        # Get the price ID from the form (for live mode)
        # Pro plan price
        price_id = request.POST.get('price_id', 'price_1SPN4iImvDyA3xuknMiIWMe5')
        
        # For live mode, we'll use the price ID directly instead of lookup key
        # Get the price from Stripe
        try:
            price = stripe.Price.retrieve(price_id, expand=['product'])
        except stripe.error.InvalidRequestError:
            # Fallback to lookup key method for backward compatibility
            lookup_key = request.POST.get('lookup_key', 'Toad_-_Pro-PRICE_KEY_HERE')
            prices = stripe.Price.list(
                lookup_keys=[lookup_key],
                expand=['data.product']
            )
            if not prices.data:
                messages.error(request, 'Subscription plan not found. Please contact support.')
                return redirect('accounts:stripe_checkout_pro')
            price = prices.data[0]
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('accounts:stripe_success_pro')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('accounts:stripe_cancel_pro')),
            customer_email=request.user.email,  # Pre-fill email
            metadata={
                'user_id': str(request.user.id),
                'user_email': request.user.email,
                'plan_type': 'pro',
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_checkout_session_pro: {e}")
        messages.error(request, 'There was an error processing your payment. Please try again.')
        return redirect('accounts:stripe_checkout_pro')
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session_pro: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('accounts:stripe_checkout_pro')

@login_required
def stripe_success_pro_view(request):
    """
    Handle successful Stripe Pro checkout
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session. Please contact support.')
        return redirect('pages:project_list')
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify the session belongs to the current user
        if session.metadata.get('user_id') != str(request.user.id):
            messages.error(request, 'Session verification failed.')
            return redirect('pages:project_list')
        
        # Update user tier to pro
        request.user.tier = 'pro'
        request.user.save()
        
        # Send joining email after successful payment (user is already verified)
        try:
            from .email_utils import send_joining_email
            import threading
            
            def send_email_async():
                try:
                    # Build CTA URL for their first grid
                    from django.urls import reverse
                    project_list_path = reverse('pages:project_list')
                    base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                    cta_url = f"{base_url}{project_list_path}" if base_url else None
                    
                    email_sent = send_joining_email(request.user, request, cta_url)
                    logger.info(f"Joining email sent after payment: {email_sent} for {request.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send joining email after payment to {request.user.email}: {e}")
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start email thread after payment for {request.user.email}: {e}")
        
        # Log the successful subscription
        logger.info(f"User {request.user.email} successfully subscribed to Pro plan. Session: {session_id}")
        
        messages.success(request, 'Welcome to Toad Pro! Your subscription is now active. Check your email for your welcome message!')
        
        return render(request, 'accounts/pages/stripe/toad_pro_stripe_success.html', {
            'session_id': session_id,
            'user': request.user
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in stripe_success_pro_view: {e}")
        messages.error(request, 'There was an error verifying your payment. Please contact support.')
        return redirect('pages:project_list')
    except Exception as e:
        logger.error(f"Unexpected error in stripe_success_pro_view: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('pages:project_list')

@login_required
def stripe_cancel_pro_view(request):
    """
    Handle cancelled Stripe Pro checkout
    """
    # Ensure user stays on free tier if they cancel
    if hasattr(request.user, 'tier') and request.user.tier != 'free':
        request.user.tier = 'free'
        request.user.save()
        logger.info(f'User {request.user.email} tier reset to free after canceling checkout')
    
    return render(request, 'accounts/pages/stripe/toad_pro_stripe_cancel.html')

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

PERSONAL_PRICE_ID = os.environ.get('STRIPE_PERSONAL_PRICE_ID', 'price_1S308oImvDyA3xukKtKWjXPI')
PRO_PRICE_ID = os.environ.get('STRIPE_PRO_PRICE_ID', 'price_1SPN4iImvDyA3xuknMiIWMe5')

PRICE_TIER_MAP = {
    PERSONAL_PRICE_ID: 'personal',
    PRO_PRICE_ID: 'pro',
}


def update_subscription_metadata_with_team_info(subscription_group):
    """
    Update Stripe subscription metadata to reflect current team member count
    This helps admins see active users in the Stripe portal
    """
    if not subscription_group or not subscription_group.stripe_subscription_id:
        return
    
    try:
        from accounts.models import TeamInvitation
        current_members_count = subscription_group.get_active_members_count()
        pending_count = TeamInvitation.objects.filter(
            subscription_group=subscription_group,
            status='pending'
        ).count()
        total_usage = current_members_count + pending_count
        
        stripe.Subscription.modify(
            subscription_group.stripe_subscription_id,
            metadata={
                'active_members': str(current_members_count),
                'pending_invitations': str(pending_count),
                'total_usage': str(total_usage),
                'total_seats': str(subscription_group.quantity),
                'available_seats': str(subscription_group.quantity - total_usage),
            }
        )
        logger.info(f'Updated subscription {subscription_group.stripe_subscription_id} metadata: {current_members_count} active, {pending_count} pending')
    except stripe.error.StripeError as e:
        logger.error(f"Error updating subscription metadata: {e}")
    except Exception as e:
        logger.error(f"Unexpected error updating subscription metadata: {e}", exc_info=True)


def update_user_tier_for_customer(customer_id, tier=None, status=None):
    """
    Update the user's tier based on Stripe customer/subscription status.
    """
    if not customer_id:
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.filter(stripe_customer_id=customer_id).first()
        if not user:
            logger.warning(f"No user found with stripe_customer_id={customer_id} when updating tier.")
            return

        original_tier = user.tier

        if status and status not in ['active', 'trialing']:
            # Subscription is no longer active – downgrade to free
            if user.tier != 'free':
                user.tier = 'free'
                user.save(update_fields=['tier'])
                logger.info(f"User {user.email} downgraded to free (Stripe status: {status}).")
            return

        if tier and tier != user.tier:
            user.tier = tier
            user.save(update_fields=['tier'])
            logger.info(f"User {user.email} tier updated from {original_tier} to {tier} based on Stripe portal change.")

    except Exception as exc:
        logger.error(f"Failed to update tier for customer {customer_id}: {exc}")

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
        customer_id = session.get('customer')
        update_fields = ['tier']
        if customer_id and getattr(request.user, 'stripe_customer_id', None) != customer_id:
            request.user.stripe_customer_id = customer_id
            update_fields.append('stripe_customer_id')
        request.user.save(update_fields=update_fields)
        
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
    Supports both individual and team subscriptions
    Configured to allow subscription updates but prevent cancellation of active subscriptions
    """
    if not stripe.api_key:
        logger.error("Stripe API key not configured - cannot create billing portal session")
        messages.error(request, 'Billing system is not configured. Please contact support.')
        return redirect('accounts:account_settings')

    # Check if user is a team admin with a team subscription
    from accounts.models import SubscriptionGroup
    subscription_group = SubscriptionGroup.objects.filter(admin=request.user, is_active=True).first()
    
    # Create or retrieve portal configuration
    # This ensures subscription updates are allowed but cancellation is disabled
    portal_config_id = None
    try:
        # Try to find existing configuration
        configurations = stripe.billing_portal.Configuration.list(limit=10)
        
        # Look for our configuration or use the first one
        existing_config = None
        for config in configurations.data:
            # Check if this config has cancellation disabled
            if hasattr(config, 'features') and hasattr(config.features, 'subscription_cancel'):
                if not config.features.subscription_cancel.enabled:
                    existing_config = config
                    break
        
        if existing_config:
            portal_config_id = existing_config.id
            logger.info(f"Using existing portal configuration: {portal_config_id}")
        elif configurations.data:
            # Use first existing config and update it
            existing_config = configurations.data[0]
            portal_config_id = existing_config.id
            try:
                # Update the configuration - Stripe API uses nested dict structure
                stripe.billing_portal.Configuration.modify(
                    portal_config_id,
                    features={
                        'subscription_update': {
                            'enabled': True,
                            'proration_behavior': 'always_invoice',
                            'default_allowed_updates': ['quantity'],
                        },
                        'subscription_cancel': {
                            'enabled': False,  # Prevent cancellation
                        },
                        'payment_method_update': {
                            'enabled': True,
                        },
                        'invoice_history': {
                            'enabled': True,
                        },
                    },
                    business_profile={
                        'headline': 'Manage your Toad subscription',
                    },
                )
                logger.info(f"Updated portal configuration: {portal_config_id}")
            except stripe.error.StripeError as e:
                logger.warning(f"Could not update portal configuration: {e}. Using existing configuration.")
        else:
            # Create new configuration
            config = stripe.billing_portal.Configuration.create(
                features={
                    'subscription_update': {
                        'enabled': True,
                        'proration_behavior': 'always_invoice',
                        'default_allowed_updates': ['quantity'],
                    },
                    'subscription_cancel': {
                        'enabled': False,  # Prevent cancellation
                    },
                    'payment_method_update': {
                        'enabled': True,
                    },
                    'invoice_history': {
                        'enabled': True,
                    },
                },
                business_profile={
                    'headline': 'Manage your Toad subscription',
                },
            )
            portal_config_id = config.id
            logger.info(f"Created new portal configuration: {portal_config_id}")
    except stripe.error.StripeError as e:
        logger.error(f"Error managing portal configuration: {e}. Portal may use default settings.")
        portal_config_id = None
    except Exception as e:
        logger.error(f"Unexpected error managing portal configuration: {e}", exc_info=True)
        portal_config_id = None
    
    if subscription_group and subscription_group.stripe_subscription_id:
        # For team subscriptions, get the customer ID from the subscription
        try:
            subscription = stripe.Subscription.retrieve(subscription_group.stripe_subscription_id)
            customer_id = subscription.get('customer')
            
            if not customer_id:
                messages.error(request, 'Unable to access billing portal. Please contact support.')
                return redirect('accounts:manage_team')
            
            # Create portal session for team subscription
            portal_params = {
                'customer': customer_id,
                'return_url': request.build_absolute_uri(reverse('accounts:manage_team')),
            }
            if portal_config_id:
                portal_params['configuration'] = portal_config_id
            
            portal_session = stripe.billing_portal.Session.create(**portal_params)
            return redirect(portal_session.url, code=303)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error in create_portal_session (team): {e}")
            messages.error(request, 'We could not open your billing portal. Please try again or contact support.')
            return redirect('accounts:manage_team')
        except Exception as e:
            logger.error(f"Unexpected error in create_portal_session (team): {e}")
            messages.error(request, 'An unexpected error occurred. Please contact support.')
            return redirect('accounts:manage_team')
    
    # For individual subscriptions
    customer_id = getattr(request.user, 'stripe_customer_id', None)
    if not customer_id:
        messages.info(request, 'Upgrade to a paid plan to unlock billing management.')
        return redirect('accounts:manage_subscription')
    
    try:
        portal_params = {
            'customer': customer_id,
            'return_url': request.build_absolute_uri(reverse('accounts:account_settings')),
        }
        if portal_config_id:
            portal_params['configuration'] = portal_config_id
        
        portal_session = stripe.billing_portal.Session.create(**portal_params)
        return redirect(portal_session.url, code=303)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_portal_session: {e}")
        messages.error(request, 'We could not open your billing portal. Please try again or contact support.')
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
                
                customer_id = session.get('customer')
                # Update tier based on plan_type in metadata, default to personal for backward compatibility
                if plan_type == 'pro':
                    user.tier = 'pro'
                    logger.info(f'User {user.email} tier updated to pro via webhook')
                else:
                    user.tier = 'personal'
                    logger.info(f'User {user.email} tier updated to personal via webhook')
                update_fields = ['tier']
                if customer_id and getattr(user, 'stripe_customer_id', None) != customer_id:
                    user.stripe_customer_id = customer_id
                    update_fields.append('stripe_customer_id')
                user.save(update_fields=update_fields)
            except User.DoesNotExist:
                logger.error(f'User with ID {user_id} not found in webhook')
            except Exception as e:
                logger.error(f'Error updating user tier in webhook: {e}')
        
    elif event['type'] == 'customer.subscription.created':
        logger.info(f'Subscription created: {event["id"]}')
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        price = None
        items = subscription.get('items', {}).get('data', [])
        if items:
            price = items[0].get('price', {}).get('id')
        
        if customer_id:
            try:
                tier = PRICE_TIER_MAP.get(price)
                update_user_tier_for_customer(customer_id, tier=tier, status=status)
            except Exception as e:
                logger.error(f'Error handling subscription created: {e}')
        
    elif event['type'] == 'customer.subscription.updated':
        logger.info(f'Subscription updated: {event["id"]}')
        subscription = event['data']['object']
        status = subscription.get('status')
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        price = None
        items = subscription.get('items', {}).get('data', [])
        quantity = None
        if items:
            price = items[0].get('price', {}).get('id')
            quantity = items[0].get('quantity')
            logger.info(f'Subscription {subscription_id} has quantity: {quantity}, price: {price}')
        
        # Check if this is a team subscription and update quantity
        from accounts.models import SubscriptionGroup, TeamInvitation
        subscription_group = SubscriptionGroup.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription_group:
            logger.info(f'Found SubscriptionGroup for subscription {subscription_id}: current quantity={subscription_group.quantity}')
            
            if quantity is not None:
                # Update the subscription group quantity to match Stripe
                old_quantity = subscription_group.quantity
                
                if old_quantity != quantity:
                    subscription_group.quantity = quantity
                    subscription_group.save(update_fields=['quantity'])
                    # Refresh from database to confirm the save
                    subscription_group.refresh_from_db()
                    logger.info(f'✅ Updated SubscriptionGroup quantity from {old_quantity} to {quantity} for subscription {subscription_id} (confirmed: {subscription_group.quantity})')
                else:
                    logger.info(f'SubscriptionGroup quantity already matches Stripe: {quantity}')
                
                # Check if quantity was reduced below current usage
                current_members_count = subscription_group.get_active_members_count()
                pending_count = TeamInvitation.objects.filter(
                    subscription_group=subscription_group,
                    status='pending'
                ).count()
                current_usage = current_members_count + pending_count
                
                if quantity < current_usage:
                    logger.warning(f'Team subscription {subscription_id} quantity ({quantity}) is below current usage ({current_usage}). Admin may need to remove members or cancel invitations.')
                    # Optionally: Cancel oldest pending invitations if quantity is too low
                    if pending_count > 0 and quantity < current_members_count:
                        # Cancel pending invitations to free up seats
                        excess_pending = current_usage - quantity
                        pending_invitations = TeamInvitation.objects.filter(
                            subscription_group=subscription_group,
                            status='pending'
                        ).order_by('created_at')[:excess_pending]
                        
                        for invitation in pending_invitations:
                            invitation.status = 'declined'
                            invitation.save()
                            logger.info(f'Cancelled pending invitation {invitation.id} due to seat reduction')
                
                # Update subscription metadata with current team info
                try:
                    update_subscription_metadata_with_team_info(subscription_group)
                except Exception as e:
                    logger.error(f'Error updating subscription metadata: {e}', exc_info=True)
            else:
                logger.warning(f'No quantity found in subscription {subscription_id} items')
        else:
            logger.info(f'No SubscriptionGroup found for subscription {subscription_id} - may be individual subscription')
        
        if customer_id:
            tier = PRICE_TIER_MAP.get(price) if status in ['active', 'trialing'] else None
            update_user_tier_for_customer(customer_id, tier=tier, status=status)
        
    elif event['type'] == 'customer.subscription.deleted':
        logger.info(f'Subscription canceled: {event["id"]}')
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        # Check if this is a team subscription
        from accounts.models import SubscriptionGroup
        subscription_group = SubscriptionGroup.objects.filter(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription_group:
            # This is a team subscription - ensure it's marked as inactive
            # (may have already been done by the cancel_team_subscription_view)
            was_active = subscription_group.is_active
            subscription_group.is_active = False
            subscription_group.save(update_fields=['is_active'])
            
            if was_active:
                logger.info(f'Team subscription canceled via webhook: {subscription_id}')
                # Only process if the subscription was still active
                # (if it was already canceled via the view, everything is already done)
                
                # Delete all grids and downgrade all members to free (including admin, who is now a member)
                from pages.models import Project
                members = subscription_group.members.all()
                total_grids_deleted = 0
                
                for member in members:
                    # Delete all projects (grids) for this member
                    member_projects = Project.objects.filter(user=member)
                    grids_deleted = member_projects.count()
                    member_projects.delete()
                    total_grids_deleted += grids_deleted
                    
                    # Downgrade member to free
                    if member.tier != 'free':
                        member.tier = 'free'
                        member.team_admin = None
                        member.save(update_fields=['tier', 'team_admin'])
                        logger.info(f'Team member {member.email} downgraded to free via webhook. {grids_deleted} grid(s) deleted.')
                
                # If admin is not in members list (shouldn't happen with new logic, but handle edge case)
                if subscription_group.admin not in members:
                    admin_projects = Project.objects.filter(user=subscription_group.admin)
                    admin_grids_deleted = admin_projects.count()
                    admin_projects.delete()
                    total_grids_deleted += admin_grids_deleted
                    
                    # Downgrade admin to free if not already
                    if subscription_group.admin.tier != 'free':
                        subscription_group.admin.tier = 'free'
                        subscription_group.admin.save(update_fields=['tier'])
                        logger.info(f'Team admin {subscription_group.admin.email} downgraded to free via webhook. {admin_grids_deleted} grid(s) deleted.')
                
                logger.info(f'Team subscription cancellation complete: {total_grids_deleted} total grid(s) deleted, all members downgraded to free')
            else:
                logger.info(f'Team subscription {subscription_id} was already marked inactive - webhook confirms cancellation')
        
        if customer_id:
            try:
                update_user_tier_for_customer(customer_id, tier=None, status='canceled')
            except Exception as e:
                logger.error(f'Error handling subscription deletion: {e}')
        
    elif event['type'] == 'entitlements.active_entitlement_summary.updated':
        logger.info(f'Active entitlement summary updated: {event["id"]}')
    
    return JsonResponse({'status': 'success'})


# Pro Plan Stripe Views

@login_required
def stripe_checkout_pro_view(request):
    """
    Display the Stripe checkout page for Team Toad subscription
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
        customer_id = session.get('customer')
        update_fields = ['tier']
        if customer_id and getattr(request.user, 'stripe_customer_id', None) != customer_id:
            request.user.stripe_customer_id = customer_id
            update_fields.append('stripe_customer_id')
        request.user.save(update_fields=update_fields)
        
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
        
        messages.success(request, 'Welcome to Team Toad! Your subscription is now active. Check your email for your welcome message!')
        
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


@login_required
def stripe_checkout_team_view(request):
    """
    Display the Stripe checkout page for Team Toad subscription with quantity selector
    Handles trial conversions by pre-populating the quantity from existing subscription group
    """
    logger.info(f"Stripe Team checkout view accessed by user: {request.user.email}")
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured - cannot display checkout page")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('pages:project_list')
        
        logger.info("Stripe API key is configured, proceeding...")
        
        # Check if user is converting from a trial subscription
        from accounts.models import SubscriptionGroup
        default_quantity = 2
        is_trial_conversion = False
        subscription_group = SubscriptionGroup.objects.filter(
            admin=request.user, 
            is_active=True,
            stripe_subscription_id__isnull=True  # Trial subscriptions have no Stripe ID
        ).first()
        
        # Get current usage data for trial conversions
        current_members_count = 0
        pending_invitations_count = 0
        members_list = []
        invitations_list = []
        
        if subscription_group:
            default_quantity = subscription_group.quantity
            is_trial_conversion = True
            logger.info(f"Trial conversion detected: pre-populating with {default_quantity} seats")
            
            # Get current members (excluding admin)
            members = subscription_group.members.exclude(id=request.user.id)
            current_members_count = members.count()
            members_list = [{'id': m.id, 'email': m.email, 'name': f"{m.first_name} {m.last_name}".strip() or m.email} for m in members]
            
            # Get pending invitations
            from accounts.models import TeamInvitation
            pending_invitations = subscription_group.invitations.filter(status='pending')
            pending_invitations_count = pending_invitations.count()
            invitations_list = [{'id': inv.id, 'email': inv.invited_email} for inv in pending_invitations]
        
        # Calculate open seats (quantity - 1 for admin - members - pending invitations)
        open_seats_count = max(0, default_quantity - 1 - current_members_count - pending_invitations_count)
        open_seats_list = [{'index': i + 1} for i in range(open_seats_count)]
        
        # Render team checkout template with quantity selector
        context = {
            'default_quantity': default_quantity,
            'is_trial_conversion': is_trial_conversion,
            'price_per_seat': 5,  # £5 per seat/month
            'current_members_count': current_members_count,
            'pending_invitations_count': pending_invitations_count,
            'open_seats_count': open_seats_count,
            'open_seats_list': open_seats_list,
            'members_list': members_list,
            'invitations_list': invitations_list,
            'subscription_group_id': subscription_group.id if subscription_group else None,
        }
        response = render(request, 'accounts/pages/stripe/toad_team_stripe_checkout.html', context)
        logger.info("Template rendered successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in stripe_checkout_team_view: {e}", exc_info=True)
        from django.http import HttpResponse
        return HttpResponse(f"Error loading checkout page: {str(e)}", status=500)


def stripe_checkout_team_registration_view(request):
    """
    Redirect directly to Stripe checkout for Team Toad subscription from registration flow
    Uses quantity from session and automatically creates checkout session
    """
    try:
        # Check if this is from registration flow
        if not request.session.get('team_registration_flow'):
            messages.error(request, 'Invalid session. Please start from the registration page.')
            return redirect('accounts:register_choices')
        
        # Get form data from session
        form_data = request.session.get('team_registration_form_data')
        if not form_data:
            messages.error(request, 'Registration data not found. Please start over.')
            return redirect('accounts:register_team_quantity')
        
        email = form_data.get('email')
        if not email:
            messages.error(request, 'Invalid registration data. Please start over.')
            return redirect('accounts:register_team_quantity')
        
        logger.info(f"Stripe Team registration checkout view accessed for email: {email}")
        
        # Get quantity from session
        quantity = request.session.get('team_registration_quantity')
        if not quantity or quantity < 2:
            messages.error(request, 'Invalid team size. Please start over.')
            return redirect('accounts:register_team_quantity')
        
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured - cannot display checkout page")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('pages:project_list')
        
        logger.info(f"Creating checkout session for {quantity} seats from registration flow")
        
        # Get the price ID
        price_id = PRO_PRICE_ID
        
        # Get the price from Stripe
        try:
            price = stripe.Price.retrieve(price_id, expand=['product'])
        except stripe.error.InvalidRequestError:
            messages.error(request, 'Subscription plan not found. Please contact support.')
            return redirect('accounts:register_team_quantity')
        
        # Create checkout session with quantity
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': quantity,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('accounts:stripe_success_team')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('accounts:register_team_quantity')),
            customer_email=email,  # Pre-fill email from form data
            metadata={
                'user_email': email,
                'plan_type': 'team',
                'quantity': str(quantity),
                'from_registration': 'true',  # Flag to indicate this is from registration
            }
        )
        
        logger.info(f"Checkout session created: {checkout_session.id}")
        logger.info(f"Redirecting to Stripe checkout URL: {checkout_session.url}")
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(checkout_session.url, status=303)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in stripe_checkout_team_registration_view: {e}")
        messages.error(request, 'There was an error processing your payment. Please try again.')
        return redirect('accounts:register_team_quantity')
    except Exception as e:
        logger.error(f"Error in stripe_checkout_team_registration_view: {e}", exc_info=True)
        from django.http import HttpResponse
        return HttpResponse(f"Error loading checkout page: {str(e)}", status=500)


@login_required
def create_checkout_session_team(request):
    """
    Create a Stripe checkout session for Team Toad subscription with quantity
    Handles seat reduction by removing members and invitations if specified
    """
    if request.method != 'POST':
        return redirect('accounts:stripe_checkout_team')
    
    try:
        # Check if Stripe is configured
        if not stripe.api_key:
            logger.error("Stripe API key not configured")
            messages.error(request, 'Payment system is not configured. Please contact support.')
            return redirect('accounts:stripe_checkout_team')
        
        # Get quantity from form
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('accounts:stripe_checkout_team')
        
        # Handle seat reduction removals for trial conversions
        from accounts.models import SubscriptionGroup, TeamInvitation
        import json
        
        remove_invitations = request.POST.get('remove_invitations', '[]')
        remove_members = request.POST.get('remove_members', '[]')
        
        try:
            invitation_ids_to_remove = json.loads(remove_invitations)
            member_ids_to_remove = json.loads(remove_members)
        except json.JSONDecodeError:
            invitation_ids_to_remove = []
            member_ids_to_remove = []
        
        # Get the user's trial subscription group if it exists
        subscription_group = SubscriptionGroup.objects.filter(
            admin=request.user,
            is_active=True,
            stripe_subscription_id__isnull=True
        ).first()
        
        if subscription_group:
            # Remove specified invitations
            if invitation_ids_to_remove:
                TeamInvitation.objects.filter(
                    id__in=invitation_ids_to_remove,
                    subscription_group=subscription_group,
                    status='pending'
                ).update(status='expired')
                logger.info(f"Cancelled {len(invitation_ids_to_remove)} pending invitations during seat reduction")
            
            # Remove specified members
            if member_ids_to_remove:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                members_to_remove = User.objects.filter(id__in=member_ids_to_remove)
                
                for member in members_to_remove:
                    subscription_group.members.remove(member)
                    # Downgrade member to free tier
                    member.tier = 'free'
                    member.save(update_fields=['tier'])
                    logger.info(f"Removed member {member.email} from subscription group during seat reduction")
        
        # Get the price ID from the form (for live mode)
        # Pro plan price
        price_id = request.POST.get('price_id', PRO_PRICE_ID)
        
        # Get the price from Stripe
        try:
            price = stripe.Price.retrieve(price_id, expand=['product'])
        except stripe.error.InvalidRequestError:
            messages.error(request, 'Subscription plan not found. Please contact support.')
            return redirect('accounts:stripe_checkout_team')
        
        # Create checkout session with quantity
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': quantity,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('accounts:stripe_success_team')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('accounts:stripe_cancel_team')),
            customer_email=request.user.email,  # Pre-fill email
            metadata={
                'user_id': str(request.user.id),
                'user_email': request.user.email,
                'plan_type': 'team',
                'quantity': str(quantity),
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except ValueError:
        messages.error(request, 'Invalid quantity. Please enter a valid number.')
        return redirect('accounts:stripe_checkout_team')
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_checkout_session_team: {e}")
        messages.error(request, 'There was an error processing your payment. Please try again.')
        return redirect('accounts:stripe_checkout_team')
    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session_team: {e}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('accounts:stripe_checkout_team')


def stripe_success_team_view(request):
    """
    Handle successful Stripe Team checkout - redirect to email input page
    Handles both new subscriptions, trial conversions, and new user registrations
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid session. Please contact support.')
        return redirect('pages:project_list')
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if this is from registration flow (user doesn't exist yet)
        from_registration = session.metadata.get('from_registration') == 'true'
        user_email = session.metadata.get('user_email')
        
        # If from registration, create the user first
        if from_registration and not request.user.is_authenticated:
            # Get form data from session
            form_data = request.session.get('team_registration_form_data')
            if not form_data:
                messages.error(request, 'Registration data not found. Please contact support.')
                return redirect('accounts:register_team_quantity')
            
            # Verify email matches
            if form_data.get('email') != user_email:
                messages.error(request, 'Email mismatch. Please contact support.')
                return redirect('accounts:register_team_quantity')
            
            # Create the user account
            from django.contrib.auth import get_user_model
            from django.contrib.auth import login
            User = get_user_model()
            
            # Check if user already exists (shouldn't happen, but safety check)
            try:
                user = User.objects.get(email=form_data['email'])
                # User already exists - this shouldn't happen, but handle it
                logger.warning(f"User {user.email} already exists during registration flow")
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    email=form_data['email'],
                    password=form_data['password'],
                    first_name=form_data['first_name'],
                    last_name=form_data.get('last_name', ''),
                    tier='pro',  # Set to Team Toad tier immediately
                    email_verified=True,  # Auto-verify for paid registration
                )
                logger.info(f"User created after payment: {user.email} with tier pro (Team Toad)")
            
            # Log the user in
            login(request, user)
            logger.info(f"User logged in after payment: {user.email}")
            
            # Clear form data from session
            if 'team_registration_form_data' in request.session:
                del request.session['team_registration_form_data']
        
        # Verify the session belongs to the current user (if authenticated)
        if request.user.is_authenticated:
            # For existing users, verify session belongs to them
            if session.metadata.get('user_id') and session.metadata.get('user_id') != str(request.user.id):
                messages.error(request, 'Session verification failed.')
                return redirect('pages:project_list')
        elif not from_registration:
            # If not authenticated and not from registration, require login
            messages.error(request, 'Please log in to complete your subscription.')
            return redirect('accounts:login')
        
        # Get quantity from metadata
        quantity = int(session.metadata.get('quantity', 1))
        
        # Get customer ID
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Check if this is a trial conversion (existing SubscriptionGroup without Stripe ID)
        from accounts.models import SubscriptionGroup
        existing_trial_group = SubscriptionGroup.objects.filter(
            admin=request.user,
            is_active=True,
            stripe_subscription_id__isnull=True
        ).first()
        
        if existing_trial_group:
            # Trial conversion - update existing SubscriptionGroup
            logger.info(f"Converting trial SubscriptionGroup {existing_trial_group.id} to paid for user {request.user.email}")
            existing_trial_group.stripe_subscription_id = subscription_id
            existing_trial_group.quantity = quantity
            existing_trial_group.save(update_fields=['stripe_subscription_id', 'quantity'])
            subscription_group = existing_trial_group
            is_trial_conversion = True
        else:
            # New subscription - create SubscriptionGroup
            subscription_group = SubscriptionGroup.objects.create(
                admin=request.user,
                stripe_subscription_id=subscription_id,
                quantity=quantity,
                is_active=True
            )
            is_trial_conversion = False
        
        # Automatically add admin as a member (fills one seat)
        subscription_group.members.add(request.user)
        
        # Update admin user tier and stripe_customer_id
        update_fields = []
        
        # For new registrations, tier is already set to pro
        # For existing users, upgrade to pro if needed
        if from_registration:
            # User was just created with tier='pro', ensure it's still set
            if request.user.tier != 'pro':
                request.user.tier = 'pro'
                update_fields.append('tier')
            # Ensure email is verified
            if not request.user.email_verified:
                request.user.email_verified = True
                update_fields.append('email_verified')
        elif request.user.tier in ['pro_trial', 'free', 'personal', 'personal_trial']:
            # Upgrade existing user to pro
            request.user.tier = 'pro'
            update_fields.append('tier')
        
        # Clear trial data on conversion
        if is_trial_conversion:
            request.user.trial_ends_at = None
            request.user.trial_started_at = None
            request.user.trial_type = None
            update_fields.extend(['trial_ends_at', 'trial_started_at', 'trial_type'])
            
            # Also upgrade all existing team members from pro_trial to pro
            team_members = subscription_group.members.exclude(id=request.user.id)
            for member in team_members:
                member_update_fields = []
                if member.tier == 'pro_trial':
                    member.tier = 'pro'
                    member_update_fields.append('tier')
                if member.trial_ends_at or member.trial_started_at or member.trial_type:
                    member.trial_ends_at = None
                    member.trial_started_at = None
                    member.trial_type = None
                    member_update_fields.extend(['trial_ends_at', 'trial_started_at', 'trial_type'])
                if member_update_fields:
                    member.save(update_fields=member_update_fields)
                    logger.info(f"Upgraded team member {member.email} from trial to paid pro tier")
        
        if customer_id and getattr(request.user, 'stripe_customer_id', None) != customer_id:
            request.user.stripe_customer_id = customer_id
            update_fields.append('stripe_customer_id')
        
        if update_fields:
            request.user.save(update_fields=update_fields)
        
        # Store subscription_group_id in session for the email input page
        request.session['subscription_group_id'] = subscription_group.id
        
        # Update Stripe subscription metadata with team info (includes admin as member)
        update_subscription_metadata_with_team_info(subscription_group)
        
        # Calculate available seats (quantity - 1 for admin, since they automatically fill one spot)
        available_seats = quantity - 1
        
        # Check if this is from registration flow
        from_registration = session.metadata.get('from_registration') == 'true'
        
        if from_registration:
            # Clear registration flow session data
            if 'team_registration_quantity' in request.session:
                del request.session['team_registration_quantity']
            if 'team_registration_flow' in request.session:
                del request.session['team_registration_flow']
            
            logger.info(f"Team subscription created for user {request.user.email} with {quantity} seats from registration flow. Admin automatically fills 1 seat, {available_seats} available for invites.")
            messages.success(request, f'Payment successful! You automatically fill one seat. Please invite {available_seats} team member(s).')
            
            # Redirect to email input page (same as upgrade flow)
            return redirect('accounts:team_invite_members')
        else:
            logger.info(f"Team subscription created for user {request.user.email} with {quantity} seats. Admin automatically fills 1 seat, {available_seats} available for invites.")
            messages.success(request, f'Payment successful! You automatically fill one seat. Please invite {available_seats} team member(s).')
            
            # Redirect to email input page (existing upgrade flow)
            return redirect('accounts:team_invite_members')
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in stripe_success_team_view: {e}")
        messages.error(request, 'There was an error processing your payment. Please contact support.')
        return redirect('pages:project_list')
    except Exception as e:
        logger.error(f"Unexpected error in stripe_success_team_view: {e}", exc_info=True)
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('pages:project_list')


@login_required
def stripe_cancel_team_view(request):
    """
    Handle cancelled Stripe Team checkout
    """
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return redirect('accounts:stripe_checkout_team')

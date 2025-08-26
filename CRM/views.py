from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.urls import reverse
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink
from .forms import LeadForm, LeadMessageForm, LeadFocusForm, ContactMethodForm, SocietyLinkForm

# Create your views here.

def is_superuser(user):
    """
    Check if user is a superuser.
    """
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def crm_home(request):
    """
    CRM home page view - only accessible by superusers.
    """
    # Get summary statistics
    total_leads = Lead.objects.count()
    recent_leads = Lead.objects.order_by('-created_at')[:5]
    
    context = {
        'title': 'CRM Dashboard',
        'user': request.user,
        'total_leads': total_leads,
        'recent_leads': recent_leads,
    }
    return render(request, 'CRM/crm_home.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_list(request):
    """
    List all leads with filtering and search.
    """
    leads = Lead.objects.select_related('lead_focus', 'contact_method').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        leads = leads.filter(name__icontains=search_query)
    
    # Filter by focus area
    focus_filter = request.GET.get('focus', '')
    if focus_filter:
        leads = leads.filter(lead_focus__name=focus_filter)
    
    # Filter by contact method
    contact_filter = request.GET.get('contact', '')
    if contact_filter:
        leads = leads.filter(contact_method__name=contact_filter)
    
    # Get filter options
    focus_areas = LeadFocus.objects.all()
    contact_methods = ContactMethod.objects.all()
    
    context = {
        'leads': leads,
        'focus_areas': focus_areas,
        'contact_methods': contact_methods,
        'search_query': search_query,
        'focus_filter': focus_filter,
        'contact_filter': contact_filter,
    }
    return render(request, 'CRM/lead_list.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_create(request):
    """
    Create a new lead.
    """
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead created successfully!')
            return redirect('crm:lead_list')
    else:
        form = LeadForm()
    
    context = {
        'form': form,
        'title': 'Create New Lead',
    }
    return render(request, 'CRM/lead_form.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_update(request, pk):
    """
    Update an existing lead.
    """
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lead updated successfully!')
            return redirect('crm:lead_list')
    else:
        form = LeadForm(instance=lead)
    
    context = {
        'form': form,
        'lead': lead,
        'title': 'Update Lead',
    }
    return render(request, 'CRM/lead_form.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_delete(request, pk):
    """
    Delete a lead.
    """
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Lead deleted successfully!')
        return redirect('crm:lead_list')
    
    context = {
        'lead': lead,
        'title': 'Delete Lead',
    }
    return render(request, 'CRM/lead_confirm_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_detail(request, pk):
    """
    View lead details.
    """
    lead = get_object_or_404(Lead, pk=pk)
    
    context = {
        'lead': lead,
        'title': f'Lead: {lead.name}',
    }
    return render(request, 'CRM/lead_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_message_create(request, lead_pk):
    """
    Create a new message for a specific lead.
    """
    lead = get_object_or_404(Lead, pk=lead_pk)
    
    if request.method == 'POST':
        form = LeadMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.lead = lead
            message.save()
            messages.success(request, 'Message added successfully!')
            return redirect('crm:lead_detail', pk=lead_pk)
    else:
        form = LeadMessageForm()
    
    context = {
        'form': form,
        'lead': lead,
        'title': 'Add Message',
    }
    return render(request, 'CRM/lead_message_form.html', context)

@login_required
@user_passes_test(is_superuser)
def lead_focus_create(request):
    """
    Create a new lead focus area.
    """
    if request.method == 'POST':
        form = LeadFocusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Focus area created successfully!')
            return redirect('crm:lead_list')
    else:
        form = LeadFocusForm()
    
    context = {
        'form': form,
        'title': 'Create New Focus Area',
    }
    return render(request, 'CRM/lead_focus_form.html', context)

@login_required
@user_passes_test(is_superuser)
def contact_method_create(request):
    """
    Create a new contact method.
    """
    if request.method == 'POST':
        form = ContactMethodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact method created successfully!')
            return redirect('crm:lead_list')
    else:
        form = ContactMethodForm()
    
    context = {
        'form': form,
        'title': 'Create New Contact Method',
    }
    return render(request, 'CRM/contact_method_form.html', context)

def crm_403_error(request, exception=None):
    """
    Custom 403 error handler for CRM app.
    """
    return render(request, 'CRM/403.html', status=403)

import logging
logger = logging.getLogger(__name__)

@login_required
@user_passes_test(is_superuser)
def society_link_create(request):
    """
    Create a new society link with image upload.
    Only accessible by superusers.
    """
    logger.info("=== SOCIETY LINK CREATE DEBUG ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"User: {request.user}")
    logger.info(f"Files: {request.FILES}")
    logger.info(f"POST data: {request.POST}")
    
    if request.method == 'POST':
        try:
            logger.info("Processing POST request...")
            form = SocietyLinkForm(request.POST, request.FILES)
            logger.info(f"Form created: {form}")
            
            if form.is_valid():
                logger.info("Form is valid, saving...")
                logger.info(f"Form cleaned data: {form.cleaned_data}")
                
                society_link = form.save()
                logger.info(f"Society link saved: {society_link}")
                logger.info(f"Society link ID: {society_link.pk}")
                logger.info(f"Society link name: {society_link.name}")
                logger.info(f"Society link url_identifier: {getattr(society_link, 'url_identifier', 'NOT SET')}")
                
                try:
                    # Get the public URL from the model property
                    public_url = request.build_absolute_uri(society_link.public_url)
                    logger.info(f"Public URL generated: {public_url}")
                except Exception as url_error:
                    logger.error(f"Error generating public URL: {url_error}")
                    public_url = "URL generation failed"
                
                messages.success(
                    request, 
                    f'Society link created successfully! Public URL: {public_url}'
                )
                logger.info("Success message added, redirecting...")
                return redirect('crm:home')
            else:
                logger.error(f"Form is invalid: {form.errors}")
                logger.error(f"Form non-field errors: {form.non_field_errors()}")
        except Exception as e:
            logger.error(f"Exception in POST processing: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            messages.error(request, f'Error creating society link: {str(e)}')
    else:
        logger.info("GET request, creating empty form...")
        form = SocietyLinkForm()
    
    context = {
        'form': form,
        'title': 'Create Society Link',
    }
    logger.info(f"Rendering template with context: {context}")
    return render(request, 'society_links/society_link_form.html', context)

@login_required
@user_passes_test(is_superuser)
def society_link_list(request):
    """
    List all society links.
    Only accessible by superusers.
    """
    society_links = SocietyLink.objects.all().order_by('-created_at')
    
    context = {
        'society_links': society_links,
        'title': 'Society Links',
    }
    return render(request, 'society_links/society_link_list.html', context)

def society_link_public(request, pk):
    """
    Public view for society links - accessible by anyone.
    """
    society_link = get_object_or_404(SocietyLink, pk=pk)
    
    context = {
        'society_link': society_link,
        'title': society_link.name,
    }
    return render(request, 'society_links/society_link_public.html', context)

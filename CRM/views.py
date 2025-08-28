from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.urls import reverse
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink
from .forms import LeadForm, LeadMessageForm, LeadFocusForm, ContactMethodForm, SocietyLinkForm, TestSocietyLinkForm
from django.core.files.base import ContentFile

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
    if request.method == 'POST':
        form = SocietyLinkForm(request.POST, request.FILES)
        if form.is_valid():
            society_link = form.save()
            messages.success(
                request, 
                f'Society link created successfully! ID: {society_link.pk}'
            )
            return redirect('crm:home')
        else:
            # Return form with errors
            context = {'form': form, 'title': 'Create Society Link'}
            return render(request, 'society_links/society_link_form.html', context)
    else:
        form = SocietyLinkForm()
    
    context = {
        'form': form,
        'title': 'Create Society Link',
    }
    return render(request, 'society_links/society_link_form.html', context)

@login_required
@user_passes_test(is_superuser)
def test_society_link_create(request):
    """
    Test view for creating a new test society link.
    Only accessible by superusers.
    """
    print("=== VIEW CALLED ===")
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        print("=== PROCESSING POST ===")
        
        # Force S3 storage BEFORE creating the form
        from django.conf import settings
        expected_storage_path = getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')
        if expected_storage_path != 'Not set':
            try:
                import importlib
                module_path, class_name = expected_storage_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                expected_class = getattr(module, class_name)
                
                # Check if we need to force S3 storage
                from django.core.files.storage import default_storage
                if not isinstance(default_storage, expected_class):
                    print("⚠️  Forcing S3 storage before form creation...")
                    forced_storage = expected_class()
                    import django.core.files.storage
                    django.core.files.storage.default_storage = forced_storage
                    print("✅ Default storage overridden to S3 before form creation")
            except Exception as e:
                print(f"Error forcing S3 storage: {e}")
        
        form = TestSocietyLinkForm(request.POST, request.FILES)
        print(f"Form created: {form}")
        print(f"Form is valid: {form.is_valid()}")
        
        if form.is_valid():
            print("=== UPLOAD DEBUG ===")
            print(f"Form is valid, about to save...")
            print(f"Image file: {request.FILES.get('photo')}")
            print(f"Image name: {request.FILES.get('photo').name if request.FILES.get('photo') else 'None'}")
            
            # Check storage backend before saving
            from django.core.files.storage import default_storage
            from django.conf import settings
            
            # Get the storage class that should be used according to settings
            expected_storage_path = getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')
            actual_storage = default_storage
            
            print(f"Storage backend: {actual_storage.__class__.__name__}")
            print(f"Storage location: {getattr(actual_storage, 'location', 'N/A')}")
            print(f"Settings DEFAULT_FILE_STORAGE: {expected_storage_path}")
            print(f"Settings FORCE_S3_TESTING: {getattr(settings, 'FORCE_S3_TESTING', 'Not set')}")
            print(f"Settings IS_PRODUCTION: {getattr(settings, 'IS_PRODUCTION', 'Not set')}")
            print(f"Settings MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
            print(f"Expected storage path: {expected_storage_path}")
            print(f"Actual storage class: {actual_storage.__class__}")
            print(f"Storage module: {actual_storage.__class__.__module__}")
            
            # Try to import the expected storage class
            try:
                if expected_storage_path != 'Not set':
                    import importlib
                    module_path, class_name = expected_storage_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    expected_class = getattr(module, class_name)
                    print(f"Successfully imported expected storage class: {expected_class}")
                    print(f"Are they the same? {isinstance(actual_storage, expected_class)}")
                    
                    # Force Django to use the correct storage
                    if not isinstance(actual_storage, expected_class):
                        print("⚠️  Storage mismatch detected! Forcing S3 storage...")
                        # Create a new S3 storage instance
                        forced_storage = expected_class()
                        print(f"Forced storage created: {forced_storage.__class__.__name__}")
                        print(f"Forced storage location: {getattr(forced_storage, 'location', 'N/A')}")
                        
                        # Override the default storage temporarily
                        import django.core.files.storage
                        django.core.files.storage.default_storage = forced_storage
                        print("✅ Default storage overridden to S3")
                else:
                    print("No DEFAULT_FILE_STORAGE setting found")
            except Exception as e:
                print(f"Error importing expected storage class: {e}")
            
            test_link = form.save()
            print(f"Test link saved with ID: {test_link.pk}")
            print(f"Photo field value: {test_link.photo}")
            print(f"Photo field URL: {test_link.photo.url if test_link.photo else 'None'}")
            
            # Check if file exists in storage
            if test_link.photo:
                print(f"File exists in storage: {default_storage.exists(test_link.photo.name)}")
                print(f"Full storage path: {test_link.photo.name}")
                
                # Check the actual file object
                print(f"Photo field name: {test_link.photo.name}")
                print(f"Photo field size: {test_link.photo.size if hasattr(test_link.photo, 'size') else 'N/A'}")
                print(f"Photo field storage: {test_link.photo.storage.__class__.__name__}")
                
                # Try to access the file content
                try:
                    with test_link.photo.open('rb') as f:
                        content = f.read()
                        print(f"✅ File content read successfully, size: {len(content)} bytes")
                except Exception as e:
                    print(f"❌ Error reading file content: {e}")
                
                # Test S3 storage directly
                try:
                    print("🔍 Testing S3 storage directly...")
                    test_content = b"S3 storage test content"
                    test_path = "test_s3_upload.txt"
                    
                    # Try to save a test file to S3
                    saved_path = default_storage.save(test_path, ContentFile(test_content))
                    print(f"✅ Test file saved to S3: {saved_path}")
                    
                    # Check if it exists
                    exists = default_storage.exists(saved_path)
                    print(f"✅ Test file exists in S3: {exists}")
                    
                    # Get the URL
                    url = default_storage.url(saved_path)
                    print(f"✅ Test file S3 URL: {url}")
                    
                    # Clean up
                    default_storage.delete(saved_path)
                    print("✅ Test file cleaned up")
                    
                except Exception as e:
                    print(f"❌ S3 storage test failed: {e}")
                    print(f"Error type: {type(e)}")
                    import traceback
                    traceback.print_exc()
            
            messages.success(request, f'Test society link created successfully! ID: {test_link.pk}')
            return redirect('crm:home')
        else:
            print(f"Form is invalid: {form.errors}")
            # Return form with errors
            context = {'form': form, 'title': 'Create Test Society Link'}
            return render(request, 'society_links/test_society_link_form.html', context)
    else:
        print("=== PROCESSING GET ===")
        form = TestSocietyLinkForm()
    
    context = {'form': form, 'title': 'Create Test Society Link'}
    return render(request, 'society_links/test_society_link_form.html', context)

@login_required
@user_passes_test(is_superuser)
def society_link_list(request):
    """
    List all society links.
    Only accessible by superusers.
    """
    society_links = SocietyLink.objects.all().order_by('-id')
    
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

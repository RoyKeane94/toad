from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.contrib import messages
from django.urls import reverse
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink
from .forms import LeadForm, LeadMessageForm, LeadFocusForm, ContactMethodForm, SocietyLinkForm, TestSocietyLinkForm, SocietyUniversityForm
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
    recent_society_links = SocietyLink.objects.order_by('-id')[:3]
    
    context = {
        'title': 'CRM Dashboard',
        'user': request.user,
        'total_leads': total_leads,
        'recent_leads': recent_leads,
        'recent_society_links': recent_society_links,
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
    print("=== PRODUCTION SOCIETY LINK CREATE DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"User: {request.user.email if request.user.is_authenticated else 'Not authenticated'}")
    print(f"Files: {request.FILES}")
    print(f"POST data: {request.POST}")
    
    if request.method == 'POST':
        print("=== PROCESSING POST REQUEST ===")
        
        # Check storage configuration before form creation
        try:
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            print(f"=== STORAGE CONFIGURATION DEBUG ===")
            print(f"IS_PRODUCTION: {getattr(settings, 'IS_PRODUCTION', 'Not set')}")
            print(f"FORCE_S3_TESTING: {getattr(settings, 'FORCE_S3_TESTING', 'Not set')}")
            print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
            print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
            print(f"Current default_storage: {default_storage.__class__.__name__}")
            print(f"Storage location: {getattr(default_storage, 'location', 'N/A')}")
            
            # Check AWS credentials
            print(f"=== AWS CREDENTIALS DEBUG ===")
            print(f"AWS_ACCESS_KEY_ID: {'✅ Set' if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else '❌ Missing'}")
            print(f"AWS_SECRET_ACCESS_KEY: {'✅ Set' if getattr(settings, 'AWS_SECRET_ACCESS_KEY', None) else '❌ Missing'}")
            print(f"AWS_STORAGE_BUCKET_NAME: {'✅ Set' if getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) else '❌ Missing'}")
            print(f"AWS_S3_REGION_NAME: {'✅ Set' if getattr(settings, 'AWS_S3_REGION_NAME', None) else '❌ Missing'}")
            
        except Exception as e:
            print(f"❌ Error checking storage configuration: {e}")
            import traceback
            traceback.print_exc()
        
        # Create form
        try:
            print("=== CREATING FORM ===")
            form = SocietyLinkForm(request.POST, request.FILES)
            print(f"Form created successfully: {form}")
            print(f"Form has files: {bool(request.FILES)}")
            if request.FILES:
                print(f"File keys: {list(request.FILES.keys())}")
                for key, file in request.FILES.items():
                    print(f"File {key}: {file.name}, size: {file.size}, type: {file.content_type}")
        except Exception as e:
            print(f"❌ Error creating form: {e}")
            import traceback
            traceback.print_exc()
            return render(request, 'CRM/500.html', status=500)
        
        # Validate form
        try:
            print("=== VALIDATING FORM ===")
            is_valid = form.is_valid()
            print(f"Form is valid: {is_valid}")
            if not is_valid:
                print(f"Form errors: {form.errors}")
                print(f"Form non-field errors: {form.non_field_errors()}")
        except Exception as e:
            print(f"❌ Error validating form: {e}")
            import traceback
            traceback.print_exc()
            return render(request, 'CRM/500.html', status=500)
        
        if form.is_valid():
            try:
                print("=== SAVING SOCIETY LINK ===")
                print(f"About to save form...")
                society_link = form.save()
                print(f"✅ Society link saved successfully!")
                print(f"ID: {society_link.pk}")
                print(f"Name: {society_link.name}")
                print(f"Image field: {society_link.image}")
                if society_link.image:
                    print(f"Image name: {society_link.image.name}")
                    print(f"Image URL: {society_link.image.url}")
                    print(f"Image storage: {society_link.image.storage.__class__.__name__}")
                
                messages.success(
                    request, 
                    f'Society link created successfully! ID: {society_link.pk}'
                )
                return redirect('crm:home')
                
            except Exception as e:
                print(f"❌ Error saving society link: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating society link: {str(e)}')
                context = {'form': form, 'title': 'Create Society Link'}
                return render(request, 'society_links/society_link_form.html', context)
        else:
            print("=== FORM INVALID, RETURNING WITH ERRORS ===")
            # Return form with errors
            context = {'form': form, 'title': 'Create Society Link'}
            return render(request, 'society_links/society_link_form.html', context)
    else:
        print("=== PROCESSING GET REQUEST ===")
        try:
            form = SocietyLinkForm()
            print(f"Form created for GET request: {form}")
        except Exception as e:
            print(f"❌ Error creating form for GET: {e}")
            import traceback
            traceback.print_exc()
            return render(request, 'CRM/500.html', status=500)
    
    context = {
        'form': form,
        'title': 'Create Society Link',
    }
    print("=== RENDERING TEMPLATE ===")
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

@login_required
@user_passes_test(is_superuser)
def society_link_delete(request, pk):
    """
    Delete a society link.
    Only accessible by superusers.
    """
    society_link = get_object_or_404(SocietyLink, pk=pk)
    
    if request.method == 'POST':
        society_link.delete()
        messages.success(request, 'Society link deleted successfully!')
        return redirect('crm:society_link_list')
    
    context = {
        'society_link': society_link,
        'title': 'Delete Society Link',
    }
    return render(request, 'society_links/society_link_confirm_delete.html', context)

def society_link_public(request, university_slug, society_slug):
    """
    Public view for society links - accessible by anyone.
    Uses university and society slugs in URL.
    """
    from django.utils.text import slugify
    
    # Find society link by matching slugified names
    society_links = SocietyLink.objects.filter(
        society_university__isnull=False
    ).select_related('society_university')
    
    society_link = None
    for link in society_links:
        if (slugify(link.society_university.name) == university_slug and 
            slugify(link.name) == society_slug):
            society_link = link
            break
    
    if not society_link:
        raise Http404("Society link not found")
    
    context = {
        'society_link': society_link,
        'title': society_link.name,
    }
    return render(request, 'society_links/society_link_public.html', context)

def society_link_public_old(request, pk):
    """
    Fallback public view for society links using old format.
    Redirects to new format if university is available.
    """
    society_link = get_object_or_404(SocietyLink, pk=pk)
    
    # If university is available, redirect to new format
    if society_link.society_university:
        from django.shortcuts import redirect
        from django.utils.text import slugify
        return redirect('crm:society_link_public', 
                       university_slug=slugify(society_link.society_university.name),
                       society_slug=slugify(society_link.name))
    
    # Otherwise show error page
    context = {
        'society_link': society_link,
        'title': society_link.name,
        'error': 'This society link requires a university to be assigned.',
    }
    return render(request, 'society_links/society_link_public.html', context)

@login_required
@user_passes_test(is_superuser)
def society_university_create(request):
    """
    Create a new society university.
    Only accessible by superusers.
    """
    if request.method == 'POST':
        form = SocietyUniversityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'University created successfully!')
            return redirect('crm:society_link_create')
    else:
        form = SocietyUniversityForm()
    
    context = {
        'form': form,
        'title': 'Create University',
    }
    return render(request, 'society_links/society_university_form.html', context)

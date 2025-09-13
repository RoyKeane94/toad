from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.urls import reverse
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink
from .forms import LeadForm, LeadMessageForm, LeadFocusForm, ContactMethodForm, SocietyLinkForm, SocietyUniversityForm
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
    recent_leads = Lead.objects.select_related('lead_focus', 'contact_method', 'society_university').order_by('-created_at')[:5]
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
    List all leads with filtering, search, and sorting.
    """
    leads = Lead.objects.select_related('lead_focus', 'contact_method', 'society_university')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        leads = leads.filter(name__icontains=search_query)
    
    # Filter by university
    university_filter = request.GET.get('university', '')
    if university_filter:
        leads = leads.filter(society_university__name=university_filter)
    
    # Filter by focus area
    focus_filter = request.GET.get('focus', '')
    if focus_filter:
        leads = leads.filter(lead_focus__name=focus_filter)
    
    # Filter by contact method
    contact_filter = request.GET.get('contact', '')
    if contact_filter:
        leads = leads.filter(contact_method__name=contact_filter)
    
    # Sorting functionality
    sort = request.GET.get('sort', 'created')
    if sort == 'university':
        leads = leads.order_by('society_university__name')
    elif sort == 'customer':
        leads = leads.order_by('-toad_customer', 'toad_customer_date')
    elif sort == 'initial_message':
        leads = leads.order_by('-initial_message_sent', 'initial_message_sent_date')
    elif sort == 'no_response':
        leads = leads.order_by('-no_response', 'no_response_date')
    elif sort == 'created':
        leads = leads.order_by('-created_at')
    else:
        leads = leads.order_by('-created_at')
    
    # Get filter options
    from .models import SocietyUniversity
    universities = SocietyUniversity.objects.all()
    focus_areas = LeadFocus.objects.all()
    contact_methods = ContactMethod.objects.all()
    
    # Calculate statistics
    total_leads = Lead.objects.count()
    customer_count = Lead.objects.filter(toad_customer=True).count()
    no_response_count = Lead.objects.filter(no_response=True).count()
    university_count = SocietyUniversity.objects.count()
    
    context = {
        'leads': leads,
        'universities': universities,
        'focus_areas': focus_areas,
        'contact_methods': contact_methods,
        'search_query': search_query,
        'university_filter': university_filter,
        'focus_filter': focus_filter,
        'contact_filter': contact_filter,
        'sort': sort,
        'total_leads': total_leads,
        'customer_count': customer_count,
        'no_response_count': no_response_count,
        'university_count': university_count,
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
        'title': f'Lead: {lead.name} - {lead.society_university.name}',
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

def society_link_public_qr(request, university_slug, society_slug):
    """
    QR code version of the public society link page.
    Shows a QR code that links to the main society page.
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
    
    # Generate the main society page URL
    main_url = request.build_absolute_uri(
        reverse('crm:society_link_public', 
                kwargs={'university_slug': university_slug, 'society_slug': society_slug})
    )
    
    context = {
        'society_link': society_link,
        'title': f"{society_link.name} - QR Code",
        'main_url': main_url,
    }
    return render(request, 'society_links/society_link_public_qr.html', context)

def society_link_qr_image(request, university_slug, society_slug):
    """
    Generate QR code image for society links.
    """
    import qrcode
    from django.utils.text import slugify
    from io import BytesIO
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
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
            logger.error(f"Society link not found: {university_slug}/{society_slug}")
            raise Http404("Society link not found")
        
        # Generate the main society page URL
        main_url = request.build_absolute_uri(
            reverse('crm:society_link_public', 
                    kwargs={'university_slug': university_slug, 'society_slug': society_slug})
        )
        
        logger.info(f"Generating QR code for URL: {main_url}")
        
        # Create QR code with simpler settings
        qr = qrcode.QRCode(
            version=None,  # Auto-determine version
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=2,
        )
        qr.add_data(main_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        logger.info("QR code generated successfully")
        
        # Return image response
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
        return response
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a simple error image
        from PIL import Image, ImageDraw
        import io
        
        # Create a simple error image
        img = Image.new('RGB', (256, 256), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw error text
        try:
            draw.text((50, 100), "QR Code Error", fill='red')
            draw.text((50, 130), str(e)[:50], fill='red')
        except:
            # If text drawing fails, just draw a red rectangle
            draw.rectangle([50, 100, 200, 150], fill='red')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/png')

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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.db import models
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink, Company, CompanySector, CustomerTemplate
from .forms import (
    B2BLeadForm, SocietyLeadForm, LeadMessageForm, LeadFocusForm, ContactMethodForm, 
    SocietyLinkForm, SocietyUniversityForm, CompanyForm, CompanySectorForm, EmailTemplateForm, CustomerTemplateForm,
    CompanyBulkSectorForm, CompanyBulkFormSet
)
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
    CRM home page view - B2B focused dashboard.
    """
    # Get company statistics
    total_companies = Company.objects.count()
    total_sectors = CompanySector.objects.count()
    total_templates = CustomerTemplate.objects.count()
    recent_companies = Company.objects.select_related('company_sector', 'email_template').order_by('-updated_at')[:5]
    
    context = {
        'title': 'B2B CRM Dashboard',
        'user': request.user,
        'total_companies': total_companies,
        'total_sectors': total_sectors,
        'total_templates': total_templates,
        'recent_companies': recent_companies,
    }
    return render(request, 'CRM/b2b/company_home.html', context)

# Company Views
@login_required
@user_passes_test(is_superuser)
def company_list(request):
    """
    List all companies with filtering, search, and sorting.
    """
    companies = Company.objects.select_related('email_template', 'company_sector').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(company_name__icontains=search_query)
    
    # Filter by status - support multiple values
    status_filters = request.GET.getlist('status')
    # Default to Prospect if no status is provided
    if not status_filters:
        status_filters = ['Prospect']
        status_filter = 'Prospect'  # For backward compatibility with template
    else:
        status_filter = status_filters[0] if len(status_filters) == 1 else ''  # For display purposes
    
    if status_filters:
        companies = companies.filter(status__in=status_filters)
    
    # Filter by email_status - support multiple values
    email_status_filters = request.GET.getlist('email_status')
    email_status_filter = email_status_filters[0] if email_status_filters else ''  # For backward compatibility with template
    
    if email_status_filters:
        companies = companies.filter(email_status__in=email_status_filters)
    
    # Filter by sector - support multiple values
    sector_filters = [s for s in request.GET.getlist('sector') if s and s.strip()]  # Filter out empty strings
    sector_filter = sector_filters[0] if sector_filters else ''  # For backward compatibility with template
    
    if sector_filters:
        # Convert to integers for the id lookup
        try:
            sector_ids = [int(s) for s in sector_filters]
            companies = companies.filter(company_sector__id__in=sector_ids)
        except (ValueError, TypeError):
            # If any value can't be converted to int, skip sector filtering
            pass
    
    # Order by updated_at (most recent first)
    companies = companies.order_by('-updated_at')
    
    # Calculate statistics from filtered queryset (before pagination)
    filtered_companies = companies  # This is the filtered queryset
    total_companies = filtered_companies.count()
    customer_count = filtered_companies.filter(status='Customer').count()
    prospect_count = filtered_companies.filter(status='Prospect').count()
    rejected_followup_count = filtered_companies.filter(status='Rejected but follow up').count()
    no_response_count = filtered_companies.filter(status='No response').count()
    rejected_count = filtered_companies.filter(status='Rejected').count()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all sectors for filter dropdown
    sectors = CompanySector.objects.all().order_by('name')
    
    # Build query string for pagination (excluding page parameter)
    from urllib.parse import urlencode
    query_params = {}
    if search_query:
        query_params['search'] = search_query
    if status_filters:
        query_params['status'] = status_filters
    if email_status_filters:
        query_params['email_status'] = email_status_filters
    if sector_filters:
        query_params['sector'] = sector_filters
    query_string = urlencode(query_params, doseq=True)
    
    context = {
        'companies': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_filters': status_filters,
        'email_status_filter': email_status_filter,
        'email_status_filters': email_status_filters,
        'sector_filter': sector_filter,
        'sector_filters': sector_filters,
        'sectors': sectors,
        'query_string': query_string,
        'total_companies': total_companies,
        'customer_count': customer_count,
        'prospect_count': prospect_count,
        'rejected_followup_count': rejected_followup_count,
        'no_response_count': no_response_count,
        'rejected_count': rejected_count,
        'title': 'Companies',
    }
    return render(request, 'CRM/b2b/company_list.html', context)

@login_required
@user_passes_test(is_superuser)
def company_create(request):
    """
    Create a new company.
    """
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully!')
            return redirect('crm:company_list')
    else:
        form = CompanyForm()
    
    context = {
        'form': form,
        'title': 'Create New Company',
    }
    return render(request, 'CRM/b2b/company_form.html', context)

@login_required
@user_passes_test(is_superuser)
def company_update(request, pk):
    """
    Update an existing company.
    """
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully!')
            return redirect('crm:company_detail', pk=company.pk)
    else:
        form = CompanyForm(instance=company)
    
    context = {
        'form': form,
        'company': company,
        'title': f'Update Company: {company.company_name}',
    }
    return render(request, 'CRM/b2b/company_form.html', context)

@login_required
@user_passes_test(is_superuser)
def company_detail(request, pk):
    """
    View company details.
    """
    company = get_object_or_404(Company.objects.select_related('company_sector', 'email_template'), pk=pk)
    
    # Get template preview URL with company_id parameter for personalization
    template_url = None
    if company.company_sector:
        from .models import CustomerTemplate
        try:
            template = CustomerTemplate.objects.get(company_sector=company.company_sector)
            from django.urls import reverse
            url = reverse('crm:customer_template_public', kwargs={'pk': template.pk})
            # Add company_id query parameter to personalize the template
            url += f'?company_id={company.pk}'
            template_url = request.build_absolute_uri(url) if request else url
        except CustomerTemplate.DoesNotExist:
            pass
        except CustomerTemplate.MultipleObjectsReturned:
            template = CustomerTemplate.objects.filter(company_sector=company.company_sector).first()
            if template:
                from django.urls import reverse
                url = reverse('crm:customer_template_public', kwargs={'pk': template.pk})
                # Add company_id query parameter to personalize the template
                url += f'?company_id={company.pk}'
                template_url = request.build_absolute_uri(url) if request else url
    
    context = {
        'company': company,
        'template_url': template_url,
        'title': f'Company: {company.company_name}',
    }
    return render(request, 'CRM/b2b/company_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def company_delete(request, pk):
    """
    Delete a company.
    """
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        company_name = company.company_name
        company.delete()
        messages.success(request, f'Company "{company_name}" has been deleted successfully.')
        return redirect('crm:company_list')
    
    context = {
        'company': company,
        'title': f'Delete Company: {company.company_name}',
    }
    return render(request, 'CRM/b2b/company_confirm_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def company_bulk_upload_select_sector(request):
    """
    Select sector for bulk upload.
    """
    if request.method == 'POST':
        form = CompanyBulkSectorForm(request.POST)
        if form.is_valid():
            sector_id = form.cleaned_data['company_sector'].pk
            return redirect('crm:company_bulk_upload', sector_id=sector_id)
    else:
        form = CompanyBulkSectorForm()
    
    context = {
        'form': form,
        'title': 'Bulk Upload Companies - Select Sector',
    }
    return render(request, 'CRM/b2b/company_bulk_upload_select_sector.html', context)

@login_required
@user_passes_test(is_superuser)
def company_bulk_upload(request, sector_id):
    """
    Bulk upload companies for a specific sector.
    """
    sector = get_object_or_404(CompanySector, pk=sector_id)
    
    if request.method == 'POST':
        formset = CompanyBulkFormSet(request.POST)
        if formset.is_valid():
            created_count = 0
            for form in formset:
                if form.cleaned_data.get('company_name'):  # Only process non-empty forms
                    company = Company.objects.create(
                        company_name=form.cleaned_data['company_name'],
                        status='Prospect',  # Default status as requested
                        company_sector=sector,
                        contact_person=form.cleaned_data.get('contact_person', ''),
                        contact_email=form.cleaned_data.get('contact_email', '')
                    )
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully created {created_count} companies!')
            else:
                messages.warning(request, 'No companies were created. Please fill in at least one company name.')
            return redirect('crm:company_list')
    else:
        formset = CompanyBulkFormSet()
    
    context = {
        'formset': formset,
        'sector': sector,
        'title': f'Bulk Upload Companies - {sector.name}',
    }
    return render(request, 'CRM/b2b/company_bulk_upload.html', context)

@login_required
@user_passes_test(is_superuser)
def company_sector_create(request):
    """
    Create a new company sector.
    """
    if request.method == 'POST':
        form = CompanySectorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company sector created successfully!')
            return redirect('crm:company_list')
    else:
        form = CompanySectorForm()
    
    context = {
        'form': form,
        'title': 'Create New Company Sector',
    }
    return render(request, 'CRM/b2b/company_sector_form.html', context)


@login_required
@user_passes_test(is_superuser)
def email_template_list(request):
    """
    List all email templates grouped by sector.
    """
    from .models import EmailTemplate, CompanySector
    
    # Email sequence info
    EMAIL_INFO = {
        1: {'label': 'Initial', 'color': 'blue', 'delay': 'Sent immediately'},
        2: {'label': '+4 days', 'color': 'purple', 'delay': '4 days after Email 1'},
        3: {'label': '+5 days', 'color': 'orange', 'delay': '5 days after Email 2'},
        4: {'label': '+10 days', 'color': 'red', 'delay': '10 days after Email 3'},
    }
    
    # Get all sectors with their templates
    sectors = CompanySector.objects.prefetch_related('email_templates').order_by('name')
    
    # Build structured data for each sector
    sectors_data = []
    for sector in sectors:
        templates = {t.email_number: t for t in sector.email_templates.all()}
        
        # Build email slots (1-4) with template or None
        email_slots = []
        for num in [1, 2, 3, 4]:
            email_slots.append({
                'number': num,
                'template': templates.get(num),
                'info': EMAIL_INFO[num],
            })
        
        sectors_data.append({
            'sector': sector,
            'email_slots': email_slots,
            'template_count': len(templates),
        })
    
    context = {
        'sectors_data': sectors_data,
        'title': 'Email Templates',
    }
    return render(request, 'CRM/b2b/email_template_list.html', context)

@login_required
@user_passes_test(is_superuser)
def email_template_create(request):
    """
    Create a new email template for B2B outreach.
    """
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Email template "{template.name}" created successfully!')
            return redirect('crm:email_template_list')
    else:
        # Pre-select sector if provided
        initial = {}
        sector_id = request.GET.get('sector')
        email_number = request.GET.get('email_number')
        if sector_id:
            initial['company_sector'] = sector_id
        if email_number:
            initial['email_number'] = email_number
        form = EmailTemplateForm(initial=initial)

    context = {
        'form': form,
        'title': 'Create Email Template',
    }
    return render(request, 'CRM/b2b/email_template_form.html', context)

@login_required
@user_passes_test(is_superuser)
def email_template_update(request, pk):
    """
    Update an existing email template.
    """
    from .models import EmailTemplate
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Email template "{template.name}" updated successfully!')
            return redirect('crm:email_template_list')
    else:
        form = EmailTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': f'Update Email Template: {template.name}',
    }
    return render(request, 'CRM/b2b/email_template_form.html', context)

@login_required
@user_passes_test(is_superuser)
def email_template_delete(request, pk):
    """
    Delete an email template.
    """
    from .models import EmailTemplate
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Email template "{template_name}" has been deleted.')
        return redirect('crm:email_template_list')
    
    context = {
        'template': template,
        'title': f'Delete Email Template: {template.name}',
    }
    return render(request, 'CRM/b2b/email_template_confirm_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def email_template_preview(request, pk):
    """
    Preview an email template with sample data.
    """
    from .models import EmailTemplate, CustomerTemplate
    from django.conf import settings
    
    template = get_object_or_404(EmailTemplate, pk=pk)
    
    # Check if this sector has a CustomerTemplate (required for personalised_template_url)
    customer_template = None
    personalised_url = None
    url_warning = None
    
    if template.company_sector:
        try:
            customer_template = CustomerTemplate.objects.get(company_sector=template.company_sector)
            # Generate a real preview URL
            url = reverse('crm:customer_template_public', kwargs={'pk': customer_template.pk})
            url += '?company_id=SAMPLE'
            personalised_url = request.build_absolute_uri(url)
        except CustomerTemplate.DoesNotExist:
            url_warning = f'No CustomerTemplate exists for sector "{template.company_sector.name}". The {{personalised_template_url}} placeholder will be empty when emails are sent.'
            personalised_url = '[NO TEMPLATE CONFIGURED]'
        except CustomerTemplate.MultipleObjectsReturned:
            customer_template = CustomerTemplate.objects.filter(company_sector=template.company_sector).first()
            url = reverse('crm:customer_template_public', kwargs={'pk': customer_template.pk})
            url += '?company_id=SAMPLE'
            personalised_url = request.build_absolute_uri(url)
    else:
        url_warning = 'This email template has no sector assigned. The {personalised_template_url} placeholder cannot be generated.'
        personalised_url = '[NO SECTOR ASSIGNED]'
    
    # Sample data for preview
    sample_company_name = 'Acme Weddings Ltd'
    sample_data = {
        'company_name': sample_company_name,
        'contact_person': 'Jane Smith',
        'personalised_template_url': personalised_url,
        'personalised_link': f'<b><a href="{personalised_url}">Toad x {sample_company_name}</a></b>',
    }
    
    rendered_subject = template.subject
    rendered_body = template.body
    
    for key, value in sample_data.items():
        rendered_subject = rendered_subject.replace(f'{{{key}}}', value)
        rendered_body = rendered_body.replace(f'{{{key}}}', value)
    
    # Check if placeholder is actually used in template
    placeholder_used = (
        '{personalised_template_url}' in template.body or 
        '{personalised_template_url}' in template.subject or
        '{personalised_link}' in template.body or 
        '{personalised_link}' in template.subject
    )
    
    context = {
        'template': template,
        'rendered_subject': rendered_subject,
        'rendered_body': rendered_body,
        'sample_data': sample_data,
        'customer_template': customer_template,
        'url_warning': url_warning,
        'placeholder_used': placeholder_used,
        'title': f'Preview: {template.name}',
    }
    return render(request, 'CRM/b2b/email_template_preview.html', context)

@login_required
@user_passes_test(is_superuser)
def customer_template_list(request):
    """
    List all customer templates.
    """
    templates = CustomerTemplate.objects.select_related('company_sector').order_by('company_sector__name', 'playbook_name')
    
    context = {
        'templates': templates,
        'title': 'Customer Templates',
    }
    return render(request, 'CRM/b2b/customer_template_list.html', context)

@login_required
@user_passes_test(is_superuser)
def customer_template_create(request):
    """
    Create a new customer template.
    """
    if request.method == 'POST':
        form = CustomerTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Customer template "{template.playbook_name}" created successfully!')
            # Redirect to the public view of the template
            return redirect('crm:customer_template_public', pk=template.pk)
    else:
        form = CustomerTemplateForm()

    context = {
        'form': form,
        'title': 'Create Customer Template',
    }
    return render(request, 'CRM/b2b/new_customer_template_form.html', context)

@login_required
@user_passes_test(is_superuser)
def customer_template_update(request, pk):
    """
    Update an existing customer template.
    """
    template = get_object_or_404(CustomerTemplate, pk=pk)
    
    if request.method == 'POST':
        form = CustomerTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer template "{template.playbook_name}" updated successfully!')
            # Redirect to the public view of the template
            return redirect('crm:customer_template_public', pk=template.pk)
    else:
        form = CustomerTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': f'Update Customer Template: {template.playbook_name}',
    }
    return render(request, 'CRM/b2b/new_customer_template_form.html', context)

# ==================== SOCIETY CRM VIEWS ====================

@login_required
@user_passes_test(is_superuser)
def society_crm_home(request):
    """
    Society CRM home page view.
    """
    # Get society statistics
    society_leads = Lead.objects.filter(lead_type='society')
    total_society_leads = society_leads.count()
    society_customers = society_leads.filter(toad_customer=True).count()
    recent_society_leads = society_leads.select_related('lead_focus', 'contact_method', 'society_university').order_by('-created_at')[:5]
    recent_society_links = SocietyLink.objects.select_related('society_university').order_by('-id')[:3]
    
    from .models import SocietyUniversity
    total_universities = SocietyUniversity.objects.count()
    
    context = {
        'title': 'Society CRM Dashboard',
        'user': request.user,
        'total_society_leads': total_society_leads,
        'society_customers': society_customers,
        'recent_society_leads': recent_society_leads,
        'recent_society_links': recent_society_links,
        'total_universities': total_universities,
    }
    return render(request, 'CRM/society/society_home.html', context)

@login_required
@user_passes_test(is_superuser)
def society_lead_list(request):
    """
    List all society leads with filtering, search, and sorting.
    """
    leads = Lead.objects.filter(lead_type='society').select_related('lead_focus', 'contact_method', 'society_university')
    
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
    total_leads = leads.count()
    customer_count = Lead.objects.filter(lead_type='society', toad_customer=True).count()
    no_response_count = Lead.objects.filter(lead_type='society', no_response=True).count()
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
        'crm_type': 'society',
    }
    return render(request, 'CRM/society/society_lead_list.html', context)

@login_required
@user_passes_test(is_superuser)
def society_lead_create(request):
    """
    Create a new society lead.
    """
    if request.method == 'POST':
        form = SocietyLeadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Society lead created successfully!')
            return redirect('crm:society_lead_list')
    else:
        form = SocietyLeadForm()
    
    context = {
        'form': form,
        'title': 'Create New Society Lead',
        'crm_type': 'society',
    }
    return render(request, 'CRM/society/society_lead_form.html', context)

@login_required
@user_passes_test(is_superuser)
def society_lead_update(request, pk):
    """
    Update an existing society lead.
    """
    lead = get_object_or_404(Lead, pk=pk, lead_type='society')
    
    if request.method == 'POST':
        form = SocietyLeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Society lead updated successfully!')
            return redirect('crm:society_lead_list')
    else:
        form = SocietyLeadForm(instance=lead)
    
    context = {
        'form': form,
        'lead': lead,
        'title': 'Update Society Lead',
        'crm_type': 'society',
    }
    return render(request, 'CRM/society/society_lead_form.html', context)

@login_required
@user_passes_test(is_superuser)
def society_lead_delete(request, pk):
    """
    Delete a society lead.
    """
    lead = get_object_or_404(Lead, pk=pk, lead_type='society')
    
    if request.method == 'POST':
        lead.delete()
        messages.success(request, 'Society lead deleted successfully!')
        return redirect('crm:society_lead_list')
    
    context = {
        'lead': lead,
        'title': 'Delete Society Lead',
        'crm_type': 'society',
    }
    return render(request, 'CRM/society/society_lead_confirm_delete.html', context)

@login_required
@user_passes_test(is_superuser)
def society_lead_detail(request, pk):
    """
    View society lead details.
    """
    lead = get_object_or_404(Lead, pk=pk, lead_type='society')
    
    context = {
        'lead': lead,
        'title': f'Society Lead: {lead.name}',
        'crm_type': 'society',
    }
    return render(request, 'CRM/society/society_lead_detail.html', context)

# ==================== LEGACY/OLD VIEWS (redirect to company views for backward compatibility) ====================

@login_required
@user_passes_test(is_superuser)
def lead_list(request):
    """
    Legacy view - redirects to company list.
    """
    return redirect('crm:company_list')

@login_required
@user_passes_test(is_superuser)
def lead_create(request):
    """
    Legacy view - redirects to company create.
    """
    return redirect('crm:company_create')

@login_required
@user_passes_test(is_superuser)
def lead_update(request, pk):
    """
    Legacy view - redirects to company update if lead has company, otherwise company list.
    """
    lead = get_object_or_404(Lead, pk=pk)
    if lead.lead_type == 'b2b' and lead.company:
        return redirect('crm:company_update', pk=lead.company.pk)
    else:
        return redirect('crm:company_list')

@login_required
@user_passes_test(is_superuser)
def lead_delete(request, pk):
    """
    Legacy view - redirects to company list.
    """
    return redirect('crm:company_list')

@login_required
@user_passes_test(is_superuser)
def lead_detail(request, pk):
    """
    Legacy view - redirects to appropriate view based on lead type.
    """
    lead = get_object_or_404(Lead, pk=pk)
    if lead.lead_type == 'b2b':
        if lead.company:
            return redirect('crm:company_detail', pk=lead.company.pk)
        else:
            return redirect('crm:company_list')
    else:
        return redirect('crm:society_lead_detail', pk=pk)

# ==================== SHARED VIEWS ====================

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
def company_message_create(request, company_pk):
    """
    Create a new message for a specific company.
    """
    company = get_object_or_404(Company, pk=company_pk)
    
    if request.method == 'POST':
        form = LeadMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.company = company
            message.save()
            messages.success(request, 'Message added successfully!')
            return redirect('crm:company_detail', pk=company_pk)
    else:
        form = LeadMessageForm()
    
    context = {
        'form': form,
        'company': company,
        'title': 'Add Message',
    }
    return render(request, 'CRM/company_message_form.html', context)

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

# Instagram Post Views
def instagram_introducing_toad(request):
    """
    Instagram post: Introducing Toad
    """
    return render(request, 'CRM/instagram/introducing_toad.html')

def instagram_why_users_love_toad(request):
    """
    Instagram post: Why Users Love Toad
    """
    return render(request, 'CRM/instagram/why_users_love_toad.html')

def instagram_toad_bingo_card(request):
    """
    Instagram post: Toad Bingo Card
    """
    return render(request, 'CRM/instagram/toad_bingo_card.html')

def instagram_preview(request):
    """
    Preview all Instagram posts
    """
    return render(request, 'CRM/instagram/preview.html')

def instagram_index(request):
    """
    Instagram posts index page
    """
    return render(request, 'CRM/instagram/index.html')

def toad_weddings_view(request):
    """
    Public landing page for wedding venue outreach links.
    Optional ?venue query parameter personalises the hero text.
    """
    venue_name = request.GET.get('venue', '').strip() or None
    context = {
        'venue_name': venue_name,
        'title': 'Toad for Weddings',
    }
    return render(request, 'business_links/events/toad_weddings.html', context)

def customer_template_public_view(request, pk):
    """
    Public landing page for customer templates.
    Renders the template with CustomerTemplate data.
    Optional ?id query parameter (lead ID) or ?company_id personalises the hero text with company name.
    Increments company-specific view count when accessed.
    """
    template = get_object_or_404(CustomerTemplate, pk=pk)
    company_name = None
    company = None
    
    # Get lead ID from query parameter
    lead_id = request.GET.get('id', '').strip()
    if lead_id:
        try:
            lead = Lead.objects.select_related('company').get(pk=lead_id, lead_type='b2b')
            if lead.company:
                company = lead.company
                company_name = company.company_name
        except (Lead.DoesNotExist, ValueError):
            # Invalid lead ID, just continue without personalization
            pass
    
    # If no company from lead, try company_id parameter
    if not company:
        company_id = request.GET.get('company_id', '').strip()
        if company_id:
            try:
                company = Company.objects.get(pk=company_id)
                company_name = company.company_name
            except (Company.DoesNotExist, ValueError):
                # Invalid company ID, just continue without personalization
                pass
    
    # Increment company-specific view count if company is identified
    if company:
        from django.db.models import F
        Company.objects.filter(pk=company.pk).update(template_view_count=F('template_view_count') + 1)
        company.refresh_from_db()
    
    context = {
        'template': template,
        'company_name': company_name,
        'title': template.playbook_name,
    }
    return render(request, 'business_links/events/toad_sector_template.html', context)

# Student Society Partnership Pages
def southampton_economics_society_page(request):
    """
    Southampton Economics Society partnership page
    """
    return render(request, 'student_templates/southampton_economics_society_link.html')

def load_southampton_economics_template(request):
    """
    Load the Southampton Economics Society template for the user
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    # Import the template creation function from signals
    from pages.signals import create_southampton_economics_society_template
    
    # Create the template for the user
    project = create_southampton_economics_society_template(request.user)
    
    # Redirect to the new project
    return redirect('pages:project_grid', pk=project.pk)


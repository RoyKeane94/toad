from django import forms
from django.forms import formset_factory
from .models import (
    Lead,
    LeadFocus,
    ContactMethod,
    LeadMessage,
    SocietyLink,
    SocietyUniversity,
    Company,
    CompanySector,
    EmailTemplate,
    CustomerTemplate,
)

# Base styling constants
BASE_INPUT_CLASS = 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
BASE_CHECKBOX_CLASS = 'h-4 w-4 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] border-[var(--inline-input-border)] rounded'

# Society Lead Form
class SocietyLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'society_university', 'lead_focus', 'contact_method', 'toad_customer', 'toad_customer_date', 'initial_message_sent', 'initial_message_sent_date', 'no_response', 'no_response_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter society lead name'}),
            'society_university': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'lead_focus': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'contact_method': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'toad_customer': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'toad_customer_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'initial_message_sent': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_message_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'no_response': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'no_response_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['society_university'].required = False
        self.fields['society_university'].empty_label = "Select a university (optional)"
        self.fields['toad_customer_date'].required = False
        self.fields['initial_message_sent_date'].required = False
        self.fields['no_response_date'].required = False
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.lead_type = 'society'
        if commit:
            instance.save()
        return instance

# B2B Lead Form (with company fields)
class B2BLeadForm(forms.ModelForm):
    # Add company-related fields
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        empty_label="Select a company (optional)",
        widget=forms.Select(attrs={'class': BASE_INPUT_CLASS})
    )
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'name@example.com'})
    )
    email_template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.all(),
        required=False,
        empty_label="Select a template (optional)",
        widget=forms.Select(attrs={'class': BASE_INPUT_CLASS})
    )
    email_subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter email subject'})
    )
    personalised_email_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 6, 'placeholder': 'Personalised email copy'})
    )
    initial_email_sent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS})
    )
    initial_email_sent_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'})
    )
    initial_email_response = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS})
    )
    initial_email_response_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'})
    )
    
    class Meta:
        model = Lead
        fields = ['name', 'contact_method', 'toad_customer', 'toad_customer_date', 'initial_message_sent', 'initial_message_sent_date', 'no_response', 'no_response_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter contact person name'}),
            'contact_method': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'toad_customer': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'toad_customer_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'initial_message_sent': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_message_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'no_response': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'no_response_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['toad_customer_date'].required = False
        self.fields['initial_message_sent_date'].required = False
        self.fields['no_response_date'].required = False
        self.fields['company'].queryset = Company.objects.order_by('company_name')
        self.fields['email_template'].queryset = EmailTemplate.objects.order_by('name')
        
        # If editing existing lead, populate company data
        if self.instance and self.instance.pk:
            company = getattr(self.instance, 'company', None)
            self.fields['company'].initial = company
            if company:
                self.fields['contact_email'].initial = company.contact_email
                self.fields['email_template'].initial = company.email_template
                self.fields['email_subject'].initial = company.email_subject
                self.fields['personalised_email_text'].initial = company.personalised_email_text
                self.fields['initial_email_sent'].initial = company.initial_email_sent
                self.fields['initial_email_sent_date'].initial = company.initial_email_sent_date
                self.fields['initial_email_response'].initial = company.initial_email_response
                self.fields['initial_email_response_date'].initial = company.initial_email_response_date
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.lead_type = 'b2b'
        if commit:
            instance.save()
            
            # Handle B2B email automation metadata
            company = self.cleaned_data.get('company')
            contact_email = self.cleaned_data.get('contact_email') or ''
            email_template = self.cleaned_data.get('email_template')
            email_subject = self.cleaned_data.get('email_subject') or ''
            personalised_email_text = self.cleaned_data.get('personalised_email_text') or ''
            initial_email_sent = bool(self.cleaned_data.get('initial_email_sent'))
            initial_email_sent_date = self.cleaned_data.get('initial_email_sent_date')
            initial_email_response = bool(self.cleaned_data.get('initial_email_response'))
            initial_email_response_date = self.cleaned_data.get('initial_email_response_date')

            instance.company = company
            if company:
                company.contact_email = contact_email
                company.email_template = email_template
                company.email_subject = email_subject
                company.personalised_email_text = personalised_email_text
                company.initial_email_sent = initial_email_sent
                company.initial_email_sent_date = initial_email_sent_date
                company.initial_email_response = initial_email_response
                company.initial_email_response_date = initial_email_response_date
                company.save()
            instance.save(update_fields=['company'])
        return instance

class LeadMessageForm(forms.ModelForm):
    class Meta:
        model = LeadMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 4, 'placeholder': 'Enter message content'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Validation is handled by the model constraint, but we can add form-level validation if needed
        return cleaned_data

# B2B-specific forms
class CompanySectorForm(forms.ModelForm):
    class Meta:
        model = CompanySector
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter sector name (e.g., Technology, Finance)'})
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'company_name',
            'status',
            'email_status',
            'company_sector',
            'contact_person',
            'contact_email',
            'email_template',
            'email_subject',
            'personalised_email_text',
            'initial_email_sent',
            'initial_email_sent_date',
            'second_email_sent_date',
            'third_email_sent_date',
            'fourth_email_sent_date',
            'initial_email_response',
            'initial_email_response_date',
            'call_made',
            'email_failed_date',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter company name'}),
            'status': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'email_status': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'company_sector': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'contact_person': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter contact person name'}),
            'contact_email': forms.EmailInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'name@example.com'}),
            'email_template': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'email_subject': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter email subject'}),
            'personalised_email_text': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 5, 'placeholder': 'Personalised email copy'}),
            'initial_email_sent': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_email_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'second_email_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'third_email_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'fourth_email_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'call_made': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_email_response': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_email_response_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'email_failed_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_template'].required = False
        self.fields['email_template'].empty_label = "Select a template (optional)"
        self.fields['email_template'].queryset = EmailTemplate.objects.order_by('company_sector', 'email_number')
        self.fields['company_sector'].required = False
        self.fields['company_sector'].empty_label = "Select a sector (optional)"
        self.fields['company_sector'].queryset = CompanySector.objects.order_by('name')
        self.fields['email_status'].required = False
        self.fields['email_status'].empty_label = "Select email status (optional)"
        self.fields['second_email_sent_date'].required = False
        self.fields['third_email_sent_date'].required = False
        self.fields['fourth_email_sent_date'].required = False
        self.fields['email_failed_date'].required = False
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-set initial_email_sent_date to today if initial_email_sent is checked and date is not set
        if instance.initial_email_sent and not instance.initial_email_sent_date:
            from django.utils import timezone
            instance.initial_email_sent_date = timezone.now().date()
        
        # Auto-set initial_email_response_date to today if initial_email_response is checked and date is not set
        if instance.initial_email_response and not instance.initial_email_response_date:
            from django.utils import timezone
            instance.initial_email_response_date = timezone.now().date()
        
        if commit:
            instance.save()
        return instance

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'company_sector', 'email_number', 'subject', 'body']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': BASE_INPUT_CLASS,
                'placeholder': 'Enter template name (e.g., "Wedding Venues - Initial Outreach")'
            }),
            'company_sector': forms.Select(attrs={
                'class': BASE_INPUT_CLASS,
            }),
            'email_number': forms.Select(attrs={
                'class': BASE_INPUT_CLASS,
            }),
            'subject': forms.TextInput(attrs={
                'class': BASE_INPUT_CLASS,
                'placeholder': 'Email subject - use {company_name}, {contact_person} for personalization'
            }),
            'body': forms.Textarea(attrs={
                'class': BASE_INPUT_CLASS,
                'rows': 12,
                'placeholder': 'Email body - use {company_name}, {contact_person}, {personalised_template_url} for personalization'
            }),
        }
        help_texts = {
            'subject': 'Available placeholders: {company_name}, {contact_person}',
            'body': 'Available placeholders: {company_name}, {contact_person}, {personalised_template_url}',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_sector'].queryset = CompanySector.objects.order_by('name')
        self.fields['company_sector'].empty_label = "Select a sector"

class LeadFocusForm(forms.ModelForm):
    class Meta:
        model = LeadFocus
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter focus area name'
            })
        }

class ContactMethodForm(forms.ModelForm):
    class Meta:
        model = ContactMethod
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter contact method name'
            })
        }

class SocietyUniversityForm(forms.ModelForm):
    class Meta:
        model = SocietyUniversity
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter university name'
            })
        }

class SocietyLinkForm(forms.ModelForm):
    class Meta:
        model = SocietyLink
        fields = ['name', 'image', 'society_university', 'lead']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter society name'}),
            'image': forms.FileInput(attrs={'class': BASE_INPUT_CLASS, 'accept': 'image/*'}),
            'society_university': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'lead': forms.Select(attrs={'class': BASE_INPUT_CLASS})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['society_university'].required = True
        self.fields['society_university'].empty_label = "Select a university"
        self.fields['lead'].required = False
        self.fields['lead'].empty_label = "Select a lead (optional)"
        # Filter leads to only show society leads
        self.fields['lead'].queryset = Lead.objects.filter(lead_type='society')

class CustomerTemplateForm(forms.ModelForm):
    class Meta:
        model = CustomerTemplate
        fields = [
            'company_sector',
            'playbook_name',
            'main_header_description',
            'video_1',
            'used_by',
            'grid_1_title',
            'grid_1_header_description',
            'grid_1_subheader',
            'grid_1_bullet_1',
            'grid_1_bullet_2',
            'grid_1_bullet_3',
            'grid_1_bullet_4',
            'grid_1_video',
            'grid_2_title',
            'grid_2_header_description',
            'grid_2_subheader',
            'grid_2_bullet_1',
            'grid_2_bullet_2',
            'grid_2_bullet_3',
            'grid_2_bullet_4',
            'grid_2_video',
            'grid_3_title',
            'grid_3_header_description',
            'grid_3_subheader',
            'grid_3_bullet_1',
            'grid_3_bullet_2',
            'grid_3_bullet_3',
            'grid_3_bullet_4',
            'grid_3_video',
            'section_2_title',
            'section_2_card_1_title',
            'section_2_card_1_description',
            'section_2_card_2_title',
            'section_2_card_2_description',
            'section_2_card_3_title',
            'section_2_card_3_description',
            'section_2_card_4_title',
            'section_2_card_4_description',
        ]
        widgets = {
            'company_sector': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'playbook_name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter playbook name'}),
            'main_header_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 4, 'placeholder': 'Enter main header description'}),
            'video_1': forms.FileInput(attrs={'class': BASE_INPUT_CLASS, 'accept': 'video/*'}),
            'used_by': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Used by event teams, venues and planners'}),
            'grid_1_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 1 title'}),
            'grid_1_header_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter grid 1 header description'}),
            'grid_1_subheader': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 1 subheader'}),
            'grid_1_bullet_1': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 1'}),
            'grid_1_bullet_2': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 2'}),
            'grid_1_bullet_3': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 3'}),
            'grid_1_bullet_4': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 4'}),
            'grid_1_video': forms.FileInput(attrs={'class': BASE_INPUT_CLASS, 'accept': 'video/*'}),
            'grid_2_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 2 title'}),
            'grid_2_header_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter grid 2 header description'}),
            'grid_2_subheader': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 2 subheader'}),
            'grid_2_bullet_1': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 1'}),
            'grid_2_bullet_2': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 2'}),
            'grid_2_bullet_3': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 3'}),
            'grid_2_bullet_4': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 4'}),
            'grid_2_video': forms.FileInput(attrs={'class': BASE_INPUT_CLASS, 'accept': 'video/*'}),
            'grid_3_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 3 title'}),
            'grid_3_header_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter grid 3 header description'}),
            'grid_3_subheader': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter grid 3 subheader'}),
            'grid_3_bullet_1': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 1'}),
            'grid_3_bullet_2': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 2'}),
            'grid_3_bullet_3': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 3'}),
            'grid_3_bullet_4': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter bullet point 4'}),
            'grid_3_video': forms.FileInput(attrs={'class': BASE_INPUT_CLASS, 'accept': 'video/*'}),
            'section_2_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Why venues love Toad'}),
            'section_2_card_1_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter card 1 title'}),
            'section_2_card_1_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter card 1 description'}),
            'section_2_card_2_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter card 2 title'}),
            'section_2_card_2_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter card 2 description'}),
            'section_2_card_3_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter card 3 title'}),
            'section_2_card_3_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter card 3 description'}),
            'section_2_card_4_title': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter card 4 title'}),
            'section_2_card_4_description': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 3, 'placeholder': 'Enter card 4 description'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up company sector field
        self.fields['company_sector'].required = False
        self.fields['company_sector'].empty_label = "Select a company sector (optional)"
        self.fields['company_sector'].queryset = CompanySector.objects.order_by('name')
        # Make video fields optional
        self.fields['video_1'].required = False
        self.fields['grid_1_video'].required = False
        self.fields['grid_2_video'].required = False
        self.fields['grid_3_video'].required = False


# Bulk Upload Forms
class CompanyBulkSectorForm(forms.Form):
    """Form for selecting sector in bulk upload"""
    company_sector = forms.ModelChoiceField(
        queryset=CompanySector.objects.order_by('name'),
        required=True,
        empty_label="Select a sector",
        widget=forms.Select(attrs={'class': BASE_INPUT_CLASS})
    )
    csv_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': BASE_INPUT_CLASS,
            'accept': '.csv',
        }),
        help_text='Optional: Upload a CSV file with columns: company_name, contact_person, contact_email'
    )


class CompanyBulkForm(forms.Form):
    """Form for a single company entry in bulk upload"""
    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': BASE_INPUT_CLASS,
            'placeholder': 'Enter company name'
        })
    )
    contact_person = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': BASE_INPUT_CLASS,
            'placeholder': 'Enter contact person name'
        })
    )
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': BASE_INPUT_CLASS,
            'placeholder': 'name@example.com'
        })
    )


CompanyBulkFormSet = formset_factory(
    CompanyBulkForm,
    extra=50,  # Start with 50 empty forms
    min_num=1,  # At least 1 form required
    can_delete=False
)



from django import forms
from .models import (
    Lead,
    LeadFocus,
    ContactMethod,
    LeadMessage,
    SocietyLink,
    SocietyUniversity,
    Feedback,
    Company,
    CompanySector,
    EmailTemplate,
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
        self.fields['company'].queryset = Company.objects.order_by('name')
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
            'name',
            'contact_email',
            'email_template',
            'email_subject',
            'personalised_email_text',
            'initial_email_sent',
            'initial_email_sent_date',
            'initial_email_response',
            'initial_email_response_date',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter company name'}),
            'contact_email': forms.EmailInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'name@example.com'}),
            'email_template': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'email_subject': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter email subject'}),
            'personalised_email_text': forms.Textarea(attrs={'class': BASE_INPUT_CLASS, 'rows': 5, 'placeholder': 'Personalised email copy'}),
            'initial_email_sent': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_email_sent_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
            'initial_email_response': forms.CheckboxInput(attrs={'class': BASE_CHECKBOX_CLASS}),
            'initial_email_response_date': forms.DateInput(attrs={'class': BASE_INPUT_CLASS, 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_template'].required = False
        self.fields['email_template'].empty_label = "Select a template (optional)"
        self.fields['email_template'].queryset = EmailTemplate.objects.order_by('name')


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'text']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': BASE_INPUT_CLASS,
                'placeholder': 'Enter template name'
            }),
            'text': forms.Textarea(attrs={
                'class': BASE_INPUT_CLASS,
                'rows': 12,
                'placeholder': 'Write your email template content here...'
            }),
        }


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

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'name',
            'regularly_using_toad', 
            'usage_reason', 
            'organization_method',
            'organization_other',
            'non_user_suggestion', 
            'user_improvement', 
            'team_toad_interest',
            'would_share',
            'testimonial_quote',
            'testimonial_first_name',
            'testimonial_job_title'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Your name (optional)'
            }),
            'regularly_using_toad': forms.RadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            ),
            'usage_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 4,
                'placeholder': 'Tell us about your experience...'
            }),
            'organization_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'organization_other': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Please specify...'
            }),
            'non_user_suggestion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 4,
                'placeholder': 'What would make you use Toad?'
            }),
            'user_improvement': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 4,
                'placeholder': 'How can we make Toad better for you?'
            }),
            'team_toad_interest': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 3,
                'placeholder': 'Would team features be useful for you?'
            }),
            'would_share': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] border-[var(--inline-input-border)] rounded'
            }),
            'testimonial_quote': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 3,
                'placeholder': 'Share your testimonial about why you love Toad...'
            }),
            'testimonial_first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Your first name'
            }),
            'testimonial_job_title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Your job title (e.g., Marketing Manager)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional except the core question
        self.fields['name'].required = False
        self.fields['usage_reason'].required = False
        self.fields['organization_method'].required = False
        self.fields['organization_other'].required = False
        self.fields['non_user_suggestion'].required = False
        self.fields['user_improvement'].required = False
        self.fields['team_toad_interest'].required = False
        self.fields['testimonial_quote'].required = False
        self.fields['testimonial_first_name'].required = False
        self.fields['testimonial_job_title'].required = False
        
        # Add empty label for organization method
        self.fields['organization_method'].empty_label = "Select an option..."



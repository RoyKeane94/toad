from django import forms
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink, SocietyUniversity, Feedback, Company, CompanySector, B2BLink

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
        
        # If editing existing lead, populate company from B2BLink
        if self.instance and self.instance.pk:
            try:
                if hasattr(self.instance, 'b2b_link') and self.instance.b2b_link:
                    self.fields['company'].initial = self.instance.b2b_link.company
            except:
                pass
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.lead_type = 'b2b'
        if commit:
            instance.save()
            
            # Handle company association via B2BLink
            company = self.cleaned_data.get('company')
            if company:
                # Create or update B2BLink
                b2b_link, created = B2BLink.objects.get_or_create(
                    lead=instance,
                    defaults={'name': instance.name, 'company': company}
                )
                if not created:
                    b2b_link.company = company
                    b2b_link.name = instance.name
                    b2b_link.save()
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
        fields = ['name', 'sector', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter company name'}),
            'sector': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'website': forms.URLInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'https://example.com'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sector'].required = False
        self.fields['sector'].empty_label = "Select a sector (optional)"
        self.fields['website'].required = False

class B2BLinkForm(forms.ModelForm):
    class Meta:
        model = B2BLink
        fields = ['name', 'company', 'lead']
        widgets = {
            'name': forms.TextInput(attrs={'class': BASE_INPUT_CLASS, 'placeholder': 'Enter contact person name'}),
            'company': forms.Select(attrs={'class': BASE_INPUT_CLASS}),
            'lead': forms.Select(attrs={'class': BASE_INPUT_CLASS})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].required = False
        self.fields['company'].empty_label = "Select a company (optional)"
        self.fields['lead'].required = False
        self.fields['lead'].empty_label = "Select a lead (optional)"
        # Filter leads to only show B2B leads
        self.fields['lead'].queryset = Lead.objects.filter(lead_type='b2b')

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



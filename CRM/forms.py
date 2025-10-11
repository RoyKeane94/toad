from django import forms
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink, SocietyUniversity, Feedback

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'society_university', 'lead_focus', 'contact_method', 'toad_customer', 'toad_customer_date', 'initial_message_sent', 'initial_message_sent_date', 'no_response', 'no_response_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter lead name'
            }),
            'society_university': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'lead_focus': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'contact_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'toad_customer': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] border-[var(--inline-input-border)] rounded'
            }),
            'toad_customer_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'type': 'date'
            }),
            'initial_message_sent': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] border-[var(--inline-input-border)] rounded'
            }),
            'initial_message_sent_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'type': 'date'
            }),
            'no_response': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] border-[var(--inline-input-border)] rounded'
            }),
            'no_response_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make society university field optional and set empty label
        self.fields['society_university'].required = False
        self.fields['society_university'].empty_label = "Select a university (optional)"
        # Make date fields optional
        self.fields['toad_customer_date'].required = False
        self.fields['initial_message_sent_date'].required = False
        self.fields['no_response_date'].required = False

class LeadMessageForm(forms.ModelForm):
    class Meta:
        model = LeadMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'rows': 4,
                'placeholder': 'Enter message content'
            })
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
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter society name'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'accept': 'image/*'
            }),
            'society_university': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'lead': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make university field required
        self.fields['society_university'].required = True
        self.fields['society_university'].empty_label = "Select a university"
        # Make lead field optional
        self.fields['lead'].required = False
        self.fields['lead'].empty_label = "Select a lead (optional)"

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
            'would_share'
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
        
        # Add empty label for organization method
        self.fields['organization_method'].empty_label = "Select an option..."



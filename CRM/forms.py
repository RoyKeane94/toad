from django import forms
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink, TestSocietyLink, SocietyUniversity

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'lead_focus', 'contact_method']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter lead name'
            }),
            'lead_focus': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            }),
            'contact_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent'
            })
        }

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
        fields = ['name', 'image', 'society_university']
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
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make university field required
        self.fields['society_university'].required = True
        self.fields['society_university'].empty_label = "Select a university"

class TestSocietyLinkForm(forms.ModelForm):
    class Meta:
        model = TestSocietyLink
        fields = ['title', 'photo']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter society title'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        print("=== FORM INIT ===")
        print(f"Form args: {args}")
        print(f"Form kwargs: {kwargs}")
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        print("=== FORM SAVE DEBUG ===")
        print(f"Form save called with commit={commit}")
        print(f"Form cleaned data: {self.cleaned_data}")
        print(f"Form instance: {self.instance}")
        
        if commit:
            print("About to call super().save()...")
            instance = super().save(commit=commit)
            print(f"Super save completed, instance: {instance}")
            print(f"Instance photo field: {instance.photo}")
            return instance
        else:
            print("Commit=False, returning instance without saving")
            return self.instance

from django import forms
from .models import Lead, LeadFocus, ContactMethod, LeadMessage, SocietyLink

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

class SocietyLinkForm(forms.ModelForm):
    class Meta:
        model = SocietyLink
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter society name'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-[var(--inline-input-border)] rounded-md focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"🔧 SOCIETY LINK FORM INIT DEBUG ===")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        print(f"Data: {getattr(self, 'data', 'NO DATA')}")
        print(f"Files: {getattr(self, 'files', 'NO FILES')}")
    
    def is_valid(self):
        print(f"🔍 SOCIETY LINK FORM VALIDATION DEBUG ===")
        print(f"Data: {self.data}")
        print(f"Files: {self.files}")
        print(f"Initial: {self.initial}")
        
        is_valid = super().is_valid()
        print(f"Form is valid: {is_valid}")
        
        if not is_valid:
            print(f"❌ Validation errors: {self.errors}")
            print(f"❌ Non-field errors: {self.non_field_errors()}")
        else:
            print(f"✅ Form validation passed")
            print(f"✅ Cleaned data: {self.cleaned_data}")
        
        return is_valid
    
    def save(self, commit=True):
        print(f"💾 SOCIETY LINK FORM SAVE DEBUG ===")
        print(f"Commit: {commit}")
        print(f"Instance: {self.instance}")
        print(f"Cleaned data: {self.cleaned_data}")
        
        try:
            instance = super().save(commit=commit)
            print(f"✅ Save successful: {instance}")
            return instance
        except Exception as e:
            print(f"❌ Save failed: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Save traceback: {traceback.format_exc()}")
            raise

"""
Passwordless Login Forms
========================
Forms for requesting and verifying email login codes.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class RequestLoginCodeForm(forms.Form):
    """Form for requesting a login code via email."""
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your email address',
            'autofocus': True,
            'autocomplete': 'email'
        }),
        help_text='We\'ll send a 6-digit code to this email address.'
    )
    
    def clean_email(self):
        """Normalize and validate email."""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # Check if user exists
            try:
                user = User.objects.get(email=email)
                # Check if account is locked
                from django.utils import timezone
                if user.account_locked_until and user.account_locked_until > timezone.now():
                    raise ValidationError(
                        'This account is temporarily locked. Please try again later or contact support.'
                    )
            except User.DoesNotExist:
                # Don't reveal if email exists for security
                pass
        
        return email


class VerifyLoginCodeForm(forms.Form):
    """Form for verifying the login code."""
    code = forms.CharField(
        label='Verification Code',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-10 pr-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)] text-center',
            'placeholder': '000000',
            'autofocus': True,
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'style': 'font-size: 1.5rem; letter-spacing: 0.5rem; font-family: "Courier New", monospace; font-weight: bold;'
        }),
        help_text='Enter the 6-digit code sent to your email.'
    )
    email = forms.EmailField(widget=forms.HiddenInput())
    
    def clean_code(self):
        """Validate code format."""
        code = self.cleaned_data.get('code')
        if code:
            # Remove any spaces or dashes
            code = re.sub(r'[\s-]', '', code)
            # Check if numeric
            if not code.isdigit():
                raise ValidationError('Code must contain only numbers.')
            if len(code) != 6:
                raise ValidationError('Code must be exactly 6 digits.')
        return code


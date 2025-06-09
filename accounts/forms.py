from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from .models import User

class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email instead of username
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your email address',
        }),
        label='Email Address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your password',
        }),
        label='Password'
    )

    def clean(self):
        email = self.cleaned_data.get('username')  # Django auth form uses 'username' field name
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,  # Our custom backend uses email as username
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Please enter a correct email and password. Note that both fields may be case-sensitive.'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class CustomUserCreationForm(UserCreationForm):
    """
    Custom registration form that uses email instead of username
    and includes first_name as required field
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your email address',
        }),
        label='Email Address',
        help_text='Required. Enter a valid email address.'
    )
    
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your first name',
        }),
        label='First Name',
        help_text='Required. Enter your first name.'
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Create a password',
        }),
        label='Password'
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Confirm your password',
        }),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user

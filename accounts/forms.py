from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User, BetaTester

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


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter your first name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter your last name (optional)',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
                'placeholder': 'Enter your email address',
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name (Optional)',
            'email': 'Email Address',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name or not first_name.strip():
            raise ValidationError('First name is required.')
        return first_name.strip()


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with Toad styling
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
            'placeholder': 'Enter your current password',
        }),
        label='Current Password'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
            'placeholder': 'Enter your new password',
        }),
        label='New Password'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-[var(--border-color)] rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-transparent',
            'placeholder': 'Confirm your new password',
        }),
        label='Confirm New Password'
    )


class AccountDeletionForm(forms.Form):
    """
    Form for account deletion confirmation
    """
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-red-300 text-red-600 focus:ring-red-500',
        }),
        label='I understand that this action cannot be undone'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 bg-[var(--container-bg)] border border-red-300 rounded-md text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent',
            'placeholder': 'Enter your password to confirm',
        }),
        label='Password Confirmation'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError('Incorrect password.')
        return password


class BetaTesterForm(forms.ModelForm):
    """
    Form for beta tester waitlist signup
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-transparent border-b-2 border-[var(--border-color)] px-2 py-3 text-[var(--text-primary)] text-lg placeholder-[var(--text-secondary)] focus:outline-none focus:border-[var(--primary-action-bg)] hover:border-[var(--primary-action-hover-bg)] transition-colors duration-200 cursor-text',
            'placeholder': 'Enter your email address',
        }),
        label='',
        help_text=''
    )

    class Meta:
        model = BetaTester
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if BetaTester.objects.filter(email=email).exists():
            raise forms.ValidationError('You\'re already on the waitlist! We\'ll notify you when it\'s your turn.')
        return email

    def save(self, commit=True):
        beta_tester = super().save(commit=False)
        beta_tester.email = self.cleaned_data['email']
        if commit:
            beta_tester.save()
        return beta_tester

class ForgotPasswordForm(forms.Form):
    """
    Form for requesting password reset
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-[var(--border-color)] rounded-md shadow-sm placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-action-bg)] focus:border-[var(--primary-action-bg)] text-[var(--text-primary)]',
            'placeholder': 'Enter your email address',
        }),
        label='Email Address',
        help_text='Enter the email address associated with your account.'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email

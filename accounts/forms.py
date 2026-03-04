from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm # Import built-in form
from .models import Profile, PaymentHistory  # Add PaymentHistory import

# Input widget attributes
INPUT_FIELD_ATTRS = {
    'class': 'input-field w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
}

# Custom registration form
class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Last Name'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Confirm Password'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

# Form for editing user profile
class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Last Name'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Email'}))
    
    # Hidden field to handle profile picture removal via JavaScript
    clear_image = forms.BooleanField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Profile
        fields = ['telegram', 'phone', 'image']
        widgets = {
            'telegram': forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Telegram'}),
            'phone': forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Phone'}),
            'image': forms.FileInput(attrs={**INPUT_FIELD_ATTRS, 'class': 'hidden', 'id': 'imageInput', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data['username']
        if username != self.user.username and User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != self.user.email and User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # If the clear_image hidden field is checked, remove the photo
        if self.cleaned_data.get('clear_image'):
            profile.image = None
            
        if commit:
            # Update User model fields
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.save()
            profile.save()
        return profile

# Form for changing password
class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Current Password'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'New Password'}))
    confirm_new_password = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Confirm New Password'}))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValidationError("New passwords do not match.")
        return cleaned_data

# Form for depositing USDT
class DepositForm(forms.Form):
    transaction_id = forms.CharField(max_length=100, widget=forms.TextInput(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Binance Order ID'}))
    payment_note = forms.CharField(widget=forms.Textarea(attrs={**INPUT_FIELD_ATTRS, 'placeholder': 'Payment Note (Optional)', 'rows': 4}), required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data['transaction_id']
        if not transaction_id:
            raise ValidationError("Binance Order ID is required.")
        # Check for duplicates per user
        if self.user and PaymentHistory.objects.filter(user=self.user, transaction_id=transaction_id).exists():
            raise ValidationError("This transaction ID has already been used in a previous deposit request.")
        return transaction_id

# Form for user settings
class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['timezone', 'theme_preference', 'auto_renew_subscription', 'auto_refill_tokens', 'email_notifications', 'push_notifications']
        widgets = {
            'timezone': forms.Select(attrs=INPUT_FIELD_ATTRS),
            'theme_preference': forms.Select(attrs=INPUT_FIELD_ATTRS),
            'auto_renew_subscription': forms.CheckboxInput(),
            'auto_refill_tokens': forms.CheckboxInput(),
            'email_notifications': forms.CheckboxInput(),
            'push_notifications': forms.CheckboxInput(),
        }

# --- Add this new form at the end ---
class EmailValidationPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("This email address is not registered. Please register first.")
        return email
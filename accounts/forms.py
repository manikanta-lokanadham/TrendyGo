from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Address

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar']
        
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your street address'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apartment, suite, unit, etc. (optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your state/province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your postal code'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 
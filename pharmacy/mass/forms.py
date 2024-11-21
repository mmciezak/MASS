from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")
    first_name = forms.CharField(max_length=30, required=True, help_text="Enter your first name.")
    last_name = forms.CharField(max_length=30, required=True, help_text="Enter your last name.")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=50, label="Imię", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Wprowadź swoje imię'
    }))
    last_name = forms.CharField(max_length=50, label="Nazwisko", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Wprowadź swoje nazwisko'
    }))
    address = forms.CharField(max_length=255, label="Adres", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Wprowadź swój adres do wysyłki'
    }))
    city = forms.CharField(max_length=100, label="Miasto", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Miasto'
    }))
    zip_code = forms.CharField(max_length=20, label="Kod pocztowy", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Kod pocztowy'
    }))
    phone = forms.CharField(max_length=15, label="Numer telefonu", widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Numer telefonu'
    }))
    payment = forms.ChoiceField(
        choices=[('karta', 'Karta kredytowa/debetowa'), ('paypal', 'PayPal')],
        label="Metoda płatności",
        widget=forms.RadioSelect
    )


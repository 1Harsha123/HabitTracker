from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import re


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email","first_name","last_name", "password1", "password2"]
    
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            
            if not re.search(r"[A-Z]", password1):
                raise forms.ValidationError("Password must contain at least 1 uppercase letter.")
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                raise forms.ValidationError("Password must contain at least 1 special character.")
        return password1
    
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter username"
        })

        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter email"
        })
        
        self.fields["first_name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter first name"
        })
        self.fields["last_name"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter last name"
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Create password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm password"
        })
        for field in self.fields:
            self.fields[field].required = True
    

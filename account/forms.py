from django.forms import ModelForm
from .models import *
from django import forms

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','password','email']
        help_texts = {
            "username":None
        }
        labels = {
            "username":""
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder":"Tên đăng nhập",
                "class":"w-full h-12 px-3 rounded-xl bg-gray-100 outline-none"
            }),
            "password": forms.PasswordInput(attrs={
                "placeholder":"Mật khẩu",
                "class":"w-full h-12 px-3 rounded-xl bg-gray-100 outline-none"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder":"Email",
                "class":"w-full h-12 px-3 rounded-xl bg-gray-100 outline-none "
            }),
        }

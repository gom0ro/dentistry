# forms.py
from django import forms
from .models import CourseApplication
from django.contrib.auth.models import User
from .models import UserProfile

class CourseApplicationForm(forms.ModelForm):
    class Meta:
        model = CourseApplication
        fields = ['name', 'phone', 'email', 'course']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя',
                'id': 'id_name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX',
                'id': 'id_phone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'id': 'id_email'
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_course'
            })
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Простая валидация телефона
        if phone and len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 10:
            raise forms.ValidationError("Введите корректный номер телефона")
        return phone
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'phone', 'specialization', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
        }

class UserSettingsForm(forms.ModelForm):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Текущий пароль'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Новый пароль'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Подтвердите пароль'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        current_password = cleaned_data.get('current_password')
        
        if new_password or confirm_password:
            if not current_password:
                raise forms.ValidationError('Для смены пароля введите текущий пароль')
            
            if not self.instance.check_password(current_password):
                raise forms.ValidationError('Текущий пароль неверен')
            
            if new_password != confirm_password:
                raise forms.ValidationError('Новый пароль и подтверждение не совпадают')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        
        return user
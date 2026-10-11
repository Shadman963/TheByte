from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import CustomerProfile, MenuItem, KitchenSetting, Category


class CustomerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'name@example.com',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    phone = forms.CharField(
        max_length=25,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': '017XXXXXXXX',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    default_area = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Mirpur, Dhanmondi, Uttara...',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    default_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'placeholder': 'Detailed delivery address (House, Road, Block, Flat)',
            'rows': 2,
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create strong password',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choose username',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            profile, _ = CustomerProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone', '')
            profile.default_area = self.cleaned_data.get('default_area', '')
            profile.default_address = self.cleaned_data.get('default_address', '')
            profile.save()
            user.profile = profile
        return user


class CustomerLoginForm(forms.Form):
    username_or_email = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Username or Email address',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        ident = cleaned_data.get('username_or_email', '').strip()
        password = cleaned_data.get('password')

        if ident and password:
            user = authenticate(username=ident, password=password)
            if not user and '@' in ident:
                user_obj = User.objects.filter(email__iexact=ident).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)

            if not user:
                raise ValidationError("Invalid username/email or password.")
            self.user = user

        return cleaned_data


class CustomerProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    phone = forms.CharField(
        max_length=25,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    default_area = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )
    default_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-4 py-2.5 rounded-xl border border-gray-300 text-sm focus:outline-none focus:border-byte-maroon focus:ring-1 focus:ring-byte-maroon'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class MenuItemQuickForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'tagline', 'description',
            'price', 'discount_price', 'portion_size', 'spice_level',
            'is_available', 'is_featured', 'is_vegetarian', 'is_frozen'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'tagline': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'discount_price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'portion_size': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'spice_level': forms.Select(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
        }


class KitchenSettingForm(forms.ModelForm):
    class Meta:
        model = KitchenSetting
        fields = [
            'restaurant_name', 'phone', 'email', 'address', 'is_kitchen_open',
            'opening_time', 'closing_time', 'estimated_delivery_time',
            'minimum_order_amount', 'delivery_fee', 'free_delivery_above',
            'announcement_banner', 'delivery_areas'
        ]
        widgets = {
            'restaurant_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'opening_time': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'closing_time': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'estimated_delivery_time': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'minimum_order_amount': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'delivery_fee': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'free_delivery_above': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'announcement_banner': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
            'delivery_areas': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-3 py-2 rounded-xl border border-gray-300 text-sm'}),
        }

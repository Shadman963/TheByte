import random
import string
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver



def generate_order_number():
    rand = ''.join(random.choices(string.digits, k=5))
    return f"BYTE-{rand}"


class KitchenSetting(models.Model):
    restaurant_name = models.CharField(max_length=100, default="The BYTE")
    tagline = models.CharField(max_length=200, default="Fresh • Tasty • Budget-Friendly")
    mission_statement = models.TextField(
        default="We don’t just cook food—we cook with responsibility. Freshly prepared meals, honest portions, and flavors you’ll come back for."
    )
    story = models.TextField(
        default="The BYTE was born from a passion for cooking and the dream of creating our own restaurant. With professional training and a clear purpose, we started this to serve healthy, tasty, and budget-friendly meals for students, office workers, and daily hustlers. Every meal is freshly cooked each day, carefully portioned, and made with care—because good food should always be reliable and satisfying."
    )
    phone = models.CharField(max_length=50, default="01718-244371")
    email = models.EmailField(default="thebyte39@gmail.com")
    address = models.CharField(max_length=255, default="Mirpur DOHS / Central Cloud Kitchen, Dhaka, Bangladesh")
    is_kitchen_open = models.BooleanField(default=True, help_text="Accepting new orders")
    opening_time = models.CharField(max_length=50, default="10:00 AM")
    closing_time = models.CharField(max_length=50, default="11:00 PM")
    estimated_delivery_time = models.CharField(max_length=50, default="25 - 40 Mins")
    minimum_order_amount = models.DecimalField(max_digits=8, decimal_places=2, default=120.00)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=40.00)
    free_delivery_above = models.DecimalField(max_digits=8, decimal_places=2, default=600.00)
    currency_symbol = models.CharField(max_length=10, default="৳")
    announcement_banner = models.CharField(
        max_length=255,
        default="⚡ Freshly cooked daily meals! Free delivery on orders over ৳600. Order now!",
        blank=True
    )
    delivery_areas = models.TextField(
        default="Mirpur, Dhanmondi, Gulshan, Banani, Uttara, Mohakhali, Panthapath, Mohammadpur, Lalmatia, Badda, Farmgate",
        help_text="Comma-separated delivery areas"
    )
    facebook_url = models.URLField(blank=True, default="https://facebook.com")
    instagram_url = models.URLField(blank=True, default="https://instagram.com")
    tiktok_url = models.URLField(blank=True, default="https://tiktok.com")

    def __str__(self):
        return f"{self.restaurant_name} Settings"

    def get_delivery_areas_list(self):
        return [area.strip() for area in self.delivery_areas.split(',') if area.strip()]

    class Meta:
        verbose_name = "Kitchen Setting"
        verbose_name_plural = "Kitchen Settings"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    banner_image = models.ImageField(upload_to="categories/", blank=True, null=True)
    static_banner = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    SPICE_CHOICES = [
        ('none', 'Not Spicy'),
        ('mild', 'Mild Spicy'),
        ('medium', 'Medium Spicy (Standard)'),
        ('hot', 'Hot & Spicy'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    static_image = models.CharField(max_length=200, blank=True, null=True)
    portion_size = models.CharField(max_length=100, default="1 Standard Portion")
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)
    is_frozen = models.BooleanField(default=False)
    spice_level = models.CharField(max_length=20, choices=SPICE_CHOICES, default='medium')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def has_discount(self):
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def discount_percent(self):
        if self.has_discount and self.price > 0:
            return int(round((1 - (self.discount_price / self.price)) * 100))
        return 0


class MenuItemAddon(models.Model):
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='addons', blank=True, null=True, help_text="Leave blank if global addon")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        target = self.item.name if self.item else "Global"
        return f"{self.name} (+৳{self.price}) [{target}]"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=25, blank=True)
    default_address = models.TextField(blank=True)
    default_area = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.phone or 'No Phone'})"


@receiver(post_save, sender=User)
def create_customer_profile_on_signup(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.get_or_create(user=instance)


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Order Received'),
        ('confirmed', 'Order Confirmed'),
        ('preparing', 'Kitchen Preparing 🍳'),
        ('ready', 'Ready for Delivery 🛵'),
        ('out_for_delivery', 'Out for Delivery 🚀'),
        ('delivered', 'Delivered 🎉'),
        ('cancelled', 'Cancelled ❌'),
    ]

    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery (COD)'),
        ('bkash', 'bKash Mobile Banking'),
        ('nagad', 'Nagad Mobile Banking'),
        ('card', 'Card Payment on Delivery'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('submitted', 'TrxID Submitted'),
        ('verified', 'Payment Verified'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=30, unique=True, default=generate_order_number)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=25)
    customer_email = models.EmailField(blank=True, null=True)
    delivery_address = models.TextField()
    delivery_area = models.CharField(max_length=100)
    delivery_slot = models.CharField(max_length=100, default="Earliest Available (30-45 mins)")
    customer_notes = models.TextField(blank=True, help_text="Special instructions for cooking or delivery")
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="bKash/Nagad Transaction ID")
    
    order_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=40.00)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} ({self.get_order_status_display()})"

    @property
    def status_step_index(self):
        steps = ['pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered']
        if self.order_status in steps:
            return steps.index(self.order_status)
        return -1

    VALID_TRANSITIONS = {
        'pending': {'confirmed', 'preparing', 'cancelled'},
        'confirmed': {'preparing', 'cancelled'},
        'preparing': {'ready', 'cancelled'},
        'ready': {'out_for_delivery', 'cancelled'},
        'out_for_delivery': {'delivered', 'cancelled'},
        'delivered': set(),
        'cancelled': set(),
    }

    def can_transition_to(self, new_status):
        if new_status == self.order_status:
            return True
        allowed = self.VALID_TRANSITIONS.get(self.order_status, set())
        return new_status in allowed

    @property
    def is_terminal_status(self):
        return self.order_status in ('delivered', 'cancelled')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    special_instructions = models.CharField(max_length=255, blank=True)
    addons = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.item_name} (Order {self.order.order_number})"


class CustomerReview(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default="Food Enthusiast")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.rating}★)"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=150, default="Customer Inquiry")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Msg from {self.name} - {self.subject}"

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

    def resolve_default_static_image(self):
        slug_val = (self.slug or '').lower()
        name_val = (self.name or '').lower()
        frozen = bool(
            self.is_frozen
            or 'frozen' in slug_val
            or (self.category_id and getattr(self.category, 'slug', '') in ('frozen-items', 'ready-to-fry'))
        )

        if 'chicken-fry' in slug_val or 'chicken fry' in name_val or 'chicken fries' in name_val:
            return 'images/menu/frozen_chicken_fry.jpg' if frozen else 'images/menu/chicken_fry.webp'
        if 'strip' in slug_val or 'tender' in slug_val or 'strip' in name_val or 'tender' in name_val:
            return 'images/menu/frozen_chicken_strips.jpg' if frozen else 'images/menu/chicken_tender.webp'
        if 'wing' in slug_val or 'wing' in name_val:
            return 'images/menu/frozen_wings.jpg' if frozen else 'images/menu/crispy_wings.jpeg'
        if 'french-fries' in slug_val or 'french fries' in name_val or 'fries' in name_val:
            return 'images/menu/frozen_french_fries.avif' if frozen else 'images/menu/french_fries.jfif'
        if 'meatball' in slug_val or 'meatball' in name_val:
            return 'images/menu/frozen_meatballs.png' if frozen else 'images/menu/meatballs.jpeg'
        if 'samosa' in slug_val or 'samusa' in slug_val or 'samosa' in name_val or 'samusa' in name_val:
            return 'images/menu/frozen_samosa.webp' if frozen else 'images/menu/samusa.jfif'
        if 'spring-roll' in slug_val or 'spring roll' in name_val:
            return 'images/menu/frozen_spring_roll.jfif' if frozen else 'images/menu/spring_roll.avif'
        if 'combo' in slug_val or 'combo' in name_val:
            return 'images/menu/combo.webp'
        return 'images/frozen_items.jpg' if frozen else 'images/hero_banner.png'

    @property
    def resolved_static_image(self):
        if self.static_image and self.static_image.strip():
            return self.static_image.strip()
        return self.resolve_default_static_image()

    @property
    def valid_uploaded_image_url(self):
        if self.image and getattr(self.image, 'name', None):
            try:
                if self.image.storage.exists(self.image.name):
                    return self.image.url
            except Exception:
                pass
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'menu-item'
            if self.is_frozen and not base_slug.startswith('frozen-'):
                candidate = f"frozen-{base_slug}"
            else:
                candidate = base_slug
            counter = 1
            while MenuItem.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                counter += 1
                candidate = f"{base_slug}-{counter}"
            self.slug = candidate
        if not self.static_image:
            self.static_image = self.resolve_default_static_image()
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

    @property
    def has_style_options(self):
        target_slugs = {
            'chicken-fry',
            'chicken-fries',
            'chicken-fries-frozen',
            'chicken-strips',
            'chicken-tender',
            'chicken-tenders',
            'chicken-wings',
            'crispy-wings',
            'spicy-wings',
            'frozen-chicken-fry',
            'frozen-chicken-strips',
            'frozen-chicken-tender',
            'frozen-wings',
            'frozen-chicken-wings',
            'marinated-wings-frozen',
        }
        if self.slug in target_slugs:
            return True
        lower_name = (self.name or '').lower()
        excluded = ('spring roll', 'samosa', 'samusa', 'meatball', 'combo', 'curry')
        if any(ex in lower_name for ex in excluded):
            return False
        return any(
            k in lower_name
            for k in (
                'chicken fry',
                'chicken fries',
                'chicken strip',
                'chicken tender',
                'chicken wing',
                'wings',
                'fried chicken',
            )
        )

    @property
    def style_options(self):
        if self.has_style_options:
            return ['Spicy', 'Crispy']
        return []


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

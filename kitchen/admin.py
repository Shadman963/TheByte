from django.contrib import admin
from django.utils.html import format_html
from .models import (
    KitchenSetting,
    Category,
    MenuItem,
    MenuItemAddon,
    Order,
    OrderItem,
    CustomerReview,
    ContactMessage,
    CustomerProfile
)

admin.site.site_header = "The BYTE — Cloud Kitchen Management"
admin.site.site_title = "The BYTE Kitchen Admin"
admin.site.index_title = "Kitchen Operations & Order Control"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item_name', 'unit_price', 'quantity', 'subtotal', 'special_instructions', 'addons')
    can_delete = False


class MenuItemAddonInline(admin.TabularInline):
    model = MenuItemAddon
    extra = 1


@admin.register(KitchenSetting)
class KitchenSettingAdmin(admin.ModelAdmin):
    list_display = ('restaurant_name', 'phone', 'is_kitchen_open', 'opening_time', 'closing_time', 'minimum_order_amount', 'delivery_fee')

    def has_add_permission(self, request):
        # Singleton setting
        return not KitchenSetting.objects.exists()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'item_count')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Total Items"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'is_available', 'is_featured', 'is_vegetarian', 'is_frozen', 'order')
    list_editable = ('is_available', 'is_featured', 'order')
    list_filter = ('category', 'is_available', 'is_featured', 'is_vegetarian', 'is_frozen')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MenuItemAddonInline]

    def price_display(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="text-decoration: line-through; color: #888;">৳{}</span> <strong style="color: #6e0f2d;">৳{}</strong>',
                obj.price, obj.discount_price
            )
        return f"৳{obj.price}"
    price_display.short_description = "Price"


@admin.register(MenuItemAddon)
class MenuItemAddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'item', 'is_available')
    list_editable = ('price', 'is_available')
    list_filter = ('is_available',)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'default_area', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'default_address', 'default_area')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'customer_name', 'customer_phone', 'delivery_area', 'total_display', 'payment_info', 'status_badge', 'created_at')
    list_filter = ('order_status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'transaction_id', 'user__username')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'subtotal', 'delivery_fee', 'discount', 'total')
    inlines = [OrderItemInline]

    def total_display(self, obj):
        return f"৳{obj.total}"
    total_display.short_description = "Total"

    def payment_info(self, obj):
        badge_color = "#28a745" if obj.payment_status == 'verified' else ("#ffc107" if obj.payment_status == 'submitted' else "#dc3545")
        return format_html(
            '<span>{}</span><br><span style="padding: 2px 6px; border-radius: 4px; font-size: 11px; background: {}; color: #fff;">{}</span>',
            obj.get_payment_method_display(),
            badge_color,
            obj.get_payment_status_display()
        )
    payment_info.short_description = "Payment"

    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'confirmed': '#17a2b8',
            'preparing': '#6e0f2d',
            'ready': '#6f42c1',
            'out_for_delivery': '#007bff',
            'delivered': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.order_status, '#6c757d')
        return format_html(
            '<span style="padding: 4px 8px; border-radius: 6px; font-weight: bold; background: {}; color: #fff;">{}</span>',
            color,
            obj.get_order_status_display()
        )
    status_badge.short_description = "Status"


@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rating_stars', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('rating', 'is_approved')

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Rating"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_resolved', 'created_at')
    list_editable = ('is_resolved',)
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message')

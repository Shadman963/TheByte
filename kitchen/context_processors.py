from .models import KitchenSetting, Category
from .cart import Cart


def kitchen_context(request):
    try:
        setting = KitchenSetting.objects.first()
        if not setting:
            setting = KitchenSetting.objects.create()
    except Exception:
        setting = None

    categories = Category.objects.filter(is_active=True).prefetch_related('items')

    if hasattr(request, 'session'):
        cart = Cart(request)
        total_qty = len(cart)
        subtotal = float(cart.get_subtotal())
        delivery_fee = float(cart.get_delivery_fee(setting))
        total = float(cart.get_total(setting))
        free_delivery_percent, free_delivery_remaining = cart.get_free_delivery_progress(setting)
        cart_items = list(cart)
    else:
        total_qty = 0
        subtotal = 0.0
        delivery_fee = float(setting.delivery_fee if setting else 40.0)
        total = subtotal + delivery_fee
        free_delivery_percent = 0
        free_delivery_remaining = float(setting.free_delivery_above if setting and setting.free_delivery_above else 0.0)
        cart_items = []

    return {
        'site_setting': setting,
        'nav_categories': categories,
        'cart_items': cart_items,
        'cart_count': total_qty,
        'cart_subtotal': subtotal,
        'cart_delivery_fee': delivery_fee,
        'cart_total': total,
        'cart_free_delivery_percent': free_delivery_percent,
        'cart_free_delivery_remaining': float(free_delivery_remaining),
    }


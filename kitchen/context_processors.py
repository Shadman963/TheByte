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
    else:
        total_qty = 0
        subtotal = 0.0
        delivery_fee = float(setting.delivery_fee if setting else 40.0)
        total = subtotal + delivery_fee

    return {
        'site_setting': setting,
        'nav_categories': categories,
        'cart_count': total_qty,
        'cart_subtotal': subtotal,
        'cart_delivery_fee': delivery_fee,
        'cart_total': total,
    }


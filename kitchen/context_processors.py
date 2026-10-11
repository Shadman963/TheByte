from .models import KitchenSetting, Category


def kitchen_context(request):
    try:
        setting = KitchenSetting.objects.first()
        if not setting:
            setting = KitchenSetting.objects.create()
    except Exception:
        setting = None

    categories = Category.objects.filter(is_active=True).prefetch_related('items')

    cart = request.session.get('thebyte_cart', {})
    total_qty = 0
    subtotal = 0.0
    for key, item in cart.items():
        qty = item.get('quantity', 0)
        price = float(item.get('price', 0))
        total_qty += qty
        subtotal += price * qty

    return {
        'site_setting': setting,
        'nav_categories': categories,
        'cart_count': total_qty,
        'cart_subtotal': subtotal,
    }

import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import (
    KitchenSetting,
    Category,
    MenuItem,
    MenuItemAddon,
    Order,
    OrderItem,
    CustomerReview,
    ContactMessage
)
from .cart import Cart


def get_site_setting():
    setting = KitchenSetting.objects.first()
    if not setting:
        setting = KitchenSetting.objects.create()
    return setting


@ensure_csrf_cookie
def home_view(request):
    setting = get_site_setting()
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    featured_items = MenuItem.objects.filter(is_featured=True, is_available=True)[:8]
    reviews = CustomerReview.objects.filter(is_approved=True)[:6]
    global_addons = MenuItemAddon.objects.filter(item=None, is_available=True)

    cart = Cart(request)
    free_delivery_percent, free_delivery_remaining = cart.get_free_delivery_progress(setting)

    context = {
        'setting': setting,
        'categories': categories,
        'featured_items': featured_items,
        'reviews': reviews,
        'global_addons': global_addons,
        'free_delivery_percent': free_delivery_percent,
        'free_delivery_remaining': free_delivery_remaining,
    }
    return render(request, 'kitchen/home.html', context)


@ensure_csrf_cookie
def menu_view(request):
    setting = get_site_setting()
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    items = MenuItem.objects.filter(is_available=True)

    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()
    diet = request.GET.get('diet')
    frozen = request.GET.get('frozen')

    current_category = None
    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()
        if current_category:
            items = items.filter(category=current_category)

    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))

    if diet == 'veg':
        items = items.filter(is_vegetarian=True)
    elif diet == 'nonveg':
        items = items.filter(is_vegetarian=False)

    if frozen == 'true':
        items = items.filter(is_frozen=True)

    global_addons = MenuItemAddon.objects.filter(item=None, is_available=True)

    context = {
        'setting': setting,
        'categories': categories,
        'items': items,
        'current_category': current_category,
        'selected_category_slug': category_slug,
        'search_query': query,
        'diet_filter': diet,
        'frozen_filter': frozen,
        'global_addons': global_addons,
    }
    return render(request, 'kitchen/menu.html', context)


def item_detail_api(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    addons = list(item.addons.filter(is_available=True).values('id', 'name', 'price'))
    global_addons = list(MenuItemAddon.objects.filter(item=None, is_available=True).values('id', 'name', 'price'))

    data = {
        'id': item.id,
        'name': item.name,
        'category': item.category.name,
        'tagline': item.tagline,
        'description': item.description,
        'price': float(item.price),
        'discount_price': float(item.discount_price) if item.discount_price else None,
        'final_price': float(item.final_price),
        'portion_size': item.portion_size,
        'is_vegetarian': item.is_vegetarian,
        'is_frozen': item.is_frozen,
        'spice_level': item.get_spice_level_display(),
        'image': item.image.url if item.image else (f"/static/{item.static_image}" if item.static_image else ''),
        'addons': addons + global_addons,
    }
    return JsonResponse(data)


@ensure_csrf_cookie
def cart_detail_view(request):
    setting = get_site_setting()
    cart = Cart(request)
    subtotal = cart.get_subtotal()
    delivery_fee = cart.get_delivery_fee(setting)
    total = cart.get_total(setting)
    free_delivery_percent, free_delivery_remaining = cart.get_free_delivery_progress(setting)

    context = {
        'setting': setting,
        'cart': cart,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'free_delivery_percent': free_delivery_percent,
        'free_delivery_remaining': free_delivery_remaining,
    }
    return render(request, 'kitchen/cart.html', context)


def get_cart_response_data(cart, setting, message=""):
    subtotal = float(cart.get_subtotal())
    delivery_fee = float(cart.get_delivery_fee(setting))
    total = float(cart.get_total(setting))
    count = len(cart)
    percent, remaining = cart.get_free_delivery_progress(setting)
    min_order = float(setting.minimum_order_amount) if setting.minimum_order_amount else 0.0

    return {
        'success': True,
        'message': message,
        'cart_count': count,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'free_delivery_percent': percent,
        'free_delivery_remaining': float(remaining),
        'minimum_order_amount': min_order,
        'can_checkout': subtotal >= min_order if min_order else True,
        'items': cart.get_items_list(),
    }


@require_GET
def cart_items_api(request):
    cart = Cart(request)
    setting = get_site_setting()
    return JsonResponse(get_cart_response_data(cart, setting))


@require_POST
def cart_add_api(request):
    cart = Cart(request)
    setting = get_site_setting()

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
            item_id = payload.get('item_id')
            quantity = payload.get('quantity', 1)
            instructions = payload.get('special_instructions', '')
            addon_ids = payload.get('addon_ids', [])
        else:
            item_id = request.POST.get('item_id')
            quantity = request.POST.get('quantity', 1)
            instructions = request.POST.get('special_instructions', '')
            addon_ids = request.POST.getlist('addon_ids')

        addon_ids = [int(a) for a in addon_ids if str(a).isdigit()]
        success, message = cart.add(item_id, quantity=quantity, special_instructions=instructions, addon_ids=addon_ids)

        if not success:
            return JsonResponse({'success': False, 'message': message}, status=400)

        return JsonResponse(get_cart_response_data(cart, setting, message=message))
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_POST
def cart_update_api(request):
    cart = Cart(request)
    setting = get_site_setting()

    try:
        payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        key = payload.get('key')
        quantity = payload.get('quantity')
        delta = payload.get('delta')

        if not key or (quantity is None and delta is None):
            return JsonResponse({'success': False, 'message': 'Missing key, quantity, or delta'}, status=400)

        if delta is not None:
            cart.update_delta(key, delta)
        else:
            cart.update(key, quantity)

        return JsonResponse(get_cart_response_data(cart, setting))
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_POST
def cart_remove_api(request):
    cart = Cart(request)
    setting = get_site_setting()

    try:
        payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        key = payload.get('key')
        if not key:
            return JsonResponse({'success': False, 'message': 'Missing key'}, status=400)

        cart.remove(key)
        return JsonResponse(get_cart_response_data(cart, setting, message="Item removed from cart."))
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@ensure_csrf_cookie
def checkout_view(request):
    setting = get_site_setting()
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(request, "Your cart is empty! Please choose something delicious to order.")
        return redirect('menu')

    subtotal = cart.get_subtotal()
    if setting.minimum_order_amount and subtotal < setting.minimum_order_amount:
        messages.error(
            request,
            f"Minimum order amount is ৳{setting.minimum_order_amount}. Your current subtotal is ৳{subtotal}."
        )
        return redirect('cart')

    delivery_fee = cart.get_delivery_fee(setting)
    total = cart.get_total(setting)
    delivery_areas = setting.get_delivery_areas_list()

    if request.method == 'POST':
        name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('customer_phone', '').strip()
        email = request.POST.get('customer_email', '').strip()
        address = request.POST.get('delivery_address', '').strip()
        area = request.POST.get('delivery_area', '').strip()
        slot = request.POST.get('delivery_slot', 'Earliest Available (30-45 mins)').strip()
        notes = request.POST.get('customer_notes', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')
        trx_id = request.POST.get('transaction_id', '').strip()

        if not name or not phone or not address or not area:
            messages.error(request, "Please fill in all required delivery details (Name, Phone, Address, and Area).")
            return redirect('checkout')

        payment_status = 'unpaid'
        if payment_method in ['bkash', 'nagad']:
            if trx_id:
                payment_status = 'submitted'
            else:
                messages.warning(request, "Please enter your bKash/Nagad Transaction ID for quick order verification.")

        # Create Order
        order = Order.objects.create(
            customer_name=name,
            customer_phone=phone,
            customer_email=email or None,
            delivery_address=address,
            delivery_area=area,
            delivery_slot=slot,
            customer_notes=notes,
            payment_method=payment_method,
            payment_status=payment_status,
            transaction_id=trx_id,
            order_status='pending',
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount=Decimal('0.00'),
            total=total
        )

        # Create Order Items
        for item_data in cart:
            try:
                menu_item = MenuItem.objects.get(id=item_data['item_id'])
            except MenuItem.DoesNotExist:
                menu_item = None

            addons_str = ", ".join(item_data['addons']) if item_data['addons'] else ""
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=item_data['name'],
                unit_price=item_data['price'],
                quantity=item_data['quantity'],
                subtotal=item_data['total'],
                special_instructions=item_data['special_instructions'],
                addons=addons_str
            )

        # Clear cart
        cart.clear()
        messages.success(request, f"🎉 Order #{order.order_number} placed successfully! The kitchen has received your order.")
        return redirect('order_tracking', order_number=order.order_number)

    context = {
        'setting': setting,
        'cart': cart,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'delivery_areas': delivery_areas,
    }
    return render(request, 'kitchen/checkout.html', context)


@ensure_csrf_cookie
def order_tracking_view(request, order_number=None):
    setting = get_site_setting()
    order = None
    search_num = order_number or request.GET.get('order_number', '').strip()

    if search_num:
        order = Order.objects.filter(order_number__iexact=search_num).first()
        if not order:
            messages.error(request, f"No order found with number: '{search_num}'. Please check and try again.")

    context = {
        'setting': setting,
        'order': order,
        'search_num': search_num,
    }
    return render(request, 'kitchen/order_tracking.html', context)


def order_status_api(request, order_number):
    order = Order.objects.filter(order_number__iexact=order_number).first()
    if not order:
        return JsonResponse({'found': False}, status=404)

    return JsonResponse({
        'found': True,
        'order_number': order.order_number,
        'order_status': order.order_status,
        'status_display': order.get_order_status_display(),
        'step_index': order.status_step_index,
        'payment_status': order.get_payment_status_display(),
        'updated_at': order.updated_at.strftime('%I:%M %p, %d %b'),
    })


@ensure_csrf_cookie
def kitchen_dashboard_view(request):
    """
    Live Kitchen Display System (KDS) for staff / chef.
    Accessible without complicated hurdles so the owner can manage in real time.
    """
    setting = get_site_setting()
    active_orders = Order.objects.exclude(order_status__in=['delivered', 'cancelled']).order_by('created_at')
    delivered_orders = Order.objects.filter(order_status='delivered').order_by('-updated_at')[:10]
    
    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)
    today_count = today_orders.count()
    today_revenue = today_orders.exclude(order_status='cancelled').aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    pending_prep_count = Order.objects.filter(order_status__in=['pending', 'confirmed', 'preparing']).count()

    context = {
        'setting': setting,
        'active_orders': active_orders,
        'delivered_orders': delivered_orders,
        'today_count': today_count,
        'today_revenue': today_revenue,
        'pending_prep_count': pending_prep_count,
    }
    return render(request, 'kitchen/kitchen_dashboard.html', context)


@require_POST
def kitchen_update_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    try:
        payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        new_status = payload.get('status')
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)

        order.order_status = new_status
        # If marked delivered, update payment if COD
        if new_status == 'delivered' and order.payment_method == 'cod' and order.payment_status == 'unpaid':
            order.payment_status = 'verified'
        order.save()

        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'new_status': order.order_status,
            'status_display': order.get_order_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_POST
def kitchen_toggle_open_api(request):
    setting = get_site_setting()
    setting.is_kitchen_open = not setting.is_kitchen_open
    setting.save()
    return JsonResponse({
        'success': True,
        'is_open': setting.is_kitchen_open,
        'status_text': "Kitchen Open" if setting.is_kitchen_open else "Kitchen Closed"
    })


@require_POST
def contact_submit_view(request):
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    subject = request.POST.get('subject', 'Customer Message').strip()
    message = request.POST.get('message', '').strip()

    if not name or not email or not message:
        messages.error(request, "Please fill in all required fields (Name, Email, Message).")
        return redirect('home')

    ContactMessage.objects.create(
        name=name,
        email=email,
        phone=phone,
        subject=subject,
        message=message
    )
    messages.success(request, "Thank you for contacting The BYTE! We have received your message and will get back to you shortly.")
    return redirect('home')


@require_POST
def review_submit_view(request):
    name = request.POST.get('name', '').strip()
    role = request.POST.get('role', 'Customer').strip()
    rating = request.POST.get('rating', '5')
    comment = request.POST.get('comment', '').strip()

    if not name or not comment:
        messages.error(request, "Please enter your name and review comment.")
        return redirect('home')

    try:
        rating_int = int(rating)
        rating_int = max(1, min(5, rating_int))
    except ValueError:
        rating_int = 5

    CustomerReview.objects.create(
        name=name,
        role=role or 'Customer',
        rating=rating_int,
        comment=comment,
        is_approved=True
    )
    messages.success(request, "⭐ Thank you for your review! Your feedback helps us serve even better.")
    return redirect('home')

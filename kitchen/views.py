import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
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
    ContactMessage,
    CustomerProfile
)
from .cart import Cart
from .forms import (
    CustomerRegistrationForm,
    CustomerLoginForm,
    CustomerProfileUpdateForm,
    MenuItemQuickForm,
    KitchenSettingForm
)


def is_kitchen_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)



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
    if not request.user.is_authenticated:
        messages.info(request, "Please log in or create an account to proceed with your order.")
        return redirect(f"{reverse('customer_login')}?next={reverse('checkout')}")

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
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('customer_phone', '').strip()
        email = request.POST.get('customer_email', '').strip() or request.user.email
        address = request.POST.get('delivery_address', '').strip()
        area = request.POST.get('delivery_area', '').strip()
        slot = request.POST.get('delivery_slot', 'Earliest Available (30-45 mins)').strip()
        notes = request.POST.get('customer_notes', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')
        trx_id = request.POST.get('transaction_id', '').strip()

        if not name or not phone or not address or not area:
            messages.error(request, "Please fill in all required delivery details (Name, Phone, Address, and Area).")
            return redirect('checkout')

        # Auto-update profile default address & phone if empty
        updated_profile = False
        if not profile.phone or profile.phone != phone:
            profile.phone = phone
            updated_profile = True
        if not profile.default_address:
            profile.default_address = address
            updated_profile = True
        if not profile.default_area:
            profile.default_area = area
            updated_profile = True
        if updated_profile:
            profile.save()

        payment_status = 'unpaid'
        if payment_method in ['bkash', 'nagad']:
            if trx_id:
                payment_status = 'submitted'
            else:
                messages.warning(request, "Please enter your bKash/Nagad Transaction ID for quick order verification.")

        # Create Order with user
        order = Order.objects.create(
            user=request.user,
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

    initial_name = request.user.get_full_name() or request.user.username
    initial_phone = profile.phone or ""
    initial_email = request.user.email or ""
    initial_address = profile.default_address or ""
    initial_area = profile.default_area or ""

    context = {
        'setting': setting,
        'cart': cart,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'delivery_areas': delivery_areas,
        'initial_name': initial_name,
        'initial_phone': initial_phone,
        'initial_email': initial_email,
        'initial_address': initial_address,
        'initial_area': initial_area,
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


# ====================================================================
# CUSTOMER AUTHENTICATION & PORTAL
# ====================================================================

@ensure_csrf_cookie
def customer_register_view(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or 'customer_dashboard'
    setting = get_site_setting()

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to The BYTE, {user.first_name or user.username}! Your account has been registered.")
            return redirect(next_url)
    else:
        form = CustomerRegistrationForm()

    return render(request, 'kitchen/customer_register.html', {
        'form': form,
        'setting': setting,
        'next': next_url,
    })


@ensure_csrf_cookie
def customer_login_view(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next') or 'customer_dashboard'
    setting = get_site_setting()

    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect(next_url)
    else:
        form = CustomerLoginForm()

    return render(request, 'kitchen/customer_login.html', {
        'form': form,
        'setting': setting,
        'next': next_url,
    })


def customer_logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out. Come back hungry!")
    return redirect('home')


@login_required(login_url='customer_login')
@ensure_csrf_cookie
def customer_dashboard_view(request):
    setting = get_site_setting()
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        default_area = request.POST.get('default_area', '').strip()
        default_address = request.POST.get('default_address', '').strip()

        request.user.first_name = first_name
        request.user.last_name = last_name
        if email:
            request.user.email = email
        request.user.save()

        profile.phone = phone
        profile.default_area = default_area
        profile.default_address = default_address
        profile.save()

        messages.success(request, "Your account details have been updated successfully.")
        return redirect('customer_dashboard')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    active_orders = orders.exclude(order_status__in=['delivered', 'cancelled'])
    past_orders = orders.filter(order_status__in=['delivered', 'cancelled'])
    delivery_areas = setting.get_delivery_areas_list()

    context = {
        'setting': setting,
        'profile': profile,
        'orders': orders,
        'active_orders': active_orders,
        'past_orders': past_orders,
        'delivery_areas': delivery_areas,
    }
    return render(request, 'kitchen/customer_dashboard.html', context)


@login_required(login_url='customer_login')
def customer_orders_api(request):
    """
    Returns active orders for current user for automatic live status tracking.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    data = []
    for o in orders:
        data.append({
            'order_number': o.order_number,
            'status': o.order_status,
            'status_display': o.get_order_status_display(),
            'total': float(o.total),
            'items_count': o.items.count(),
            'created_at': o.created_at.strftime('%I:%M %p, %d %b %Y'),
            'is_active': o.order_status not in ['delivered', 'cancelled'],
            'step_index': o.status_step_index,
        })
    return JsonResponse({'orders': data})


# ====================================================================
# STAFF & ADMIN CLOUD KITCHEN MANAGEMENT PORTAL
# ====================================================================

@ensure_csrf_cookie
def staff_login_view(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('staff_dashboard')

    setting = get_site_setting()
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            user = form.user
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Logged into Staff Portal as {user.username}")
                return redirect('staff_dashboard')
            else:
                messages.error(request, "Access denied. Only kitchen staff and administrators can access this portal.")
    else:
        form = CustomerLoginForm()

    return render(request, 'kitchen/staff_login.html', {'form': form, 'setting': setting})


@user_passes_test(is_kitchen_staff, login_url='/staff/login/')
@ensure_csrf_cookie
def staff_dashboard_view(request):
    setting = get_site_setting()
    active_orders = Order.objects.exclude(order_status__in=['delivered', 'cancelled']).order_by('created_at')
    delivered_orders = Order.objects.filter(order_status='delivered').order_by('-updated_at')[:15]
    all_recent_orders = Order.objects.all().order_by('-created_at')[:30]

    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)
    today_count = today_orders.count()
    today_revenue = today_orders.exclude(order_status='cancelled').aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
    pending_prep_count = Order.objects.filter(order_status__in=['pending', 'confirmed', 'preparing']).count()
    ready_count = Order.objects.filter(order_status='ready').count()
    out_for_delivery_count = Order.objects.filter(order_status='out_for_delivery').count()

    categories = Category.objects.all().prefetch_related('items')
    menu_items = MenuItem.objects.all().select_related('category').order_by('category', 'order', 'name')
    settings_form = KitchenSettingForm(instance=setting)
    item_form = MenuItemQuickForm()

    context = {
        'setting': setting,
        'active_orders': active_orders,
        'delivered_orders': delivered_orders,
        'all_recent_orders': all_recent_orders,
        'today_count': today_count,
        'today_revenue': today_revenue,
        'pending_prep_count': pending_prep_count,
        'ready_count': ready_count,
        'out_for_delivery_count': out_for_delivery_count,
        'categories': categories,
        'menu_items': menu_items,
        'settings_form': settings_form,
        'item_form': item_form,
    }
    return render(request, 'kitchen/staff_dashboard.html', context)


@user_passes_test(is_kitchen_staff)
def staff_orders_api(request):
    """
    Live stream API for staff portal to get orders and notify of newly placed orders.
    """
    active_orders = Order.objects.exclude(order_status__in=['delivered', 'cancelled']).order_by('created_at')
    orders_data = []
    for order in active_orders:
        items = [{
            'name': i.item_name,
            'qty': i.quantity,
            'subtotal': float(i.subtotal),
            'special_instructions': i.special_instructions,
            'addons': i.addons
        } for i in order.items.all()]

        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'delivery_address': order.delivery_address,
            'delivery_area': order.delivery_area,
            'delivery_slot': order.delivery_slot,
            'customer_notes': order.customer_notes,
            'payment_method': order.get_payment_method_display(),
            'payment_status': order.payment_status,
            'payment_status_display': order.get_payment_status_display(),
            'transaction_id': order.transaction_id or '',
            'order_status': order.order_status,
            'status_display': order.get_order_status_display(),
            'subtotal': float(order.subtotal),
            'delivery_fee': float(order.delivery_fee),
            'total': float(order.total),
            'created_at_time': order.created_at.strftime('%I:%M %p'),
            'created_at_timestamp': order.created_at.timestamp(),
            'items': items,
        })

    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)
    today_revenue = today_orders.exclude(order_status='cancelled').aggregate(Sum('total'))['total__sum'] or Decimal('0.00')

    return JsonResponse({
        'success': True,
        'orders': orders_data,
        'active_count': len(orders_data),
        'today_count': today_orders.count(),
        'today_revenue': float(today_revenue),
    })


@user_passes_test(is_kitchen_staff)
@require_POST
def staff_update_payment_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    try:
        payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        new_status = payload.get('payment_status')
        valid_statuses = [choice[0] for choice in Order.PAYMENT_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid payment status'}, status=400)

        order.payment_status = new_status
        order.save()
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'new_payment_status': order.payment_status,
            'payment_status_display': order.get_payment_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@user_passes_test(is_kitchen_staff)
@require_POST
def staff_toggle_item_api(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.is_available = not item.is_available
    item.save()
    return JsonResponse({
        'success': True,
        'item_id': item.id,
        'name': item.name,
        'is_available': item.is_available,
        'status_text': "In Stock" if item.is_available else "Sold Out"
    })


@user_passes_test(is_kitchen_staff)
@require_POST
def staff_update_item_api(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    try:
        payload = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        price = payload.get('price')
        discount_price = payload.get('discount_price')
        is_available = payload.get('is_available')

        if price is not None:
            item.price = Decimal(str(price))
        if discount_price is not None:
            if str(discount_price).strip() in ['', 'null', '0']:
                item.discount_price = None
            else:
                item.discount_price = Decimal(str(discount_price))
        if is_available is not None:
            item.is_available = bool(is_available)

        item.save()
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'name': item.name,
            'price': float(item.price),
            'discount_price': float(item.discount_price) if item.discount_price else None,
            'is_available': item.is_available
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@user_passes_test(is_kitchen_staff)
@require_POST
def staff_create_item_view(request):
    form = MenuItemQuickForm(request.POST)
    if form.is_valid():
        item = form.save()
        messages.success(request, f"New menu item '{item.name}' added successfully!")
    else:
        messages.error(request, "Failed to create item. Please check the form data.")
    return redirect('staff_dashboard')


@user_passes_test(is_kitchen_staff)
@require_POST
def staff_update_settings_view(request):
    setting = get_site_setting()
    form = KitchenSettingForm(request.POST, instance=setting)
    if form.is_valid():
        form.save()
        messages.success(request, "Kitchen operations settings updated successfully!")
    else:
        messages.error(request, "Error saving settings. Please check values.")
    return redirect('staff_dashboard')


@user_passes_test(is_kitchen_staff)
def staff_kot_view(request, order_number):
    setting = get_site_setting()
    order = get_object_or_404(Order, order_number__iexact=order_number)
    return render(request, 'kitchen/print_kot.html', {
        'setting': setting,
        'order': order,
    })


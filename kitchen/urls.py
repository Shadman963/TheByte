from django.urls import path
from . import views

urlpatterns = [
    # Public & Menu
    path('', views.home_view, name='home'),
    path('menu/', views.menu_view, name='menu'),
    path('api/item/<int:item_id>/', views.item_detail_api, name='item_detail_api'),

    # Live Cart
    path('cart/', views.cart_detail_view, name='cart'),
    path('api/cart/items/', views.cart_items_api, name='cart_items_api'),
    path('api/cart/add/', views.cart_add_api, name='cart_add_api'),
    path('api/cart/update/', views.cart_update_api, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),

    # Mandatory Customer Auth & Account Portal
    path('customer/register/', views.customer_register_view, name='customer_register'),
    path('register/', views.customer_register_view, name='register_alias'),
    path('customer/login/', views.customer_login_view, name='customer_login'),
    path('login/', views.customer_login_view, name='login_alias'),
    path('customer/logout/', views.customer_logout_view, name='customer_logout'),
    path('logout/', views.customer_logout_view, name='logout_alias'),
    path('customer/dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    path('account/', views.customer_dashboard_view, name='account_alias'),
    path('api/customer/orders/', views.customer_orders_api, name='customer_orders_api'),

    # Checkout & Live Order Tracking
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/track/', views.order_tracking_view, name='order_tracking_search'),
    path('order/track/<str:order_number>/', views.order_tracking_view, name='order_tracking'),
    path('api/order/<str:order_number>/status/', views.order_status_api, name='order_status_api'),

    # Kitchen KDS (Direct)
    path('kitchen/dashboard/', views.kitchen_dashboard_view, name='kitchen_dashboard'),
    path('api/kitchen/order/<int:order_id>/update-status/', views.kitchen_update_status_api, name='kitchen_update_status_api'),
    path('api/kitchen/toggle-open/', views.kitchen_toggle_open_api, name='kitchen_toggle_open_api'),

    # Staff & Admin Cloud Kitchen Management Portal
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/portal/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/', views.staff_dashboard_view, name='staff_alias'),
    path('kitchen/portal/', views.staff_dashboard_view, name='kitchen_portal'),
    path('api/staff/orders/', views.staff_orders_api, name='staff_orders_api'),
    path('api/staff/order/<int:order_id>/payment-status/', views.staff_update_payment_status_api, name='staff_update_payment_status_api'),
    path('api/staff/item/<int:item_id>/toggle/', views.staff_toggle_item_api, name='staff_toggle_item_api'),
    path('api/staff/item/<int:item_id>/update/', views.staff_update_item_api, name='staff_update_item_api'),
    path('staff/item/create/', views.staff_create_item_view, name='staff_create_item'),
    path('staff/settings/update/', views.staff_update_settings_view, name='staff_update_settings'),
    path('staff/order/<str:order_number>/kot/', views.staff_kot_view, name='staff_kot'),

    # Contact & Review Form Submissions
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),
    path('review/submit/', views.review_submit_view, name='review_submit'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('menu/', views.menu_view, name='menu'),
    path('api/item/<int:item_id>/', views.item_detail_api, name='item_detail_api'),
    path('cart/', views.cart_detail_view, name='cart'),
    path('api/cart/items/', views.cart_items_api, name='cart_items_api'),
    path('api/cart/add/', views.cart_add_api, name='cart_add_api'),
    path('api/cart/update/', views.cart_update_api, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/track/', views.order_tracking_view, name='order_tracking_search'),
    path('order/track/<str:order_number>/', views.order_tracking_view, name='order_tracking'),
    path('api/order/<str:order_number>/status/', views.order_status_api, name='order_status_api'),
    path('kitchen/dashboard/', views.kitchen_dashboard_view, name='kitchen_dashboard'),
    path('api/kitchen/order/<int:order_id>/update-status/', views.kitchen_update_status_api, name='kitchen_update_status_api'),
    path('api/kitchen/toggle-open/', views.kitchen_toggle_open_api, name='kitchen_toggle_open_api'),
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),
    path('review/submit/', views.review_submit_view, name='review_submit'),
]

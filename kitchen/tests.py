import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import KitchenSetting, Category, MenuItem, Order, OrderItem, CustomerReview, ContactMessage, CustomerProfile
from .cart import Cart


class KitchenTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.setting = KitchenSetting.objects.create(
            restaurant_name="The BYTE",
            tagline="Fresh • Tasty • Budget-Friendly",
            phone="01718-244371",
            email="thebyte39@gmail.com",
            minimum_order_amount=100.00,
            delivery_fee=40.00,
            free_delivery_above=500.00
        )
        self.cat_curry = Category.objects.create(name="Curry", slug="curry", order=1)
        self.cat_rice = Category.objects.create(name="Rice", slug="rice", order=2)

        self.item_chicken = MenuItem.objects.create(
            category=self.cat_curry,
            name="Chicken Curry",
            slug="chicken-curry",
            description="Tender chicken slow-cooked with onions and traditional spices.",
            price=150.00,
            portion_size="2 Pcs with gravy",
            is_available=True,
            is_featured=True,
            spice_level="medium"
        )

        self.item_rice = MenuItem.objects.create(
            category=self.cat_rice,
            name="Plain Rice",
            slug="plain-rice",
            description="Steamed premium rice.",
            price=40.00,
            portion_size="1 Plate",
            is_available=True,
            is_vegetarian=True,
            spice_level="none"
        )

        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer1',
            email='customer1@example.com',
            password='password123',
            first_name='Tanvir',
            last_name='Ahmed'
        )
        self.customer_profile, _ = CustomerProfile.objects.get_or_create(user=self.customer_user)
        self.customer_profile.phone = '01711111111'
        self.customer_profile.default_area = 'Mirpur'
        self.customer_profile.default_address = 'House 10, Road 2, Mirpur'
        self.customer_profile.save()

        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff1',
            email='staff1@thebyte.com',
            password='password123',
            is_staff=True
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The BYTE")
        self.assertContains(response, "Chicken Curry")

    def test_menu_view_filtering(self):
        response = self.client.get(reverse('menu') + '?category=curry')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chicken Curry")
        self.assertNotContains(response, "Plain Rice")

        # Search test
        response_search = self.client.get(reverse('menu') + '?q=chicken')
        self.assertEqual(response_search.status_code, 200)
        self.assertContains(response_search, "Chicken Curry")

    def test_cart_workflow(self):
        payload = {
            'item_id': self.item_chicken.id,
            'quantity': 2,
            'special_instructions': 'Extra gravy',
            'addon_ids': []
        }
        res = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(data['subtotal'], 300.0)

        # View cart page
        res_cart = self.client.get(reverse('cart'))
        self.assertEqual(res_cart.status_code, 200)
        self.assertContains(res_cart, "Chicken Curry")

    def test_mandatory_customer_login_for_checkout(self):
        # 1. Anonymous user trying to access checkout must be redirected to login
        res_anon_get = self.client.get(reverse('checkout'))
        self.assertEqual(res_anon_get.status_code, 302)
        self.assertIn(reverse('customer_login'), res_anon_get.url)

        # 2. Anonymous user trying to post checkout must be redirected to login
        res_anon_post = self.client.post(reverse('checkout'), data={'customer_name': 'Anon'})
        self.assertEqual(res_anon_post.status_code, 302)
        self.assertIn(reverse('customer_login'), res_anon_post.url)

    def test_checkout_and_order_tracking_authenticated(self):
        # Log in as customer
        self.client.login(username='customer1', password='password123')

        # Add item to cart
        self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 1}),
            content_type='application/json'
        )

        checkout_data = {
            'customer_name': 'Tanvir Ahmed',
            'customer_phone': '01711111111',
            'customer_email': 'customer1@example.com',
            'delivery_address': 'House 12, Road 4, Sector 11, Uttara',
            'delivery_area': 'Uttara',
            'delivery_slot': 'Immediate Delivery (25-40 mins)',
            'customer_notes': 'Please ring bell twice',
            'payment_method': 'cod',
            'transaction_id': ''
        }

        res = self.client.post(reverse('checkout'), data=checkout_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify order in DB linked to customer user
        order = Order.objects.filter(customer_name='Tanvir Ahmed').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.user, self.customer_user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().item_name, "Chicken Curry")

        # Test tracking API
        res_track = self.client.get(reverse('order_status_api', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_track.status_code, 200)
        self.assertEqual(res_track.json()['order_status'], 'pending')

    def test_customer_registration_and_portal(self):
        reg_data = {
            'username': 'newcustomer',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'phone': '01722222222',
            'default_area': 'Dhanmondi',
            'default_address': 'Road 27, Dhanmondi',
            'password': 'password12345',
            'confirm_password': 'password12345'
        }
        res = self.client.post(reverse('customer_register'), data=reg_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify user created
        new_user = User.objects.filter(username='newcustomer').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.profile.phone, '01722222222')

        # Test customer dashboard access
        res_dash = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, "Welcome, New")

        # Test customer orders api
        res_api = self.client.get(reverse('customer_orders_api'))
        self.assertEqual(res_api.status_code, 200)
        self.assertIn('orders', res_api.json())

        # Test logout
        res_logout = self.client.get(reverse('customer_logout'))
        self.assertEqual(res_logout.status_code, 302)

    def test_staff_portal_permissions_and_management(self):
        # 1. Non-staff user should be denied / redirected
        self.client.login(username='customer1', password='password123')
        res_denied = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(res_denied.status_code, 302)

        # 2. Staff user login and access
        self.client.login(username='staff1', password='password123')
        res_staff = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(res_staff.status_code, 200)
        self.assertContains(res_staff, "Kitchen Operations & Staff Portal")

        # Create an order
        order = Order.objects.create(
            user=self.customer_user,
            customer_name="Tanvir",
            customer_phone="01711111111",
            delivery_address="Mirpur 10",
            delivery_area="Mirpur",
            subtotal=150.00,
            total=190.00,
            order_status='pending'
        )

        # 3. Staff updates order status
        res_update = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'preparing'}),
            content_type='application/json'
        )
        self.assertEqual(res_update.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'preparing')

        # 4. Staff updates payment status
        res_pay = self.client.post(
            reverse('staff_update_payment_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'payment_status': 'verified'}),
            content_type='application/json'
        )
        self.assertEqual(res_pay.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'verified')

        # 5. Staff toggles item availability
        res_item_toggle = self.client.post(
            reverse('staff_toggle_item_api', kwargs={'item_id': self.item_chicken.id}),
            content_type='application/json'
        )
        self.assertEqual(res_item_toggle.status_code, 200)
        self.item_chicken.refresh_from_db()
        self.assertFalse(self.item_chicken.is_available)

        # 6. Staff prints KOT
        res_kot = self.client.get(reverse('staff_kot', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_kot.status_code, 200)
        self.assertContains(res_kot, f"ORDER #{order.order_number}")

    def test_free_delivery_progress_calculation(self):
        cart_client = Client()
        # Item price 150, free delivery above 500
        # 1 item: subtotal 150 -> 30% progress, remaining 350
        cart_client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 1}),
            content_type='application/json'
        )
        res1 = cart_client.get(reverse('cart_items_api'))
        data1 = res1.json()
        self.assertEqual(data1['free_delivery_percent'], 30)
        self.assertEqual(data1['free_delivery_remaining'], 350.0)
        self.assertEqual(data1['delivery_fee'], 40.0)

        # Add 3 more items: total 4 items -> subtotal 600 -> 100% progress, 0 remaining, 0 delivery fee
        cart_client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 3}),
            content_type='application/json'
        )
        res2 = cart_client.get(reverse('cart_items_api'))
        data2 = res2.json()
        self.assertEqual(data2['free_delivery_percent'], 100)
        self.assertEqual(data2['free_delivery_remaining'], 0.0)
        self.assertEqual(data2['delivery_fee'], 0.0)

    def test_contact_submission(self):
        res = self.client.post(reverse('contact_submit'), data={
            'name': 'Inquirer',
            'email': 'inq@example.com',
            'phone': '01711111111',
            'subject': 'Party Catering',
            'message': 'Need 50 boxes for university event'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(name='Inquirer').exists())

    def test_csrf_cookie_delivered_on_views(self):
        csrf_client = Client(enforce_csrf_checks=True)
        for url_name in ['menu', 'cart', 'kitchen_dashboard', 'customer_login', 'customer_register']:
            res = csrf_client.get(reverse(url_name))
            self.assertEqual(res.status_code, 200)
            self.assertIn('csrftoken', csrf_client.cookies, f"CSRF cookie missing for {url_name}")

    def test_cart_delta_and_safe_keys_with_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get(reverse('menu'))
        csrf_token = csrf_client.cookies['csrftoken'].value

        # Test adding with special characters/quotes in instructions
        payload = {
            'item_id': self.item_chicken.id,
            'quantity': 1,
            'special_instructions': "Don't add extra oil; it's 'very' spicy!",
            'addon_ids': []
        }
        res = csrf_client.post(
            reverse('cart_add_api'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        item_key = data['items'][0]['key']
        # Key must not contain quotes or spaces
        self.assertNotIn("'", item_key)
        self.assertNotIn('"', item_key)
        self.assertNotIn(' ', item_key)

        # Test delta +1
        res_inc = csrf_client.post(
            reverse('cart_update_api'),
            data=json.dumps({'key': item_key, 'delta': 1}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(res_inc.status_code, 200)
        self.assertEqual(res_inc.json()['items'][0]['quantity'], 2)

        # Test delta -1
        res_dec = csrf_client.post(
            reverse('cart_update_api'),
            data=json.dumps({'key': item_key, 'delta': -1}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(res_dec.status_code, 200)
        self.assertEqual(res_dec.json()['items'][0]['quantity'], 1)

        # Test cart_items_api
        res_items = csrf_client.get(reverse('cart_items_api'))
        self.assertEqual(res_items.status_code, 200)
        self.assertEqual(len(res_items.json()['items']), 1)

        # Test remove
        res_rem = csrf_client.post(
            reverse('cart_remove_api'),
            data=json.dumps({'key': item_key}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(res_rem.status_code, 200)
        self.assertEqual(res_rem.json()['cart_count'], 0)

    def test_kitchen_toggle_open_with_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.get(reverse('kitchen_dashboard'))
        csrf_token = csrf_client.cookies['csrftoken'].value

        initial_state = self.setting.is_kitchen_open
        res = csrf_client.post(
            reverse('kitchen_toggle_open_api'),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['is_open'], not initial_state)

    def test_cart_invalid_quantity_rejected(self):
        # 1. Negative quantity
        res_neg = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': -5}),
            content_type='application/json'
        )
        self.assertEqual(res_neg.status_code, 400)
        self.assertFalse(res_neg.json()['success'])

        # 2. Zero quantity
        res_zero = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 0}),
            content_type='application/json'
        )
        self.assertEqual(res_zero.status_code, 400)

        # 3. Excessive quantity (> 50)
        res_excess = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 500}),
            content_type='application/json'
        )
        self.assertEqual(res_excess.status_code, 400)

        # 4. Non-numeric quantity
        res_str = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 'abc'}),
            content_type='application/json'
        )
        self.assertEqual(res_str.status_code, 400)

    def test_cart_unavailable_product_rejected(self):
        unavailable_item = MenuItem.objects.create(
            category=self.cat_curry,
            name="Beef Bhuna (Sold Out)",
            slug="beef-bhuna-sold-out",
            description="Sold out item test",
            price=200.00,
            is_available=False
        )
        res = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': unavailable_item.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()['success'])

    def test_cart_form_fallback_non_ajax(self):
        form_client = Client()
        # 1. Standard HTML form submit to add to cart
        res_add = form_client.post(reverse('cart_add_api'), data={
            'item_id': self.item_chicken.id,
            'quantity': 1
        })
        self.assertEqual(res_add.status_code, 302)

        # Cart should now contain the item
        res_cart = form_client.get(reverse('cart'))
        self.assertEqual(res_cart.status_code, 200)
        self.assertContains(res_cart, "Chicken Curry")

    def test_checkout_unavailable_item_and_price_recalculation(self):
        self.client.login(username='customer1', password='password123')

        # Add available item
        self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 1}),
            content_type='application/json'
        )

        # Now simulate item being marked sold out before checkout
        self.item_chicken.is_available = False
        self.item_chicken.save()

        checkout_data = {
            'customer_name': 'Tanvir Ahmed',
            'customer_phone': '01711111111',
            'customer_email': 'customer1@example.com',
            'delivery_address': 'House 12, Road 4, Sector 11, Uttara',
            'delivery_area': 'Uttara',
            'payment_method': 'cod'
        }
        res_fail = self.client.post(reverse('checkout'), data=checkout_data)
        self.assertEqual(res_fail.status_code, 302)
        self.assertIn(reverse('cart'), res_fail.url)

        # Restore availability and test server price calculation
        self.item_chicken.is_available = True
        self.item_chicken.price = 180.00
        self.item_chicken.save()

        # Checkout should reflect DB price 180, not old price
        res_ok = self.client.post(reverse('checkout'), data=checkout_data, follow=True)
        self.assertEqual(res_ok.status_code, 200)
        created_order = Order.objects.filter(customer_name='Tanvir Ahmed').first()
        self.assertIsNotNone(created_order)
        self.assertEqual(created_order.subtotal, Decimal('180.00'))

    def test_checkout_duplicate_submission_protection(self):
        self.client.login(username='customer1', password='password123')
        self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 1}),
            content_type='application/json'
        )

        checkout_data = {
            'customer_name': 'Tanvir Duplicate Test',
            'customer_phone': '01799999999',
            'delivery_address': 'House 5, Mirpur',
            'delivery_area': 'Mirpur',
            'payment_method': 'cod'
        }
        # First submission
        res1 = self.client.post(reverse('checkout'), data=checkout_data)
        self.assertEqual(res1.status_code, 302)
        initial_order_count = Order.objects.filter(customer_name='Tanvir Duplicate Test').count()
        self.assertEqual(initial_order_count, 1)

        # Immediate rapid second submission (same details within 10 seconds)
        res2 = self.client.post(reverse('checkout'), data=checkout_data)
        self.assertEqual(res2.status_code, 302)
        second_order_count = Order.objects.filter(customer_name='Tanvir Duplicate Test').count()
        # Must not create a duplicate order
        self.assertEqual(second_order_count, 1)

    def test_order_tracking_ownership_and_unauthorized_access(self):
        # Create user 2
        user2 = User.objects.create_user(
            username='customer2',
            password='password123'
        )

        # Order belongs to customer1
        order = Order.objects.create(
            user=self.customer_user,
            customer_name="Tanvir",
            customer_phone="01711111111",
            delivery_address="Mirpur 10",
            delivery_area="Mirpur",
            subtotal=150.00,
            total=190.00,
            order_status='pending'
        )

        # 1. Customer 2 tries to access customer 1's order status API -> 403 Forbidden
        self.client.login(username='customer2', password='password123')
        res_api_denied = self.client.get(reverse('order_status_api', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_api_denied.status_code, 403)

        # 2. Customer 2 tries to access customer 1's tracking page -> redirected
        res_page_denied = self.client.get(reverse('order_tracking', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_page_denied.status_code, 302)

        # 3. Customer 1 (owner) accesses own order -> 200 OK
        self.client.login(username='customer1', password='password123')
        res_api_allowed = self.client.get(reverse('order_status_api', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_api_allowed.status_code, 200)

        # 4. Staff user accesses customer 1's order -> 200 OK
        self.client.login(username='staff1', password='password123')
        res_staff_allowed = self.client.get(reverse('order_status_api', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_staff_allowed.status_code, 200)

    def test_kitchen_status_staff_only_permission(self):
        order = Order.objects.create(
            user=self.customer_user,
            customer_name="Tanvir",
            customer_phone="01711111111",
            delivery_address="Mirpur 10",
            delivery_area="Mirpur",
            subtotal=150.00,
            total=190.00,
            order_status='pending'
        )

        # 1. Anonymous user cannot update status
        anon_client = Client()
        res_anon = anon_client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json'
        )
        self.assertEqual(res_anon.status_code, 403)

        # 2. Regular customer cannot update status
        self.client.login(username='customer1', password='password123')
        res_cust = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json'
        )
        self.assertEqual(res_cust.status_code, 403)

        # 3. Staff user can update status
        self.client.login(username='staff1', password='password123')
        res_staff = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json'
        )
        self.assertEqual(res_staff.status_code, 200)

    def test_kitchen_status_transition_rules(self):
        self.client.login(username='staff1', password='password123')

        order = Order.objects.create(
            user=self.customer_user,
            customer_name="Tanvir",
            customer_phone="01711111111",
            delivery_address="Mirpur 10",
            delivery_area="Mirpur",
            subtotal=150.00,
            total=190.00,
            order_status='pending'
        )

        # Invalid jump: pending -> delivered (not allowed)
        res_invalid = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'delivered'}),
            content_type='application/json'
        )
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("Cannot transition", res_invalid.json()['message'])

        # Valid transitions sequence: pending -> confirmed -> preparing -> ready -> out_for_delivery -> delivered
        transitions = ['confirmed', 'preparing', 'ready', 'out_for_delivery', 'delivered']
        for target_status in transitions:
            res_step = self.client.post(
                reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
                data=json.dumps({'status': target_status}),
                content_type='application/json'
            )
            self.assertEqual(res_step.status_code, 200)
            order.refresh_from_db()
            self.assertEqual(order.order_status, target_status)

        # Delivered is terminal state: cannot transition to anything
        res_terminal = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'preparing'}),
            content_type='application/json'
        )
        self.assertEqual(res_terminal.status_code, 400)

    def test_floating_cart_rendering_and_context(self):
        # 1. Test empty cart initial state on home and menu pages
        for url_name in ['home', 'menu']:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['cart_count'], 0)
            self.assertEqual(response.context['cart_subtotal'], 0.0)
            
            # Assert floating cart elements exist in HTML
            self.assertContains(response, 'id="floating-cart-wrapper"')
            self.assertContains(response, 'id="floating-cart-btn"')
            self.assertContains(response, 'id="floating-cart-badge"')
            self.assertContains(response, 'id="floating-cart-subtotal"')
            self.assertContains(response, 'id="floating-cart-items-text"')
            
            # Assert slide-out drawer and backdrop elements exist
            self.assertContains(response, 'id="cart-drawer"')
            self.assertContains(response, 'id="cart-drawer-backdrop"')
            self.assertContains(response, 'id="cart-drawer-items"')
            self.assertContains(response, 'id="drawer-subtotal"')
            self.assertContains(response, 'id="drawer-checkout-btn"')

    def test_floating_cart_with_items_and_sync(self):
        # 1. Add item to cart
        payload = {
            'item_id': self.item_chicken.id,
            'quantity': 2,
            'special_instructions': 'Hot',
            'addon_ids': []
        }
        res_add = self.client.post(
            reverse('cart_add_api'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res_add.status_code, 200)
        data = res_add.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(data['subtotal'], 300.0)

        # 2. Page render should reflect updated floating cart values and drawer items
        res_menu = self.client.get(reverse('menu'))
        self.assertEqual(res_menu.status_code, 200)
        self.assertEqual(res_menu.context['cart_count'], 2)
        self.assertEqual(res_menu.context['cart_subtotal'], 300.0)
        self.assertEqual(len(res_menu.context['cart_items']), 1)
        self.assertContains(res_menu, '<span>৳</span><span id="floating-cart-subtotal">300.00</span>')
        self.assertContains(res_menu, '2 items')
        self.assertContains(res_menu, 'data-cart-key=')

        # 3. Test cart_items_api contains items for the drawer
        res_items = self.client.get(reverse('cart_items_api'))
        self.assertEqual(res_items.status_code, 200)
        items_data = res_items.json()
        self.assertEqual(len(items_data['items']), 1)
        self.assertEqual(items_data['items'][0]['name'], "Chicken Curry")
        self.assertEqual(items_data['items'][0]['quantity'], 2)
        self.assertEqual(items_data['items'][0]['price'], 150.0)
        self.assertEqual(items_data['items'][0]['total'], 300.0)

        # 4. Update cart item quantity (+1 via delta)
        key = items_data['items'][0]['key']
        res_upd = self.client.post(
            reverse('cart_update_api'),
            data=json.dumps({'key': key, 'delta': 1}),
            content_type='application/json'
        )
        self.assertEqual(res_upd.status_code, 200)
        upd_data = res_upd.json()
        self.assertEqual(upd_data['cart_count'], 3)
        self.assertEqual(upd_data['subtotal'], 450.0)

        # 5. Remove item from cart
        res_rem = self.client.post(
            reverse('cart_remove_api'),
            data=json.dumps({'key': key}),
            content_type='application/json'
        )
        self.assertEqual(res_rem.status_code, 200)
        rem_data = res_rem.json()
        self.assertEqual(rem_data['cart_count'], 0)
        self.assertEqual(rem_data['subtotal'], 0.0)

    def test_hero_cta_and_tracking_widget_removed_on_home(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<!-- CTA Action Buttons -->')
        self.assertNotContains(response, '<!-- LIVE ORDER TRACKING QUICK LOOKUP WIDGET -->')
        self.assertNotContains(response, 'Enter Order Number (e.g. BYTE-82194)')


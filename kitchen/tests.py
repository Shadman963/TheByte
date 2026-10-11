import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import KitchenSetting, Category, MenuItem, Order, OrderItem, CustomerReview, ContactMessage


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
        # 1. Add to cart
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

        # 2. View cart page
        res_cart = self.client.get(reverse('cart'))
        self.assertEqual(res_cart.status_code, 200)
        self.assertContains(res_cart, "Chicken Curry")

    def test_checkout_and_order_tracking(self):
        # Add item to cart first
        self.client.post(
            reverse('cart_add_api'),
            data=json.dumps({'item_id': self.item_chicken.id, 'quantity': 1}),
            content_type='application/json'
        )

        checkout_data = {
            'customer_name': 'Sadman Kabir',
            'customer_phone': '01718244371',
            'customer_email': 'sadman@example.com',
            'delivery_address': 'House 12, Road 4, Sector 11, Uttara',
            'delivery_area': 'Uttara',
            'delivery_slot': 'Immediate Delivery (25-40 mins)',
            'customer_notes': 'Please ring bell twice',
            'payment_method': 'cod',
            'transaction_id': ''
        }

        res = self.client.post(reverse('checkout'), data=checkout_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify order in DB
        order = Order.objects.filter(customer_name='Sadman Kabir').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().item_name, "Chicken Curry")

        # Test tracking API
        res_track = self.client.get(reverse('order_status_api', kwargs={'order_number': order.order_number}))
        self.assertEqual(res_track.status_code, 200)
        self.assertEqual(res_track.json()['order_status'], 'pending')

    def test_kitchen_kds_update(self):
        order = Order.objects.create(
            customer_name="Test Chef",
            customer_phone="01700000000",
            delivery_address="Test Kitchen",
            delivery_area="Mirpur",
            subtotal=150.00,
            total=190.00,
            order_status='pending'
        )

        # Update order status to 'preparing'
        res = self.client.post(
            reverse('kitchen_update_status_api', kwargs={'order_id': order.id}),
            data=json.dumps({'status': 'preparing'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'preparing')

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

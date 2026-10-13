import os
from django.core.management.base import BaseCommand
from kitchen.models import KitchenSetting, Category, MenuItem, MenuItemAddon, CustomerReview, Order, OrderItem


class Command(BaseCommand):
    help = 'Seeds initial data for The Byte cloud kitchen matching Canva reference'

    def handle(self, *args, **options):
        self.stdout.write("Seeding The Byte Cloud Kitchen data...")

        # 1. Kitchen Setting
        setting, _ = KitchenSetting.objects.get_or_create(id=1)
        setting.restaurant_name = "The BYTE"
        setting.tagline = "Fresh • Tasty • Budget-Friendly"
        setting.mission_statement = (
            "We don’t just cook food—we cook with responsibility. "
            "Freshly prepared meals, honest portions, and flavors you’ll come back for."
        )
        setting.story = (
            "The BYTE was born from a passion for cooking and the dream of creating our own restaurant. "
            "With professional training and a clear purpose, we started this to serve healthy, tasty, and "
            "budget-friendly meals for students, office workers, and daily hustlers. Every meal is freshly cooked each day, "
            "carefully portioned, and made with care—because good food should always be reliable and satisfying."
        )
        setting.phone = "01718-244371"
        setting.email = "thebyte39@gmail.com"
        setting.address = "Mirpur DOHS / Central Cloud Kitchen, Dhaka, Bangladesh"
        setting.is_kitchen_open = True
        setting.opening_time = "10:00 AM"
        setting.closing_time = "11:00 PM"
        setting.estimated_delivery_time = "25 - 40 Mins"
        setting.minimum_order_amount = 120.00
        setting.delivery_fee = 40.00
        setting.free_delivery_above = 600.00
        setting.currency_symbol = "৳"
        setting.announcement_banner = "⚡ Freshly cooked daily meals! Get free delivery on orders over ৳600. Hotline: 01718-244371"
        setting.delivery_areas = "Mirpur, Dhanmondi, Gulshan, Banani, Uttara, Mohakhali, Panthapath, Mohammadpur, Lalmatia, Badda, Farmgate"
        setting.facebook_url = "https://facebook.com"
        setting.instagram_url = "https://instagram.com"
        setting.tiktok_url = "https://tiktok.com"
        setting.save()

        # 2. Categories
        cat_data = [
            {
                'name': 'Curry',
                'slug': 'curry',
                'order': 1,
                'description': 'Slow-cooked traditional spiced curries made with premium meats and fresh garden vegetables.',
                'static_banner': 'images/curry_main.jpg'
            },
            {
                'name': 'Rice',
                'slug': 'rice',
                'order': 2,
                'description': 'Steamed premium rice varieties cooked fresh to perfection—light, fluffy, and aromatic.',
                'static_banner': 'images/rice_main.jpg'
            },
            {
                'name': 'Fries & Crispy',
                'slug': 'fries',
                'order': 3,
                'description': 'Golden, crunchy, and spicy sides cooked to order for ultimate crunch and flavor.',
                'static_banner': 'images/fries_main.jpg'
            },
            {
                'name': 'Frozen Items',
                'slug': 'frozen-items',
                'order': 4,
                'description': 'Convenient, pre-portioned, seasoned treats ready to fry at home anytime.',
                'static_banner': 'images/frozen_items.jpg'
            },
            {
                'name': 'Meal Combos',
                'slug': 'meal-combos',
                'order': 5,
                'description': 'Complete, filling, budget-friendly meal boxes designed for students & professionals.',
                'static_banner': 'images/hero_banner.png'
            }
        ]

        categories = {}
        for c in cat_data:
            cat, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'order': c['order'],
                    'description': c['description'],
                    'static_banner': c['static_banner'],
                    'is_active': True
                }
            )
            categories[c['slug']] = cat

        # 3. Menu Items
        items_data = [
            # Rice
            {
                'category': categories['rice'],
                'name': 'Plain Rice',
                'slug': 'plain-rice',
                'tagline': 'Light, fluffy, steamed daily',
                'description': 'Steamed premium rice, cooked fresh to perfection—light, fluffy, and the perfect base for any meal.',
                'price': 40.00,
                'discount_price': None,
                'static_image': 'images/rice_main.jpg',
                'portion_size': '1 Plate (approx 350g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'none',
                'order': 1
            },
            {
                'category': categories['rice'],
                'name': 'Fried Rice',
                'slug': 'fried-rice',
                'tagline': 'Fragrant stir-fry with garden veggies',
                'description': 'Fragrant rice stir-fried with fresh vegetables and light seasoning—simple, flavorful, and perfectly satisfying.',
                'price': 90.00,
                'discount_price': None,
                'static_image': 'images/rice_section_bg.png',
                'portion_size': '1 Plate (approx 380g)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'mild',
                'order': 2
            },
            {
                'category': categories['rice'],
                'name': 'Jira Rice',
                'slug': 'jira-rice',
                'tagline': 'Aromatic cumin-infused basmati style',
                'description': 'Steamed plain rice lightly tossed with cumin seeds and onions—simple, aromatic, and comfortingly flavorful.',
                'price': 70.00,
                'discount_price': None,
                'static_image': 'images/rice_main.jpg',
                'portion_size': '1 Plate (approx 350g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'mild',
                'order': 3
            },

            # Curry
            {
                'category': categories['curry'],
                'name': 'Chicken Curry',
                'slug': 'chicken-curry',
                'tagline': 'Slow-cooked homestyle comfort',
                'description': 'Tender chicken slow-cooked with onions and traditional spices—rich in flavor, comforting, and freshly prepared.',
                'price': 150.00,
                'discount_price': None,
                'static_image': 'images/curry_main.jpg',
                'portion_size': '2 Large Pcs with rich onion gravy',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 1
            },
            {
                'category': categories['curry'],
                'name': 'Beef Curry',
                'slug': 'beef-curry',
                'tagline': 'Deeply savory tender beef',
                'description': 'Juicy beef pieces cooked slowly with onions and selected spices—deeply flavorful, hearty, and freshly made.',
                'price': 220.00,
                'discount_price': None,
                'static_image': 'images/curry_section_bg.png',
                'portion_size': '4-5 Tender Pcs with thick rich gravy',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'hot',
                'order': 2
            },
            {
                'category': categories['curry'],
                'name': 'Vegetable Curry',
                'slug': 'vegetable-curry',
                'tagline': 'Healthy, wholesome seasonal harvest',
                'description': 'Fresh seasonal vegetables cooked with traditional spices into a hearty, flavorful curry.',
                'price': 70.00,
                'discount_price': None,
                'static_image': 'images/curry_main.jpg',
                'portion_size': '1 Bowl (approx 250g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'mild',
                'order': 3
            },

            # Fries & Crispy
            {
                'category': categories['fries'],
                'name': 'Chicken Fry',
                'slug': 'chicken-fry',
                'tagline': 'Spicy crunch on outside, juicy inside',
                'description': 'Crispy and spicy chicken pieces, perfectly fried for a juicy inside and a flavorful kick outside.',
                'price': 130.00,
                'discount_price': None,
                'static_image': 'images/fries_main.jpg',
                'portion_size': '2 Pcs Crispy Chicken',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'hot',
                'order': 1
            },
            {
                'category': categories['fries'],
                'name': 'French Fries',
                'slug': 'french-fries',
                'tagline': 'Classic golden salted crunch',
                'description': 'Golden, crispy potato sticks—perfectly salted and irresistibly crunchy.',
                'price': 80.00,
                'discount_price': None,
                'static_image': 'images/fries_section_bg.jpg',
                'portion_size': 'Large Basket (approx 180g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'none',
                'order': 2
            },
            {
                'category': categories['fries'],
                'name': 'Pakora',
                'slug': 'pakora',
                'tagline': 'Bengali spiced vegetable fritters',
                'description': 'Crispy, golden fritters made with fresh vegetables coated in spiced chickpea batter—perfectly crunchy and flavorful.',
                'price': 60.00,
                'discount_price': None,
                'static_image': 'images/fries_main.jpg',
                'portion_size': '6 Pcs Fresh Fritters',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 3
            },

            # Frozen Items
            {
                'category': categories['frozen-items'],
                'name': 'Spring Rolls (Frozen)',
                'slug': 'spring-rolls-frozen',
                'tagline': 'Ready-to-fry appetizer snack',
                'description': 'Frozen spring rolls, packed with fresh vegetables and spices ready to fry at home for a hot, crispy snack.',
                'price': 180.00,
                'discount_price': None,
                'static_image': 'images/frozen_items.jpg',
                'portion_size': '1 Pack (10 Pieces)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': True,
                'spice_level': 'mild',
                'order': 1
            },
            {
                'category': categories['frozen-items'],
                'name': 'Samosa (Frozen)',
                'slug': 'samosa-frozen',
                'tagline': 'Traditional triangular spiced snack',
                'description': 'Frozen samosas filled with spiced vegetables or meat—ready to fry at home for a hot, crispy treat.',
                'price': 160.00,
                'discount_price': None,
                'static_image': 'images/frozen_items.jpg',
                'portion_size': '1 Pack (10 Pieces)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': False,
                'is_frozen': True,
                'spice_level': 'medium',
                'order': 2
            },
            {
                'category': categories['frozen-items'],
                'name': 'Chicken Fries (Frozen)',
                'slug': 'chicken-fries-frozen',
                'tagline': 'Seasoned chicken fingers ready in 5 mins',
                'description': 'Frozen chicken pieces, marinated and seasoned—ready to fry at home for a crispy, spicy, and juicy meal.',
                'price': 260.00,
                'discount_price': None,
                'static_image': 'images/frozen_items.jpg',
                'portion_size': '1 Pack (12 Pieces)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': True,
                'spice_level': 'hot',
                'order': 3
            },
            {
                'category': categories['frozen-items'],
                'name': 'French Fries (Frozen)',
                'slug': 'french-fries-frozen',
                'tagline': 'Pre-cut restaurant quality potatoes',
                'description': 'Frozen potato sticks, coated and ready to fry at home for golden, crispy, and perfectly seasoned fries.',
                'price': 140.00,
                'discount_price': None,
                'static_image': 'images/frozen_items.jpg',
                'portion_size': '1 Pack (500g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': True,
                'spice_level': 'none',
                'order': 4
            },
            {
                'category': categories['frozen-items'],
                'name': 'Marinated Wings (Frozen)',
                'slug': 'marinated-wings-frozen',
                'tagline': 'Signature secret recipe marinade',
                'description': 'Tender chicken wings soaked in our special house marinade, packed with bold flavor and grilled/fried to juicy perfection.',
                'price': 280.00,
                'discount_price': None,
                'static_image': 'images/frozen_items.jpg',
                'portion_size': '1 Pack (8 Jumbo Wings)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': True,
                'spice_level': 'hot',
                'order': 5
            },

            # Meal Combos
            {
                'category': categories['meal-combos'],
                'name': 'BYTE Student Box (Chicken Curry + Plain Rice)',
                'slug': 'byte-student-box',
                'tagline': 'Our #1 best-selling student & hustler meal',
                'description': 'Our signature tender chicken curry paired with fluffy steamed rice and fresh salad. Honest portions, reliable taste, student-friendly price!',
                'price': 190.00,
                'discount_price': 165.00,
                'static_image': 'images/hero_banner.png',
                'portion_size': '1 Complete Box (Rice + 2pc Chicken + Gravy + Salad)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 1
            },
            {
                'category': categories['meal-combos'],
                'name': 'BYTE Beef Feast Box (Beef Curry + Jira Rice + Pakora)',
                'slug': 'byte-beef-feast-box',
                'tagline': 'Hearty lunch or dinner combo',
                'description': 'Slow-cooked savory beef curry served with fragrant cumin rice and 2 crispy vegetable pakoras.',
                'price': 290.00,
                'discount_price': 260.00,
                'static_image': 'images/curry_section_bg.png',
                'portion_size': '1 Complete Box (Jira Rice + Beef Curry + 2pc Pakora)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'hot',
                'order': 2
            },
            {
                'category': categories['meal-combos'],
                'name': 'BYTE Crispy Snack Box (Chicken Fry + Fries + Dip)',
                'slug': 'byte-crispy-snack-box',
                'tagline': 'Crunchy satisfaction anytime',
                'description': '2 pcs crunchy spiced chicken fry paired with golden crispy french fries and signature dipping sauce.',
                'price': 210.00,
                'discount_price': 185.00,
                'static_image': 'images/fries_main.jpg',
                'portion_size': '2pc Chicken Fry + Fries Basket + Garlic Mayo',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'hot',
                'order': 3
            },
        ]

        for item_info in items_data:
            MenuItem.objects.update_or_create(
                slug=item_info['slug'],
                defaults=item_info
            )

        # 4. Global Addons
        addons_data = [
            {'name': 'Extra Fluffy Plain Rice', 'price': 40.00},
            {'name': 'Extra Savory Curry Gravy', 'price': 30.00},
            {'name': 'Fresh Cucumber & Onion Salad', 'price': 20.00},
            {'name': 'BYTE Signature Garlic Mayo Dip', 'price': 25.00},
            {'name': 'BYTE Naga Fire Dip', 'price': 25.00},
            {'name': 'Extra Fried Green Chilies & Lemon Wedge', 'price': 10.00},
        ]

        for a in addons_data:
            MenuItemAddon.objects.get_or_create(
                name=a['name'],
                item=None,
                defaults={'price': a['price'], 'is_available': True}
            )

        # 5. Reviews
        reviews_data = [
            {
                'name': 'Tanvir Ahmed',
                'role': 'Software Engineer, Gulshan',
                'rating': 5,
                'comment': 'The Byte’s Chicken Curry with Jira Rice is the ultimate comfort lunch during our sprint days. Honest portions, freshly cooked, and delivered hot!'
            },
            {
                'name': 'Ayesha Siddiqua',
                'role': 'University Student (AIUB)',
                'rating': 5,
                'comment': 'Budget-friendly meals with clean restaurant-grade taste. The student box is a lifesaver between classes, and the pakoras are super crunchy.'
            },
            {
                'name': 'Farhana Kabir',
                'role': 'Home Maker, Mirpur DOHS',
                'rating': 5,
                'comment': 'We keep their frozen samosas and marinated wings in our freezer. Ready in 5 minutes when guests arrive and they always ask where we got them!'
            },
            {
                'name': 'Mahinur Rahman',
                'role': 'Banker, Dhanmondi',
                'rating': 5,
                'comment': 'Reliable, responsible cooking. No excess oil, genuine spices, and very polite delivery personnel. Highly recommended for daily orders.'
            }
        ]

        for r in reviews_data:
            CustomerReview.objects.get_or_create(
                name=r['name'],
                defaults={
                    'role': r['role'],
                    'rating': r['rating'],
                    'comment': r['comment'],
                    'is_approved': True
                }
            )

        # 6. Sample Live Orders for Kitchen Display System (KDS)
        sample_order, created = Order.objects.get_or_create(
            order_number='BYTE-82194',
            defaults={
                'customer_name': 'Rahim Chowdhury',
                'customer_phone': '01718-244371',
                'customer_email': 'rahim@example.com',
                'delivery_address': 'House 14, Road 5, Block B, Mirpur 12',
                'delivery_area': 'Mirpur',
                'delivery_slot': 'Immediate Delivery (30-45 mins)',
                'customer_notes': 'Please keep gravy separate if possible, less spicy.',
                'payment_method': 'bkash',
                'payment_status': 'verified',
                'transaction_id': '9K38JF1029',
                'order_status': 'preparing',
                'subtotal': 345.00,
                'delivery_fee': 40.00,
                'discount': 0.00,
                'total': 385.00
            }
        )
        if created:
            chick = MenuItem.objects.get(slug='chicken-curry')
            rice = MenuItem.objects.get(slug='plain-rice')
            OrderItem.objects.create(
                order=sample_order,
                menu_item=chick,
                item_name=chick.name,
                unit_price=chick.final_price,
                quantity=2,
                subtotal=chick.final_price * 2,
                special_instructions='Medium spicy'
            )
            OrderItem.objects.create(
                order=sample_order,
                menu_item=rice,
                item_name=rice.name,
                unit_price=rice.final_price,
                quantity=1,
                subtotal=rice.final_price,
                special_instructions='Hot steamed'
            )

        # 7. Default Admin / Kitchen Staff Superuser
        from django.contrib.auth.models import User
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'thebyte39@gmail.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin1234')
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
            )
            self.stdout.write(self.style.SUCCESS(f"Created default superuser '{admin_username}'."))

        self.stdout.write(self.style.SUCCESS("Successfully seeded The Byte Cloud Kitchen database!"))


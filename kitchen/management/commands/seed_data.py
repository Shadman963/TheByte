import os
from django.core.management.base import BaseCommand
from kitchen.models import KitchenSetting, Category, MenuItem, MenuItemAddon, CustomerReview, Order, OrderItem


class Command(BaseCommand):
    help = 'Seeds initial data for The Byte cloud kitchen matching F:\\Menu items'

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
                'name': 'Fries & Crispy',
                'slug': 'fries',
                'order': 1,
                'description': 'Golden, crunchy, and spicy snacks and wings cooked fresh to order for ultimate crunch and flavor.',
                'static_banner': 'images/menu/chicken_fry.webp'
            },
            {
                'name': 'Frozen Items',
                'slug': 'frozen-items',
                'order': 2,
                'description': 'Convenient, pre-portioned, seasoned treats ready to fry at home anytime.',
                'static_banner': 'images/menu/frozen_wings.jpg'
            },
            {
                'name': 'Meal Combos',
                'slug': 'meal-combos',
                'order': 3,
                'description': 'Complete, filling, budget-friendly snack platters and combos.',
                'static_banner': 'images/menu/combo.webp'
            }
        ]

        active_cat_slugs = [c['slug'] for c in cat_data]
        Category.objects.exclude(slug__in=active_cat_slugs).delete()

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

        # 3. Menu Items (from F:\Menu)
        items_data = [
            # Fries & Crispy
            {
                'category': categories['fries'],
                'name': 'Chicken Fry',
                'slug': 'chicken-fry',
                'tagline': 'Spicy crunch on outside, juicy inside',
                'description': 'Crispy and spicy chicken pieces, perfectly fried for a juicy inside and a flavorful kick outside.',
                'price': 130.00,
                'discount_price': 110.00,
                'static_image': 'images/menu/chicken_fry.webp',
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
                'name': 'Chicken Tender',
                'slug': 'chicken-tender',
                'tagline': 'Golden crispy boneless chicken strips',
                'description': 'Tender, juicy boneless chicken strips coated in a seasoned golden crispy batter, served with dipping sauce.',
                'price': 150.00,
                'discount_price': 135.00,
                'static_image': 'images/menu/chicken_tender.webp',
                'portion_size': '4 Pcs Crispy Tenders',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 2
            },
            {
                'category': categories['fries'],
                'name': 'Crispy Wings',
                'slug': 'crispy-wings',
                'tagline': 'Extra crunchy golden fried chicken wings',
                'description': 'Juicy chicken wings double-coated and fried to a golden, shattering crunch.',
                'price': 160.00,
                'discount_price': 140.00,
                'static_image': 'images/menu/crispy_wings.jpeg',
                'portion_size': '6 Pcs Crispy Wings',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 3
            },
            {
                'category': categories['fries'],
                'name': 'Spicy Wings',
                'slug': 'spicy-wings',
                'tagline': 'Fiery glazed & spiced hot wings',
                'description': 'Crispy chicken wings tossed in our signature fiery spice blend for a bold, mouthwatering kick.',
                'price': 170.00,
                'discount_price': None,
                'static_image': 'images/menu/spicy_wings.jpg',
                'portion_size': '6 Pcs Spicy Wings',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'hot',
                'order': 4
            },
            {
                'category': categories['fries'],
                'name': 'Meatballs',
                'slug': 'meatballs',
                'tagline': 'Savory, juicy spiced meatballs',
                'description': 'Tender, flavorful meatballs seasoned with aromatic herbs and spices, fried to golden perfection.',
                'price': 120.00,
                'discount_price': None,
                'static_image': 'images/menu/meatballs.jpeg',
                'portion_size': '6 Pcs Meatballs',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 5
            },
            {
                'category': categories['fries'],
                'name': 'French Fries',
                'slug': 'french-fries',
                'tagline': 'Classic golden salted crunch',
                'description': 'Golden, crispy potato sticks—perfectly salted and irresistibly crunchy.',
                'price': 80.00,
                'discount_price': None,
                'static_image': 'images/menu/french_fries.jfif',
                'portion_size': '1 Large Basket (approx 180g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'none',
                'order': 6
            },
            {
                'category': categories['fries'],
                'name': 'Samusa',
                'slug': 'samusa',
                'tagline': 'Crisp pastry triangles with savory filling',
                'description': 'Freshly fried golden pastry triangles stuffed with a savory, spiced filling—flaky, crunchy, and delicious.',
                'price': 60.00,
                'discount_price': None,
                'static_image': 'images/menu/samusa.jfif',
                'portion_size': '4 Pcs Fresh Samusa',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 7
            },
            {
                'category': categories['fries'],
                'name': 'Spring Roll',
                'slug': 'spring-roll',
                'tagline': 'Crispy golden rolls with savory filling',
                'description': 'Crunchy golden rolls packed with seasoned vegetables and savory filling, fried fresh to order.',
                'price': 80.00,
                'discount_price': None,
                'static_image': 'images/menu/spring_roll.avif',
                'portion_size': '4 Pcs Fresh Spring Rolls',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': False,
                'spice_level': 'mild',
                'order': 8
            },

            # Frozen Items
            {
                'category': categories['frozen-items'],
                'name': 'Frozen French Fries',
                'slug': 'frozen-french-fries',
                'tagline': 'Pre-cut restaurant quality potatoes',
                'description': 'Frozen potato sticks, coated and ready to fry at home for golden, crispy, and perfectly seasoned fries.',
                'price': 140.00,
                'discount_price': None,
                'static_image': 'images/menu/frozen_french_fries.avif',
                'portion_size': '1 Pack (500g)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': True,
                'spice_level': 'none',
                'order': 1
            },
            {
                'category': categories['frozen-items'],
                'name': 'Frozen Meatballs',
                'slug': 'frozen-meatballs',
                'tagline': 'Ready-to-cook seasoned meatballs',
                'description': 'Pre-seasoned, tender frozen meatballs ready to fry or pan-sear at home in minutes.',
                'price': 220.00,
                'discount_price': None,
                'static_image': 'images/menu/frozen_meatballs.png',
                'portion_size': '1 Pack (15 Pieces)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': True,
                'spice_level': 'medium',
                'order': 2
            },
            {
                'category': categories['frozen-items'],
                'name': 'Frozen Samosa',
                'slug': 'frozen-samosa',
                'tagline': 'Traditional triangular spiced snack',
                'description': 'Frozen samosas filled with spiced savory filling—ready to fry at home for a hot, crispy treat.',
                'price': 160.00,
                'discount_price': None,
                'static_image': 'images/menu/frozen_samosa.webp',
                'portion_size': '1 Pack (10 Pieces)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': False,
                'is_frozen': True,
                'spice_level': 'medium',
                'order': 3
            },
            {
                'category': categories['frozen-items'],
                'name': 'Frozen Spring Roll',
                'slug': 'frozen-spring-roll',
                'tagline': 'Ready-to-fry appetizer snack',
                'description': 'Frozen spring rolls, packed with fresh vegetables and spices ready to fry at home for a hot, crispy snack.',
                'price': 180.00,
                'discount_price': None,
                'static_image': 'images/menu/frozen_spring_roll.jfif',
                'portion_size': '1 Pack (10 Pieces)',
                'is_available': True,
                'is_featured': False,
                'is_vegetarian': True,
                'is_frozen': True,
                'spice_level': 'mild',
                'order': 4
            },
            {
                'category': categories['frozen-items'],
                'name': 'Frozen Wings',
                'slug': 'frozen-wings',
                'tagline': 'Signature secret recipe marinated wings',
                'description': 'Tender chicken wings soaked in our special house marinade, frozen and ready to fry or bake to juicy perfection.',
                'price': 280.00,
                'discount_price': 250.00,
                'static_image': 'images/menu/frozen_wings.jpg',
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
                'name': 'Combo',
                'slug': 'combo',
                'tagline': 'Ultimate crispy snack platter with dips',
                'description': 'Assorted crispy snack platter featuring golden samosas, crunchy spring rolls, crispy bites, and signature dipping sauces.',
                'price': 220.00,
                'discount_price': 190.00,
                'static_image': 'images/menu/combo.webp',
                'portion_size': '1 Full Platter (Samosa + Spring Roll + Crispy Bites + Dips)',
                'is_available': True,
                'is_featured': True,
                'is_vegetarian': False,
                'is_frozen': False,
                'spice_level': 'medium',
                'order': 1
            },
        ]

        active_item_slugs = [item['slug'] for item in items_data]
        MenuItem.objects.exclude(slug__in=active_item_slugs).delete()

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
                'comment': 'The Byte’s Chicken Fry and Spicy Wings are the ultimate comfort snack during our sprint days. Honest portions, freshly fried, and delivered hot!'
            },
            {
                'name': 'Ayesha Siddiqua',
                'role': 'University Student (AIUB)',
                'rating': 5,
                'comment': 'Budget-friendly snacks with clean restaurant-grade taste. The Combo platter is a lifesaver between classes, and the samusas are super crunchy.'
            },
            {
                'name': 'Farhana Kabir',
                'role': 'Home Maker, Mirpur DOHS',
                'rating': 5,
                'comment': 'We keep their frozen samosas and frozen wings in our freezer. Ready in 5 minutes when guests arrive and they always ask where we got them!'
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
                'customer_notes': 'Please keep sauce separate if possible, less spicy.',
                'payment_method': 'bkash',
                'payment_status': 'verified',
                'transaction_id': '9K38JF1029',
                'order_status': 'preparing',
                'subtotal': 340.00,
                'delivery_fee': 40.00,
                'discount': 0.00,
                'total': 380.00
            }
        )
        if created:
            chick = MenuItem.objects.get(slug='chicken-fry')
            fries = MenuItem.objects.get(slug='french-fries')
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
                menu_item=fries,
                item_name=fries.name,
                unit_price=fries.final_price,
                quantity=1,
                subtotal=fries.final_price,
                special_instructions='Extra crispy'
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

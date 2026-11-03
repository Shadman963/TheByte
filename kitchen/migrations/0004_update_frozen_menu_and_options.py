from django.db import migrations
from django.db.models import Q


def update_frozen_menu_and_options(apps, schema_editor):
    Category = apps.get_model('kitchen', 'Category')
    MenuItem = apps.get_model('kitchen', 'MenuItem')

    fries_cat = Category.objects.filter(slug='fries').first()
    frozen_cat = Category.objects.filter(slug='frozen-items').first()

    # 1. Update Live Items (Fries & Crispy)
    if fries_cat:
        # Remove separate spicy-wings if consolidating into chicken-wings
        MenuItem.objects.filter(slug='spicy-wings').delete()

        # Rename chicken-tender -> chicken-strips if present
        tender = MenuItem.objects.filter(slug='chicken-tender').first()
        if tender and not MenuItem.objects.filter(slug='chicken-strips').exists():
            tender.slug = 'chicken-strips'
            tender.name = 'Chicken Strips'
            tender.save()
        elif tender:
            tender.delete()

        # Rename crispy-wings -> chicken-wings if present
        c_wings = MenuItem.objects.filter(slug='crispy-wings').first()
        if c_wings and not MenuItem.objects.filter(slug='chicken-wings').exists():
            c_wings.slug = 'chicken-wings'
            c_wings.name = 'Chicken Wings'
            c_wings.save()
        elif c_wings:
            c_wings.delete()

        live_updates = [
            {
                'slug': 'chicken-fry',
                'defaults': {
                    'category': fries_cat,
                    'name': 'Chicken Fry',
                    'tagline': 'Available in Spicy & Crispy options',
                    'description': 'Crispy and spicy chicken pieces, perfectly fried for a juicy inside and a flavorful kick outside. Choose your preferred style: Spicy or Crispy.',
                    'price': 130.00,
                    'discount_price': 110.00,
                    'static_image': 'images/menu/chicken_fry.webp',
                    'portion_size': '2 Pcs Chicken Fry',
                    'is_available': True,
                    'is_featured': True,
                    'is_vegetarian': False,
                    'is_frozen': False,
                    'spice_level': 'hot',
                    'order': 1,
                },
            },
            {
                'slug': 'chicken-strips',
                'defaults': {
                    'category': fries_cat,
                    'name': 'Chicken Strips',
                    'tagline': 'Golden boneless chicken strips (Spicy / Crispy)',
                    'description': 'Tender, juicy boneless chicken strips coated in a seasoned golden batter, served with dipping sauce. Available in Spicy or Crispy style.',
                    'price': 150.00,
                    'discount_price': 135.00,
                    'static_image': 'images/menu/chicken_tender.webp',
                    'portion_size': '4 Pcs Chicken Strips',
                    'is_available': True,
                    'is_featured': True,
                    'is_vegetarian': False,
                    'is_frozen': False,
                    'spice_level': 'medium',
                    'order': 2,
                },
            },
            {
                'slug': 'chicken-wings',
                'defaults': {
                    'category': fries_cat,
                    'name': 'Chicken Wings',
                    'tagline': 'Juicy fried chicken wings (Spicy / Crispy)',
                    'description': 'Juicy chicken wings fried to perfection—choose between our fiery Spicy blend or golden shattering Crispy coating.',
                    'price': 160.00,
                    'discount_price': 140.00,
                    'static_image': 'images/menu/crispy_wings.jpeg',
                    'portion_size': '6 Pcs Chicken Wings',
                    'is_available': True,
                    'is_featured': True,
                    'is_vegetarian': False,
                    'is_frozen': False,
                    'spice_level': 'medium',
                    'order': 3,
                },
            },
            {
                'slug': 'spring-roll',
                'defaults': {
                    'category': fries_cat,
                    'name': 'Spring Roll',
                    'tagline': 'Crispy golden rolls with savory chicken filling',
                    'description': 'Crunchy golden rolls packed with seasoned chicken and savory filling, fried fresh to order.',
                    'price': 80.00,
                    'discount_price': None,
                    'static_image': 'images/menu/spring_roll.avif',
                    'portion_size': '4 Pcs Fresh Spring Rolls',
                    'is_available': True,
                    'is_featured': False,
                    'is_vegetarian': False,
                    'is_frozen': False,
                    'spice_level': 'mild',
                    'order': 7,
                },
            },
        ]
        for lu in live_updates:
            MenuItem.objects.update_or_create(slug=lu['slug'], defaults=lu['defaults'])

    # 2. Update Frozen Items (remove "Frozen" from names, order: Chicken Fry, French Fries, Chicken Strips, ...)
    if frozen_cat:
        frozen_updates = [
            {
                'slug': 'frozen-chicken-fry',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Chicken Fry',
                    'tagline': 'Marinated chicken pieces ready to fry (Spicy / Crispy)',
                    'description': 'Pre-marinated tender chicken pieces coated in our signature blend, frozen and ready to fry at home for crispy, juicy chicken anytime.',
                    'price': 260.00,
                    'discount_price': 230.00,
                    'static_image': 'images/menu/frozen_chicken_fry.jpg',
                    'portion_size': '1 Pack (6 Pieces)',
                    'is_available': True,
                    'is_featured': True,
                    'is_vegetarian': False,
                    'is_frozen': True,
                    'spice_level': 'hot',
                    'order': 1,
                },
            },
            {
                'slug': 'frozen-french-fries',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'French Fries',
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
                    'order': 2,
                },
            },
            {
                'slug': 'frozen-chicken-strips',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Chicken Strips',
                    'tagline': 'Seasoned boneless chicken strips ready to cook (Spicy / Crispy)',
                    'description': 'Marinated boneless chicken breast strips seasoned with herbs and spices, frozen and ready to bread, pan-sear, or fry at home in minutes.',
                    'price': 250.00,
                    'discount_price': 220.00,
                    'static_image': 'images/menu/frozen_chicken_strips.jpg',
                    'portion_size': '1 Pack (10 Strips)',
                    'is_available': True,
                    'is_featured': True,
                    'is_vegetarian': False,
                    'is_frozen': True,
                    'spice_level': 'medium',
                    'order': 3,
                },
            },
            {
                'slug': 'frozen-wings',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Chicken Wings',
                    'tagline': 'Signature secret recipe marinated wings (Spicy / Crispy)',
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
                    'order': 4,
                },
            },
            {
                'slug': 'frozen-meatballs',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Meatballs',
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
                    'order': 5,
                },
            },
            {
                'slug': 'frozen-samosa',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Samosa',
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
                    'order': 6,
                },
            },
            {
                'slug': 'frozen-spring-roll',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Spring Roll',
                    'tagline': 'Ready-to-fry non-veg appetizer snack',
                    'description': 'Frozen spring rolls, packed with seasoned chicken and spices ready to fry at home for a hot, crispy snack.',
                    'price': 180.00,
                    'discount_price': None,
                    'static_image': 'images/menu/frozen_spring_roll.jfif',
                    'portion_size': '1 Pack (10 Pieces)',
                    'is_available': True,
                    'is_featured': False,
                    'is_vegetarian': False,
                    'is_frozen': True,
                    'spice_level': 'mild',
                    'order': 7,
                },
            },
        ]
        for fu in frozen_updates:
            MenuItem.objects.update_or_create(slug=fu['slug'], defaults=fu['defaults'])

        # Also strip "Frozen " prefix from any other items in the frozen category
        for item in MenuItem.objects.filter(Q(category=frozen_cat) | Q(is_frozen=True)):
            if item.name.lower().startswith('frozen '):
                item.name = item.name[7:].strip()
                item.save()

    # Ensure all Spring Roll items are non-veg (is_vegetarian=False)
    MenuItem.objects.filter(Q(name__icontains='spring roll') | Q(slug__icontains='spring-roll')).update(is_vegetarian=False)


class Migration(migrations.Migration):

    dependencies = [
        ('kitchen', '0003_update_menu_and_remove_biriyani'),
    ]

    operations = [
        migrations.RunPython(update_frozen_menu_and_options, migrations.RunPython.noop),
    ]

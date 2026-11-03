from django.db import migrations
from django.db.models import Q


def update_menu_and_remove_biriyani(apps, schema_editor):
    Category = apps.get_model('kitchen', 'Category')
    MenuItem = apps.get_model('kitchen', 'MenuItem')

    # Remove any biriyani/biryani item or category added via Staff Portal
    MenuItem.objects.filter(
        Q(name__icontains='biriyani')
        | Q(name__icontains='biryani')
        | Q(slug__icontains='biriyani')
        | Q(slug__icontains='biryani')
    ).delete()

    Category.objects.filter(
        Q(name__icontains='biriyani')
        | Q(name__icontains='biryani')
        | Q(slug__icontains='biriyani')
        | Q(slug__icontains='biryani')
    ).delete()

    frozen_cat = Category.objects.filter(slug='frozen-items').first()
    if frozen_cat:
        new_frozen_items = [
            {
                'slug': 'frozen-chicken-fry',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Frozen Chicken Fry',
                    'tagline': 'Marinated spicy chicken pieces ready to fry',
                    'description': 'Pre-marinated tender chicken pieces coated in our signature spice blend, frozen and ready to fry at home for crispy, juicy chicken anytime.',
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
                'slug': 'frozen-chicken-strips',
                'defaults': {
                    'category': frozen_cat,
                    'name': 'Frozen Chicken Strips',
                    'tagline': 'Seasoned boneless chicken strips ready to cook',
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
                    'order': 2,
                },
            },
        ]
        for item in new_frozen_items:
            MenuItem.objects.update_or_create(
                slug=item['slug'],
                defaults=item['defaults'],
            )


class Migration(migrations.Migration):

    dependencies = [
        ('kitchen', '0002_order_user_customerprofile'),
    ]

    operations = [
        migrations.RunPython(update_menu_and_remove_biriyani, migrations.RunPython.noop),
    ]

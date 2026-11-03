from django.db import migrations
from django.db.models import Q


def rename_frozen_category_to_ready_to_fry(apps, schema_editor):
    Category = apps.get_model('kitchen', 'Category')
    MenuItem = apps.get_model('kitchen', 'MenuItem')

    # Ensure primary Ready to Fry category uses slug 'frozen-items' and name 'Ready to Fry'
    primary_cat = Category.objects.filter(slug='frozen-items').first()
    if primary_cat:
        primary_cat.name = 'Ready to Fry'
        primary_cat.is_active = True
        primary_cat.save()

    # Merge any duplicate 'Frozen Items' or 'ready-to-fry' categories into primary_cat
    extra_cats = Category.objects.filter(
        Q(name__iexact='Frozen Items')
        | Q(name__iexact='Ready to Fry')
        | Q(slug='ready-to-fry')
    )
    if primary_cat:
        extra_cats = extra_cats.exclude(id=primary_cat.id)
        for extra in extra_cats:
            MenuItem.objects.filter(category=extra).update(category=primary_cat)
            extra.delete()
    else:
        first_extra = extra_cats.first()
        if first_extra:
            first_extra.name = 'Ready to Fry'
            first_extra.slug = 'frozen-items'
            first_extra.is_active = True
            first_extra.save()
            for extra in extra_cats.exclude(id=first_extra.id):
                MenuItem.objects.filter(category=extra).update(category=first_extra)
                extra.delete()

    # Ensure all items have a non-empty accessible description
    for item in MenuItem.objects.all():
        if not (item.description or '').strip():
            item.description = (item.tagline or f"Freshly prepared {item.name} from The BYTE Cloud Kitchen.").strip()
            item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kitchen', '0004_update_frozen_menu_and_options'),
    ]

    operations = [
        migrations.RunPython(rename_frozen_category_to_ready_to_fry, migrations.RunPython.noop),
    ]

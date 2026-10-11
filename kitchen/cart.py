import hashlib
from decimal import Decimal
from django.conf import settings
from .models import MenuItem, MenuItemAddon, KitchenSetting


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def _generate_key(self, item_id, special_instructions='', addon_ids=None):
        addons_part = "-".join(sorted(map(str, addon_ids or []))) if addon_ids else "base"
        clean_instructions = special_instructions.strip().lower()
        inst_hash = hashlib.md5(clean_instructions.encode('utf-8')).hexdigest()[:8] if clean_instructions else 'none'
        return f"{item_id}_{addons_part}_{inst_hash}"

    def add(self, item_id, quantity=1, special_instructions='', addon_ids=None):
        try:
            quantity = int(quantity)
            if quantity <= 0 or quantity > 50:
                return False, "Quantity must be between 1 and 50."
        except (ValueError, TypeError):
            return False, "Invalid quantity."

        try:
            item = MenuItem.objects.get(id=item_id, is_available=True)
        except (MenuItem.DoesNotExist, ValueError, TypeError):
            return False, "Item not found or unavailable."

        addon_ids = addon_ids or []
        addons = MenuItemAddon.objects.filter(id__in=addon_ids, is_available=True)
        addons_total = sum(a.price for a in addons)
        addons_names = [f"{a.name} (+৳{a.price})" for a in addons]

        unit_price = item.final_price + addons_total
        key = self._generate_key(item_id, special_instructions, addon_ids)

        if key in self.cart:
            new_qty = self.cart[key]['quantity'] + int(quantity)
            if new_qty > 100:
                return False, "Maximum 100 portions allowed per item."
            self.cart[key]['quantity'] = new_qty
        else:
            self.cart[key] = {
                'item_id': item.id,
                'name': item.name,
                'slug': item.slug,
                'price': str(unit_price),
                'quantity': int(quantity),
                'special_instructions': special_instructions.strip(),
                'addons': addons_names,
                'image': item.image.url if item.image else (item.static_image or ''),
                'portion_size': item.portion_size,
            }

        self.save()
        return True, "Item added to cart."

    def update(self, key, quantity):
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return False
        if key in self.cart:
            if quantity > 100:
                return False
            elif quantity > 0:
                self.cart[key]['quantity'] = quantity
            else:
                del self.cart[key]
            self.save()
            return True
        return False

    def update_delta(self, key, delta):
        try:
            delta = int(delta)
        except (ValueError, TypeError):
            return False
        if key in self.cart:
            new_qty = self.cart[key]['quantity'] + delta
            if new_qty > 100:
                return False
            elif new_qty > 0:
                self.cart[key]['quantity'] = new_qty
            else:
                del self.cart[key]
            self.save()
            return True
        return False

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()
            return True
        return False

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def save(self):
        self.session.modified = True

    def __iter__(self):
        for key, data in self.cart.items():
            qty = data['quantity']
            unit_price = Decimal(data['price'])
            item_total = unit_price * qty
            yield {
                'key': key,
                'item_id': data['item_id'],
                'name': data['name'],
                'slug': data.get('slug', ''),
                'price': unit_price,
                'quantity': qty,
                'special_instructions': data.get('special_instructions', ''),
                'addons': data.get('addons', []),
                'image': data.get('image', ''),
                'portion_size': data.get('portion_size', ''),
                'total': item_total,
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_delivery_fee(self, setting=None):
        if not setting:
            setting = KitchenSetting.objects.first()
        subtotal = self.get_subtotal()
        if subtotal == 0:
            return Decimal('0.00')
        if setting and setting.free_delivery_above and subtotal >= setting.free_delivery_above:
            return Decimal('0.00')
        return Decimal(setting.delivery_fee if setting else 40.00)

    def get_total(self, setting=None):
        return self.get_subtotal() + self.get_delivery_fee(setting)

    def get_free_delivery_progress(self, setting=None):
        if not setting:
            setting = KitchenSetting.objects.first()
        if not setting or not setting.free_delivery_above:
            return 100, Decimal('0.00')
        subtotal = self.get_subtotal()
        threshold = setting.free_delivery_above
        if subtotal >= threshold:
            return 100, Decimal('0.00')
        remaining = threshold - subtotal
        percent = min(int((subtotal / threshold) * 100), 100)
        return percent, remaining

    def get_items_list(self):
        items = []
        for item in self:
            items.append({
                'key': item['key'],
                'item_id': item['item_id'],
                'name': item['name'],
                'slug': item.get('slug', ''),
                'price': float(item['price']),
                'quantity': item['quantity'],
                'special_instructions': item.get('special_instructions', ''),
                'addons': item.get('addons', []),
                'image': item.get('image', ''),
                'portion_size': item.get('portion_size', ''),
                'total': float(item['total']),
            })
        return items


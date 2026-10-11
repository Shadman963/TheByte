# 🍽️ The BYTE — Cloud Kitchen Web Application

A full-stack Cloud Kitchen web application developed using the **Django Framework (v6.1)**, precisely referenced and reverse-engineered from **The BYTE**'s Canva design ([The BYTE Canva Website](https://thebyte39.my.canva.site/thebyte)).

Built specifically for high-volume, budget-friendly meal delivery serving students, office workers, and daily hustlers.

---

## ✨ Features & Architecture

### 1. 🎨 Authentic Visuals & Canva Alignment
- **Branding & Color Theme**: Deep Wine Maroon (`#6e0f2d`), Warm Ivory/Cream (`#f2f4ea`), Amber Flame (`#ff8c42`), and Charcoal (`#1c1517`).
- **Real Canva Food Imagery**: High-resolution photos extracted directly from the Canva design:
  - Signature Chicken Curry & Beef Curry (`curry_main.jpg`, `curry_section_bg.png`)
  - Steamed Plain Rice & Jira Rice (`rice_main.jpg`, `rice_section_bg.png`)
  - Crispy Spiced Chicken Fry & Fries (`fries_main.jpg`, `fries_section_bg.jpg`)
  - Frozen items & Samosas (`frozen_items.jpg`)
  - Brand Logo & Chef Story Artwork (`byte_logo.png`, `story_chef.jpg`)
- **Typography**: Editorial display headers with *Playfair Display* and high-readability UI using *Plus Jakarta Sans*.

---

### 2. 🍲 Food Menu & Categories
- **Curry**:
  - Chicken Curry (Slow-cooked homestyle comfort)
  - Beef Curry (Deeply savory tender beef)
  - Vegetable Curry (Wholesome seasonal harvest)
- **Rice**:
  - Plain Rice (Light & fluffy daily steamed)
  - Fried Rice (Fragrant stir-fry with garden veggies)
  - Jira Rice (Aromatic cumin-infused basmati style)
- **Fries & Crispy Sides**:
  - Chicken Fry (Spicy crunch outside, juicy inside)
  - French Fries (Golden salted crunch)
  - Bengali Pakora (Crispy spiced vegetable fritters)
- **Frozen Items (Ready-to-Fry)**:
  - Spring Rolls (Frozen)
  - Samosa (Frozen)
  - Chicken Fries (Frozen)
  - French Fries (Frozen)
  - Marinated Jumbo Wings (Frozen)
- **Meal Boxes & Combos**:
  - BYTE Student Box (Chicken Curry + Plain Rice + Salad)
  - BYTE Beef Feast Box (Beef Curry + Jira Rice + Pakora)
  - BYTE Crispy Snack Box (Chicken Fry + Fries + Garlic Mayo Dip)

---

### 3. 🛒 Cart, Customization & Ordering
- **Real-time AJAX Drawer & Page**: Add/update/remove items without reloading.
- **Custom Add-ons & Sides**: Extra rice, savory gravy, signature dips (Garlic Mayo, Naga Fire), fresh salad.
- **Cooking Instructions**: Custom notes sent directly to the kitchen (e.g. "less spicy", "separate gravy").
- **Dynamic Delivery Progress**: Live progress meter towards **Free Delivery threshold** (৳600).

---

### 4. 🛵 Checkout & Local Payment Methods
- **Delivery Zone Selection**: Covers Dhaka zones (Mirpur, Dhanmondi, Gulshan, Banani, Uttara, Mohakhali, Panthapath, Mohammadpur, etc.).
- **Flexible Delivery Slots**: Immediate (25-40 mins), Lunch slot, Evening snack, Dinner slot.
- **Payment Options**:
  - **Cash on Delivery (COD)**
  - **bKash Mobile Banking** (with merchant hotline `01718-244371` and TrxID entry)
  - **Nagad Mobile Banking** (with TrxID entry)
  - **Card Payment on Delivery (Rider POS)**

---

### 5. 📍 Real-Time Live Order Tracking
- **Order Number System**: Unique tracking code (e.g. `#BYTE-82194`).
- **Interactive Visual Stepper**:
  1. *Received* 📋
  2. *Confirmed* ✅
  3. *Kitchen Cooking* 🍳
  4. *Packed & Ready* 📦
  5. *Out for Delivery* 🛵
  6. *Delivered* 🎉
- **Auto-polling API**: Checks `/api/order/<order_number>/status/` every 8 seconds and animates status updates live on the customer's screen.

---

### 6. 🧑‍🍳 Kitchen Display System (KDS Dashboard)
- Dedicated live kitchen view at `/kitchen/dashboard/`:
  - Instant overview of active orders grouped by priority.
  - One-click workflow buttons: `Start Cooking 🍳` ➔ `Mark Packed 📦` ➔ `Hand to Rider 🛵` ➔ `Mark Delivered 🎉`.
  - Kitchen Order Ticket (KOT) with special customer cooking notes highlighted in red.
  - Kitchen Open/Closed instant toggle.
  - KPI Metrics: Orders cooking now, today's order count, today's revenue.

---

### 7. ⚙️ Django Administration & Management
- Custom Admin branding at `/admin/`
- Color-coded badges for order status, payment status, and review ratings.
- Manage categories, menu items, addons, kitchen opening hours, delivery fees, and customer contact inquiries.

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- Django 5.x / 6.x

### 2. Setup & Database Seeding
```bash
# Clone / navigate to project
cd F:\TheByte

# Run migrations
python manage.py migrate

# Seed database with authentic Canva menu and branding
python manage.py seed_data

# Run tests
python manage.py test
```

### 3. Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```
Open your browser at:
- **Customer Home**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Full Menu**: [http://127.0.0.1:8000/menu/](http://127.0.0.1:8000/menu/)
- **Cart**: [http://127.0.0.1:8000/cart/](http://127.0.0.1:8000/cart/)
- **Live Order Tracker**: [http://127.0.0.1:8000/order/track/](http://127.0.0.1:8000/order/track/)
  - Sample seeded order: `#BYTE-82194` ([http://127.0.0.1:8000/order/track/BYTE-82194/](http://127.0.0.1:8000/order/track/BYTE-82194/))
- **Kitchen Dashboard (KDS)**: [http://127.0.0.1:8000/kitchen/dashboard/](http://127.0.0.1:8000/kitchen/dashboard/)
- **Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Username**: `admin`
  - **Password**: `admin1234`

---

## 📞 Kitchen Contacts (From Canva Reference)
- **Hotline**: `01718-244371`
- **Email**: `thebyte39@gmail.com`
- **Socials**: Facebook | Instagram | TikTok
- **Location**: Mirpur DOHS / Central Cloud Kitchen, Dhaka, Bangladesh

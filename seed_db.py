import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

# 1. Run migrations to ensure all tables exist on the persistent database
print("Running database migrations...")
call_command('migrate', interactive=False)

from products.models import Product, Category, ProductImage
from django.utils.text import slugify
from django.contrib.auth import get_user_model

# 2. Wipe existing product data to remove duplicates completely
print("Wiping existing product data...")
ProductImage.objects.all().delete()
Product.objects.all().delete()
Category.objects.all().delete()

# Create Categories
categories = {}
for cat_name in ['Timepieces', 'Jewelry', 'Fragrances', 'Accessories', 'Lifestyle', 'Audio', 'Technology']:
    cat, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': slugify(cat_name)})
    categories[cat_name] = cat

# 18 Unique Products
products_data = [
    {
        "name": "Aura Chronograph Gold",
        "category": "Timepieces",
        "description": "Classic luxury handcrafted watch, completed with 24k gold bezel and solid oyster link bracelet.",
        "price": 499999.00,
        "stock": 5,
        "image": "/static/images/watch.png"
    },
    {
        "name": "Lumina Diamond Ring",
        "category": "Jewelry",
        "description": "Solitaire lab-grown 3.5 carat cushion cut diamond mounted on an ultra-slim 18k white gold band.",
        "price": 249999.00,
        "stock": 12,
        "image": "/static/images/ring.png"
    },
    {
        "name": "Nebula Glass Perfume",
        "category": "Fragrances",
        "description": "A signature blend of rare oud, smoked vanilla, sandalwood, and sweet violet highlights.",
        "price": 14999.00,
        "stock": 45,
        "image": "/static/images/perfume.png"
    },
    {
        "name": "Signature Suede Tote",
        "category": "Accessories",
        "description": "Italian calfskin suede tote bag with structural brass hardware handles and suede lined interior.",
        "price": 84999.00,
        "stock": 8,
        "image": "/static/images/bag.png"
    },
    {
        "name": "Solstice Obsidian Pen",
        "category": "Accessories",
        "description": "A luxury fountain pen hand-turned from natural volcanic obsidian stone, with an 18k solid gold nib.",
        "price": 129999.00,
        "stock": 4,
        "image": "/static/images/pen.png"
    },
    {
        "name": "Elysian Amber Jacket",
        "category": "Lifestyle",
        "description": "Bespoke structured motorcycle jacket made of cognac-colored burnished amber lambskin leather.",
        "price": 149999.00,
        "stock": 3,
        "image": "/static/images/jacket.png"
    },
    {
        "name": "Zenith Marble Speaker",
        "category": "Audio",
        "description": "Minimalist cylindrical home audio speaker carved out of a single piece of Carrara white marble.",
        "price": 199999.00,
        "stock": 7,
        "image": "/static/images/speaker.png"
    },
    {
        "name": "Vesper Crystal Decanter",
        "category": "Lifestyle",
        "description": "Mouth-blown lead-free crystal whiskey decanter with geometric glasses, trimmed in 24k gold.",
        "price": 59999.00,
        "stock": 15,
        "image": "/static/images/decanter.png"
    },
    {
        "name": "Aether Celestial Globe",
        "category": "Lifestyle",
        "description": "A luxury desktop mechanical celestial globe, finished in hand-burnished brass and blue lapis lazuli stone.",
        "price": 349999.00,
        "stock": 3,
        "image": "/static/images/globe.png"
    },
    {
        "name": "Oracle Quartz Keyboard",
        "category": "Accessories",
        "description": "A luxury mechanical keyboard with keycaps hand-carved from clear solid crystal quartz, retro brass key stems, and glowing warm white underlight.",
        "price": 189999.00,
        "stock": 6,
        "image": "/static/images/keyboard.png"
    },
    {
        "name": "Hyperion Carbon Chessboard",
        "category": "Lifestyle",
        "description": "A luxury designer chess set, the chessboard and pieces crafted from aerospace-grade carbon fiber and solid blocks of polished black obsidian and white Carrara marble.",
        "price": 299999.00,
        "stock": 4,
        "image": "/static/images/chessboard.png"
    },
    {
        "name": "Helios Amber Sunglasses",
        "category": "Accessories",
        "description": "A pair of luxury handcrafted sunglasses with thick dark amber frames, 24k gold leaf details, and polarized Carl Zeiss lenses.",
        "price": 74999.00,
        "stock": 10,
        "image": "/static/images/sunglasses.png"
    },
    {
        "name": "Aura CyberPhone Titanium",
        "category": "Technology",
        "description": "Aerospace-grade titanium frame, custom graphene battery, and biometric security. High-performance computing meets fine art.",
        "price": 149999.00,
        "stock": 45,
        "image": "/static/images/phone_titanium.png"
    },
    {
        "name": "Aura CyberPhone Carbon",
        "category": "Technology",
        "description": "Super lightweight carbon fiber weave body, ceramic shield display, and high-performance quantum computing chips.",
        "price": 99999.00,
        "stock": 99,
        "image": "/static/images/phone_carbon.png"
    },
    {
        "name": "Valkyrie Titanium Headset",
        "category": "Audio",
        "description": "High-fidelity reference monitor audio headset, carved out of pure aerospace-grade titanium with memory foam leather cups.",
        "price": 249999.00,
        "stock": 10,
        "image": "/static/images/headset.png"
    },
    {
        "name": "Astral Amber Chessboard",
        "category": "Lifestyle",
        "description": "Premium luxury chessboard hand-carved from rare Baltic amber and fossilised wood blocks.",
        "price": 319999.00,
        "stock": 3,
        "image": "/static/images/amber_chessboard.png"
    },
    {
        "name": "Aura Gold Fountain Pen",
        "category": "Accessories",
        "description": "Handcrafted fountain pen detailed with 24k gold leaf and an 18k solid gold medium nib.",
        "price": 159999.00,
        "stock": 5,
        "image": "/static/images/gold_pen.png"
    },
    {
        "name": "Lumina Crystal Decanter",
        "category": "Lifestyle",
        "description": "Fine lead-free crystal whiskey decanter hand-blown by local artisans, featuring 24k gold leaf trim.",
        "price": 69999.00,
        "stock": 8,
        "image": "/static/images/crystal_decanter.png"
    }
]

# Seed Products & Images
print("Seeding products...")
for p_info in products_data:
    p = Product.objects.create(
        name=p_info["name"],
        slug=slugify(p_info["name"]),
        description=p_info["description"],
        price=p_info["price"],
        stock=p_info["stock"],
        category=categories[p_info["category"]],
        is_active=True
    )
    ProductImage.objects.create(
        product=p,
        image_url=p_info["image"]
    )
print("Products seeded successfully!")

# 3. Create Admin Superuser & Test Customer
print("Creating users...")
User = get_user_model()

# Admin
admin_email = 'admin@example.com'
if not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser(
        email=admin_email,
        password='adminpassword',
        first_name='Admin',
        last_name='User'
    )
    print(f"Superuser {admin_email} created with password: 'adminpassword'")
else:
    print(f"Superuser {admin_email} already exists.")

# Test Customer
customer_email = 'customer@example.com'
if not User.objects.filter(email=customer_email).exists():
    User.objects.create_user(
        email=customer_email,
        password='customerpassword',
        first_name='Jane',
        last_name='Doe',
        phone_number='1234567890',
        address='456 Customer Ave, Seattle, WA'
    )
    print(f"Test Customer {customer_email} created with password: 'customerpassword'")
else:
    print(f"Test Customer {customer_email} already exists.")

print("All seeding and migrations completed successfully!")

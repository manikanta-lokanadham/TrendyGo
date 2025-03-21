import os
import django
import random
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from products.models import Category, Brand, Product, ProductImage
from django.utils.text import slugify

def create_sample_data():
    print("Creating sample data...")
    
    # Create categories
    categories = [
        {
            'name': 'Electronics',
            'description': 'Electronic devices and gadgets for everyday use.'
        },
        {
            'name': 'Clothing',
            'description': 'Fashion items for men, women, and children.'
        },
        {
            'name': 'Home & Kitchen',
            'description': 'Everything you need for your home and kitchen.'
        },
        {
            'name': 'Books',
            'description': 'Books of all genres for all ages.'
        },
        {
            'name': 'Sports & Outdoors',
            'description': 'Equipment and gear for sports and outdoor activities.'
        }
    ]
    
    category_objects = {}
    for category_data in categories:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'description': category_data['description'],
                'slug': slugify(category_data['name'])
            }
        )
        category_objects[category.name] = category
        print(f"Category {'created' if created else 'already exists'}: {category.name}")
    
    # Create brands
    brands = [
        {
            'name': 'Apple',
            'description': 'Innovative technology products.'
        },
        {
            'name': 'Samsung',
            'description': 'Leading electronics manufacturer.'
        },
        {
            'name': 'Nike',
            'description': 'Athletic footwear and apparel.'
        },
        {
            'name': 'Adidas',
            'description': 'Sports clothing and accessories.'
        },
        {
            'name': 'Sony',
            'description': 'Consumer electronics and entertainment.'
        },
        {
            'name': 'Penguin Books',
            'description': 'Publishing house for quality literature.'
        },
        {
            'name': 'KitchenAid',
            'description': 'Premium kitchen appliances.'
        }
    ]
    
    brand_objects = {}
    for brand_data in brands:
        brand, created = Brand.objects.get_or_create(
            name=brand_data['name'],
            defaults={
                'description': brand_data['description'],
                'slug': slugify(brand_data['name'])
            }
        )
        brand_objects[brand.name] = brand
        print(f"Brand {'created' if created else 'already exists'}: {brand.name}")
    
    # Create products
    products = [
        # Electronics
        {
            'name': 'Smartphone X Pro',
            'category': 'Electronics',
            'brand': 'Apple',
            'description': 'Latest smartphone with advanced features and long battery life.',
            'price': 999.99,
            'sale_price': 899.99,
            'stock': 50,
            'is_featured': True
        },
        {
            'name': 'Laptop Ultra',
            'category': 'Electronics',
            'brand': 'Apple',
            'description': 'Powerful laptop for professionals and creatives.',
            'price': 1499.99,
            'stock': 30,
            'is_featured': True
        },
        {
            'name': 'Smart TV 55"',
            'category': 'Electronics',
            'brand': 'Samsung',
            'description': '4K Ultra HD Smart TV with voice control.',
            'price': 699.99,
            'sale_price': 649.99,
            'stock': 25,
            'is_featured': True
        },
        {
            'name': 'Wireless Headphones',
            'category': 'Electronics',
            'brand': 'Sony',
            'description': 'Noise-cancelling wireless headphones with premium sound quality.',
            'price': 249.99,
            'stock': 100,
            'is_featured': False
        },
        {
            'name': 'Digital Camera',
            'category': 'Electronics',
            'brand': 'Sony',
            'description': 'High-resolution digital camera for professional photography.',
            'price': 799.99,
            'sale_price': 749.99,
            'stock': 15,
            'is_featured': False
        },
        
        # Clothing
        {
            'name': 'Running Shoes',
            'category': 'Clothing',
            'brand': 'Nike',
            'description': 'Lightweight running shoes with responsive cushioning.',
            'price': 129.99,
            'stock': 80,
            'is_featured': True
        },
        {
            'name': 'Athletic T-Shirt',
            'category': 'Clothing',
            'brand': 'Adidas',
            'description': 'Moisture-wicking athletic t-shirt for workouts.',
            'price': 34.99,
            'sale_price': 29.99,
            'stock': 150,
            'is_featured': False
        },
        {
            'name': 'Denim Jeans',
            'category': 'Clothing',
            'brand': 'Adidas',
            'description': 'Classic denim jeans with comfortable fit.',
            'price': 59.99,
            'stock': 100,
            'is_featured': False
        },
        
        # Home & Kitchen
        {
            'name': 'Stand Mixer',
            'category': 'Home & Kitchen',
            'brand': 'KitchenAid',
            'description': 'Powerful stand mixer for baking and cooking.',
            'price': 349.99,
            'sale_price': 299.99,
            'stock': 20,
            'is_featured': True
        },
        {
            'name': 'Coffee Maker',
            'category': 'Home & Kitchen',
            'brand': 'KitchenAid',
            'description': 'Programmable coffee maker with thermal carafe.',
            'price': 129.99,
            'stock': 40,
            'is_featured': False
        },
        
        # Books
        {
            'name': 'The Great Novel',
            'category': 'Books',
            'brand': 'Penguin Books',
            'description': 'Award-winning novel exploring human relationships.',
            'price': 24.99,
            'sale_price': 19.99,
            'stock': 200,
            'is_featured': True
        },
        {
            'name': 'Cookbook Collection',
            'category': 'Books',
            'brand': 'Penguin Books',
            'description': 'Collection of gourmet recipes from around the world.',
            'price': 39.99,
            'stock': 75,
            'is_featured': False
        },
        
        # Sports & Outdoors
        {
            'name': 'Yoga Mat',
            'category': 'Sports & Outdoors',
            'brand': 'Nike',
            'description': 'Non-slip yoga mat for comfortable practice.',
            'price': 49.99,
            'stock': 120,
            'is_featured': False
        },
        {
            'name': 'Hiking Backpack',
            'category': 'Sports & Outdoors',
            'brand': 'Adidas',
            'description': 'Durable hiking backpack with multiple compartments.',
            'price': 89.99,
            'sale_price': 79.99,
            'stock': 60,
            'is_featured': True
        }
    ]
    
    for product_data in products:
        # Get category and brand
        category = category_objects.get(product_data['category'])
        brand = brand_objects.get(product_data['brand'])
        
        if not category or not brand:
            print(f"Skipping {product_data['name']} - Category or Brand not found")
            continue
        
        # Generate SKU
        sku = f"{category.name[:3].upper()}-{brand.name[:3].upper()}-{random.randint(1000, 9999)}"
        
        # Create product
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults={
                'category': category,
                'brand': brand,
                'slug': slugify(product_data['name']),
                'sku': sku,
                'description': product_data['description'],
                'price': Decimal(str(product_data['price'])),
                'sale_price': Decimal(str(product_data.get('sale_price', 0))) or None,
                'stock': product_data['stock'],
                'is_featured': product_data.get('is_featured', False)
            }
        )
        
        print(f"Product {'created' if created else 'already exists'}: {product.name}")

if __name__ == '__main__':
    create_sample_data() 
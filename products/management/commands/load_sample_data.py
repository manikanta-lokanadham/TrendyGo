from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from products.models import Category, Product
from decimal import Decimal
import random
import os
import shutil

class Command(BaseCommand):
    help = 'Load sample data for development'

    def copy_default_image(self, category):
        try:
            # Use no-image.png as a default for categories
            default_image_path = os.path.join(settings.STATIC_ROOT, 'images', 'no-image.png')
            if os.path.exists(default_image_path):
                with open(default_image_path, 'rb') as f:
                    category.image.save(f"{category.slug}.png", File(f), save=True)
            else:
                self.stdout.write(self.style.WARNING(f'Default image not found for {category.name}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error setting image for {category.name}: {str(e)}'))

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample categories...')
        
        # Create categories with descriptions
        categories_data = [
            {
                'name': 'Electronics',
                'description': 'Latest gadgets and electronic devices'
            },
            {
                'name': 'Fashion',
                'description': 'Trendy clothing and accessories'
            },
            {
                'name': 'Home & Living',
                'description': 'Home decor and furniture'
            },
            {
                'name': 'Books',
                'description': 'Books and educational materials'
            },
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear'
            },
            {
                'name': 'Beauty & Health',
                'description': 'Beauty products and health essentials'
            }
        ]
        
        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'slug': slugify(category_data['name']),
                    'description': category_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created category: {category_data["name"]}')
            
            # Set default image for the category
            if not category.image:
                self.copy_default_image(category)
        
        self.stdout.write('Creating sample products...')
        
        # Create products for each category
        sample_products = [
            {
                'category': 'Electronics',
                'products': [
                    'Smart Watch Pro',
                    'Wireless Earbuds',
                    'HD Webcam',
                    'Bluetooth Speaker'
                ]
            },
            {
                'category': 'Fashion',
                'products': [
                    'Classic T-Shirt',
                    'Denim Jeans',
                    'Running Shoes',
                    'Leather Wallet'
                ]
            },
            {
                'category': 'Home & Living',
                'products': [
                    'Coffee Maker',
                    'Bed Sheet Set',
                    'Table Lamp',
                    'Kitchen Knife Set'
                ]
            },
            {
                'category': 'Books',
                'products': [
                    'Python Programming',
                    'AI & Machine Learning',
                    'Web Development',
                    'Data Science'
                ]
            }
        ]
        
        for category_data in sample_products:
            try:
                category = Category.objects.get(name=category_data['category'])
                for product_name in category_data['products']:
                    price = Decimal(random.uniform(10.0, 200.0)).quantize(Decimal('0.01'))
                    is_featured = random.choice([True, False])
                    rating = random.uniform(3.5, 5.0)
                    
                    product, created = Product.objects.get_or_create(
                        name=product_name,
                        defaults={
                            'category': category,
                            'slug': slugify(product_name),
                            'description': f'Sample description for {product_name}',
                            'price': price,
                            'stock': random.randint(10, 100),
                            'is_available': True,
                            'is_featured': is_featured,
                            'rating': rating,
                            'num_reviews': random.randint(5, 50)
                        }
                    )
                    if created:
                        self.stdout.write(f'Created product: {product_name}')
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Category not found: {category_data["category"]}'))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating products for {category_data["category"]}: {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data')) 
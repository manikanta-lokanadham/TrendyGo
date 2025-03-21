import os
import django
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from products.models import Product
from recommendations.models import UserBehavior
from recommendations.recommendation_engine import RecommendationEngine

def test_recommendations():
    print("Testing recommendation engine...")
    
    # Get a user (create one if none exists)
    user = User.objects.first()
    if not user:
        print("No users found. Creating a test user...")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    print(f"Using user: {user.username}")
    
    # Get some products
    products = Product.objects.all()[:5]
    if not products:
        print("No products found. Please run sample_data.py first.")
        return
    
    # Create some user behaviors
    for product in products:
        # Randomly choose an action
        actions = ['V', 'S', 'C', 'W', 'P']
        action = random.choice(actions)
        count = random.randint(1, 5)
        
        behavior, created = UserBehavior.objects.get_or_create(
            user=user,
            product=product,
            action=action,
            defaults={'count': count}
        )
        
        if not created:
            behavior.count += count
            behavior.save()
        
        print(f"Created/Updated behavior: {user.username} - {product.name} - {action} - {behavior.count}")
    
    # Test different recommendation methods
    engine = RecommendationEngine()
    
    print("\nContent-Based Recommendations:")
    cb_recommendations = engine.content_based_filtering(user)
    for product, score in cb_recommendations[:3]:
        print(f"- {product.name} (Score: {score:.2f})")
    
    print("\nCollaborative Filtering Recommendations:")
    cf_recommendations = engine.collaborative_filtering(user)
    for product, score in cf_recommendations[:3]:
        print(f"- {product.name} (Score: {score:.2f})")
    
    print("\nHybrid Recommendations:")
    hybrid_recommendations = engine.hybrid_recommendations(user)
    for product, score in hybrid_recommendations[:3]:
        print(f"- {product.name} (Score: {score:.2f})")
    
    print("\nTrending Recommendations:")
    trending_recommendations = engine.trending_recommendations()
    for product, score in trending_recommendations[:3]:
        print(f"- {product.name} (Score: {score:.2f})")
    
    print("\nRecent Activity Based Recommendations:")
    recent_recommendations = engine.recent_activity_based(user)
    for product, score in recent_recommendations[:3]:
        print(f"- {product.name} (Score: {score:.2f})")

if __name__ == '__main__':
    test_recommendations() 
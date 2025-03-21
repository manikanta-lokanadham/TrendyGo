from django.shortcuts import render
from django.db.models import Q
from products.models import Product, Category
from recommendations.recommendation_engine import RecommendationEngine

def home(request):
    """Home page view with featured products, new arrivals, and recommendations"""
    try:
        # Get featured products
        featured_products = Product.objects.filter(is_featured=True)[:8]
        
        # Get new arrivals
        new_arrivals = Product.objects.order_by('-created_at')[:8]
        
        # Get categories
        categories = Category.objects.filter(is_active=True)[:6]
        
        # Get recommended products for authenticated users
        recommended_products = []
        if request.user.is_authenticated:
            recommendation_engine = RecommendationEngine()
            recommended_products = recommendation_engine.generate_recommendations_for_user(request.user, limit=8)
        
        context = {
            'featured_products': featured_products,
            'new_arrivals': new_arrivals,
            'categories': categories,
            'recommended_products': recommended_products,
        }
        
        return render(request, 'index.html', context)
    except Exception as e:
        print(f"Error in home view: {e}")
        return render(request, 'index.html', {
            'featured_products': [],
            'new_arrivals': [],
            'categories': [],
            'recommended_products': []
        })

def search_products(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).filter(is_available=True)
    else:
        products = []
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'products/search_results.html', context) 
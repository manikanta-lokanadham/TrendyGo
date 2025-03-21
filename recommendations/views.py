from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Recommendation, UserPreference
from .recommendation_engine import RecommendationEngine
from products.serializers import ProductSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Get personalized product recommendations for the current user"""
    user = request.user
    method = request.query_params.get('method', 'H')  # Default to hybrid
    
    # Check if valid method
    valid_methods = ['CF', 'CB', 'H', 'TR', 'BR']
    if method not in valid_methods:
        method = 'H'
    
    # Get or generate recommendations
    recent_recommendation = Recommendation.objects.filter(
        user=user, 
        method=method
    ).order_by('-created_at').first()
    
    # If no recent recommendation or force refresh requested, generate new ones
    force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
    
    if not recent_recommendation or force_refresh:
        engine = RecommendationEngine()
        recent_recommendation = engine.generate_recommendations_for_user(user, method)
    
    # Get recommendation items
    items = recent_recommendation.items.all().select_related('product')
    
    # Prepare response
    products = [item.product for item in items]
    serializer = ProductSerializer(products, many=True)
    
    return Response({
        'method': recent_recommendation.get_method_display(),
        'products': serializer.data
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    """Get or update user preferences for recommendations"""
    user = request.user
    
    # Get or create user preference
    preference, created = UserPreference.objects.get_or_create(user=user)
    
    if request.method == 'GET':
        # Return current preferences
        data = {
            'favorite_categories': [category.id for category in preference.favorite_categories.all()],
            'price_range_min': preference.price_range_min,
            'price_range_max': preference.price_range_max
        }
        return Response(data)
    
    elif request.method == 'POST':
        # Update preferences
        data = request.data
        
        # Update price range
        if 'price_range_min' in data:
            preference.price_range_min = data['price_range_min']
        if 'price_range_max' in data:
            preference.price_range_max = data['price_range_max']
        
        # Update favorite categories
        if 'favorite_categories' in data:
            preference.favorite_categories.set(data['favorite_categories'])
        
        preference.save()
        
        return Response({'status': 'preferences updated'}, status=status.HTTP_200_OK)

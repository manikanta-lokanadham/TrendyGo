from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'products'

urlpatterns = [
    path('search/', views.search_products, name='search'),
    path('products/<int:pk>/reviews/', views.create_review, name='create_review'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]

router = DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('brands', views.BrandViewSet, basename='brand')

urlpatterns += router.urls 
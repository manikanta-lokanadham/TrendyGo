from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, Review
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary']


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    images = ProductImageSerializer(many=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'sale_price',
            'category', 'brand', 'stock', 'is_available', 'is_featured',
            'rating', 'num_reviews', 'images', 'created_at'
        ]


class ProductDetailSerializer(ProductSerializer):
    reviews = ReviewSerializer(many=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['reviews'] 
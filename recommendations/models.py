from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Category
import numpy as np

class UserBehavior(models.Model):
    ACTION_CHOICES = (
        ('V', 'View'),
        ('S', 'Search'),
        ('C', 'Cart'),
        ('W', 'Wishlist'),
        ('P', 'Purchase'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behaviors')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_behaviors')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    count = models.PositiveIntegerField(default=1)  # How many times this action was performed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'product', 'action')
        ordering = ('-updated_at',)
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.get_action_display()}"


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    favorite_categories = models.ManyToManyField(Category, blank=True, related_name='preferred_by')
    price_range_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_range_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s preferences"


class Recommendation(models.Model):
    METHOD_CHOICES = (
        ('CF', 'Collaborative Filtering'),
        ('CB', 'Content-Based'),
        ('H', 'Hybrid'),
        ('TR', 'Trending'),
        ('BR', 'Based on Recent Activity'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    products = models.ManyToManyField(Product, through='RecommendationItem')
    method = models.CharField(max_length=2, choices=METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return f"{self.user.username}'s recommendations ({self.get_method_display()})"


class RecommendationItem(models.Model):
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField()  # Recommendation score/confidence
    position = models.PositiveSmallIntegerField()  # Order of recommendation
    
    class Meta:
        ordering = ('position',)
        unique_together = ('recommendation', 'product')
    
    def __str__(self):
        return f"{self.product.name} in {self.recommendation}"


class SimilarityMatrix(models.Model):
    """Stores product similarity scores for content-based filtering"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='similarity_data')
    matrix = models.BinaryField()  # Pickled numpy array of similarity scores
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Similarity data for {self.product.name}"
    
    def get_matrix(self):
        """Unpickle the matrix"""
        return np.frombuffer(self.matrix)
    
    def set_matrix(self, matrix_array):
        """Pickle the matrix for storage"""
        self.matrix = matrix_array.tobytes()

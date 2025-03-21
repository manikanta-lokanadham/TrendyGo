from django.contrib import admin
from .models import UserBehavior, UserPreference, Recommendation, RecommendationItem, SimilarityMatrix

class RecommendationItemInline(admin.TabularInline):
    model = RecommendationItem
    extra = 0
    readonly_fields = ('product', 'score', 'position')

@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'action', 'count', 'updated_at')
    list_filter = ('action', 'updated_at')
    search_fields = ('user__username', 'product__name')

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'price_range_min', 'price_range_max', 'updated_at')
    filter_horizontal = ('favorite_categories',)
    search_fields = ('user__username',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'created_at')
    list_filter = ('method', 'created_at')
    search_fields = ('user__username',)
    inlines = [RecommendationItemInline]

@admin.register(SimilarityMatrix)
class SimilarityMatrixAdmin(admin.ModelAdmin):
    list_display = ('product', 'updated_at')
    search_fields = ('product__name',)

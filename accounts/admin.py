from django.contrib import admin
from .models import UserProfile, Address

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_filter = ('created_at', 'updated_at')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'state', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country', 'state', 'city', 'created_at')
    search_fields = ('user__username', 'address_line1', 'city', 'state', 'postal_code', 'country')

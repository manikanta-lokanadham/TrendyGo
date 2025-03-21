from django.contrib import admin
from .models import Payment, PaymentMethod

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'order', 'amount_paid', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('payment_id', 'user__username', 'order__order_number')
    readonly_fields = ('payment_id', 'user', 'order', 'amount_paid', 'created_at')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'is_default', 'created_at')
    list_filter = ('method_type', 'is_default')
    search_fields = ('user__username', 'cardholder_name', 'upi_id')
    readonly_fields = ('token',)

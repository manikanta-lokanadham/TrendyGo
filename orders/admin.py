from django.contrib import admin
from .models import Order, OrderItem, CartItem, Payment, Refund

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'total')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    exclude = ('updated_at',)
    list_display = ('order_id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_id', 'user__username', 'first_name', 'last_name')
    readonly_fields = ('order_id', 'created_at', 'total_amount')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'notes')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address',)
        }),
        ('Amount Information', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    ordering = ('-created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment_id', 'order__order_id')
    readonly_fields = ('payment_id', 'created_at')

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'refund_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_id',)
    readonly_fields = ('created_at', 'updated_at')

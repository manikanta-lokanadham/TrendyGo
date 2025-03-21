from django.db import models
from django.contrib.auth.models import User
from orders.models import Order

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('CC', 'Credit Card'),
        ('DC', 'Debit Card'),
        ('PP', 'PayPal'),
        ('UPI', 'UPI'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('P', 'Pending'),
        ('C', 'Completed'),
        ('F', 'Failed'),
        ('R', 'Refunded'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=3, choices=PAYMENT_METHOD_CHOICES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.payment_id}"


class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('CC', 'Credit Card'),
        ('DC', 'Debit Card'),
        ('UPI', 'UPI'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=3, choices=METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    
    # For credit/debit cards
    card_number = models.CharField(max_length=16, blank=True, null=True)  # Store last 4 digits only
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    expiry_month = models.CharField(max_length=2, blank=True, null=True)
    expiry_year = models.CharField(max_length=4, blank=True, null=True)
    card_type = models.CharField(max_length=20, blank=True, null=True)  # Visa, Mastercard, etc.
    
    # For UPI
    upi_id = models.CharField(max_length=50, blank=True, null=True)
    
    # For all payment methods
    token = models.CharField(max_length=255, blank=True, null=True)  # Payment gateway token
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        unique_together = ('user', 'card_number')  # Ensures no duplicate cards
    
    def __str__(self):
        if self.method_type in ['CC', 'DC']:
            return f"{self.get_method_type_display()} ending with {self.card_number[-4:]}"
        elif self.method_type == 'UPI':
            return f"UPI: {self.upi_id}"
        return f"{self.get_method_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default payment method per user
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super(PaymentMethod, self).save(*args, **kwargs)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from decimal import Decimal
from django.db import transaction
from .models import Order, OrderItem, CartItem, Cart
from .utils import generate_invoice_pdf
from accounts.models import Address
from products.models import Product

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)\
        .prefetch_related('items__product__images')\
        .order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    context = {
        'order': order,
        'items': order.items.all(),
        'total_items': order.items.count(),
        'subtotal': order.subtotal,
        'tax': order.tax_amount,
        'total': order.total_amount
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'orders/track_order.html', {'order': order})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    response = generate_invoice_pdf(order)
    return response

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get cart and items
                cart = Cart.objects.get(user=request.user)
                cart_items = CartItem.objects.filter(cart=cart)
                
                if not cart_items.exists():
                    messages.error(request, 'Your cart is empty.')
                    return redirect('cart')
                
                # Calculate totals
                total = sum(item.total_price for item in cart_items)
                tax = Decimal('0.10') * total  # 10% tax
                total_with_tax = total + tax
                
                # Get shipping details
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                notes = request.POST.get('notes')
                payment_method = request.POST.get('payment_method')
                
                # Handle address
                selected_address_id = request.POST.get('selected_address')
                if selected_address_id:
                    # Use selected address
                    address = get_object_or_404(Address, id=selected_address_id, user=request.user)
                    shipping_address = address.address_line1
                    if address.address_line2:
                        shipping_address += f"\n{address.address_line2}"
                    shipping_address += f"\n{address.city}, {address.state} {address.postal_code}\n{address.country}"
                else:
                    # Create new address
                    address = Address.objects.create(
                        user=request.user,
                        address_line1=request.POST.get('address_line1'),
                        address_line2=request.POST.get('address_line2', ''),
                        city=request.POST.get('city'),
                        state=request.POST.get('state'),
                        postal_code=request.POST.get('postal_code'),
                        country=request.POST.get('country'),
                        is_default=request.POST.get('set_default') == 'on' or not Address.objects.filter(user=request.user).exists()
                    )
                    shipping_address = address.address_line1
                    if address.address_line2:
                        shipping_address += f"\n{address.address_line2}"
                    shipping_address += f"\n{address.city}, {address.state} {address.postal_code}\n{address.country}"
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    shipping_address=shipping_address,
                    notes=notes,
                    payment_method=payment_method,
                    subtotal=total,
                    tax_amount=tax,
                    total_amount=total_with_tax,
                    status='pending'
                )
                
                # Create order items and clear cart
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        total=cart_item.total_price
                    )
                    # Update product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
                
                cart_items.delete()
                cart.delete()
                
                messages.success(request, 'Order placed successfully!')
                return redirect('order_detail', order_id=order.order_id)
                
        except Exception as e:
            messages.error(request, f'An error occurred while placing your order: {str(e)}')
            return redirect('cart')
    
    # GET request - show checkout form
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        
        # Calculate totals
        total = sum(item.total_price for item in cart_items)
        tax = Decimal('0.10') * total  # 10% tax
        total_with_tax = total + tax
        
        # Get user's addresses
        addresses = Address.objects.filter(user=request.user)
        selected_address = request.GET.get('selected_address')
        
        # If no address is selected but user has a default address, select it
        if not selected_address and addresses.exists():
            default_address = addresses.filter(is_default=True).first()
            if default_address:
                selected_address = default_address.id
        
        context = {
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'total_with_tax': total_with_tax,
            'addresses': addresses,
            'selected_address': selected_address
        }
        return render(request, 'orders/checkout.html', context)
        
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

@login_required
def buy_now_checkout(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Get shipping details
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    email = request.POST.get('email')
                    phone = request.POST.get('phone')
                    notes = request.POST.get('notes')
                    payment_method = request.POST.get('payment_method')
                    
                    # Calculate totals
                    subtotal = product.price
                    tax_amount = subtotal * Decimal('0.1')  # 10% tax
                    total_amount = subtotal + tax_amount
                    
                    # Handle address
                    selected_address_id = request.POST.get('selected_address')
                    if selected_address_id:
                        # Use selected address
                        address = get_object_or_404(Address, id=selected_address_id, user=request.user)
                        shipping_address = address.address_line1
                        if address.address_line2:
                            shipping_address += f"\n{address.address_line2}"
                        shipping_address += f"\n{address.city}, {address.state} {address.postal_code}\n{address.country}"
                    else:
                        # Use new address
                        shipping_address = request.POST.get('address_line1')
                        if request.POST.get('address_line2'):
                            shipping_address += f"\n{request.POST.get('address_line2')}"
                        shipping_address += f"\n{request.POST.get('city')}, {request.POST.get('state')} {request.POST.get('postal_code')}\n{request.POST.get('country')}"
                    
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        shipping_address=shipping_address,
                        notes=notes,
                        payment_method=payment_method,
                        subtotal=subtotal,
                        tax_amount=tax_amount,
                        total_amount=total_amount,
                        status='pending'
                    )
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=1,
                        price=product.price,
                        total=product.price
                    )
                    
                    # Update product stock
                    product.stock -= 1
                    product.save()
                    
                    messages.success(request, 'Order placed successfully!')
                    return redirect('order_detail', order_id=order.order_id)
                    
            except Exception as e:
                messages.error(request, f'An error occurred while placing your order: {str(e)}')
                return redirect('product_detail', product_id=product_id)
        
        # GET request - show checkout form
        # Get user's addresses
        addresses = Address.objects.filter(user=request.user)
        selected_address = request.GET.get('selected_address')
        
        context = {
            'product': product,
            'total': product.price,
            'tax': product.price * Decimal('0.1'),
            'total_with_tax': product.price * Decimal('1.1'),
            'addresses': addresses,
            'selected_address': selected_address
        }
        return render(request, 'orders/buy_now_checkout.html', context)
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('product_detail', product_id=product_id)

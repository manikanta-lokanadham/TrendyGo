from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, Brand, Review, WishlistItem, Coupon
from orders.models import CartItem, Order, OrderItem
from .serializers import (
    ProductSerializer, 
    ProductDetailSerializer, 
    CategorySerializer, 
    BrandSerializer,
    ReviewSerializer
)
from recommendations.models import UserBehavior
from recommendations.recommendation_engine import RecommendationEngine
import os
from django.http import JsonResponse
from decimal import Decimal
from orders.utils import generate_invoice_pdf
from django.db.models.deletion import transaction

def get_default_image():
    return os.path.join(settings.STATIC_URL, 'images', 'no-image.png')

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_available=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'is_featured']
    search_fields = ['name', 'description', 'category__name', 'brand__name']
    ordering_fields = ['price', 'created_at', 'name', 'rating']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Track user behavior for recommendations
        if request.user.is_authenticated:
            behavior, created = UserBehavior.objects.get_or_create(
                user=request.user,
                product=instance,
                action='V'  # View
            )
            if not created:
                behavior.count += 1
                behavior.save()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = Product.objects.filter(is_featured=True, is_available=True)[:8]
        serializer = ProductSerializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        new_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
        serializer = ProductSerializer(new_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        top_products = Product.objects.filter(is_available=True, rating__gt=0).order_by('-rating')[:8]
        serializer = ProductSerializer(top_products, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, pk):
    user = request.user
    product = get_object_or_404(Product, pk=pk)
    
    # Check if user already reviewed this product
    already_exists = Review.objects.filter(user=user, product=product).exists()
    if already_exists:
        return Response({'detail': 'Product already reviewed'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get data from request
    data = request.data
    rating = data.get('rating', 0)
    comment = data.get('comment', '')
    
    if rating == 0:
        return Response({'detail': 'Please select a rating'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create review
    review = Review.objects.create(
        user=user,
        product=product,
        rating=rating,
        comment=comment
    )
    
    # Track user behavior for recommendations
    behavior, created = UserBehavior.objects.get_or_create(
        user=user,
        product=product,
        action='V'  # View - we count reviews as views too
    )
    if not created:
        behavior.count += 1
        behavior.save()
    
    return Response({'detail': 'Review added'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def search_products(request):
    query = request.GET.get('q', '')
    products = []
    
    if query:
        # Track search behavior
        if request.user.is_authenticated:
            products = Product.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(brand__name__icontains=query)
            )
            for product in products:
                behavior, created = UserBehavior.objects.get_or_create(
                    user=request.user,
                    product=product,
                    action='S'  # Search
                )
                if not created:
                    behavior.count += 1
                    behavior.save()
        
        # Perform actual search
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).filter(is_available=True)
        
        # Add default images if needed
        for product in products:
            if not product.images.exists():
                product.default_image = get_default_image()
    
    context = {
        'products': products,
        'query': query,
        'total_results': len(products)
    }
    
    return render(request, 'products/search_results.html', context)

def home(request):
    try:
        # Get featured products
        featured_products = Product.objects.filter(is_featured=True)[:8]
        for product in featured_products:
            if not product.images.exists():
                product.default_image = get_default_image()
        
        # Get new arrivals
        new_arrivals = Product.objects.order_by('-created_at')[:8]
        for product in new_arrivals:
            if not product.images.exists():
                product.default_image = get_default_image()
        
        # Get top rated products
        top_rated = Product.objects.filter(rating__gt=0).order_by('-rating')[:8]
        for product in top_rated:
            if not product.images.exists():
                product.default_image = get_default_image()
        
        # Get categories
        categories = Category.objects.filter(is_active=True)[:6]
        
        # Get recommended products for authenticated users
        recommended_products = []
        if request.user.is_authenticated:
            recommendation_engine = RecommendationEngine()
            recommended_products = recommendation_engine.get_recommendations(request.user, limit=8)
            for product in recommended_products:
                if not product.images.exists():
                    product.default_image = get_default_image()
        
        context = {
            'featured_products': featured_products,
            'new_arrivals': new_arrivals,
            'top_rated': top_rated,
            'categories': categories,
            'recommended_products': recommended_products,
        }
        
        return render(request, 'index.html', context)
    except Exception as e:
        print(f"Error in home view: {str(e)}")
        # Return empty lists if there's an error, but still render the page
        return render(request, 'index.html', {
            'featured_products': [],
            'new_arrivals': [],
            'top_rated': [],
            'categories': Category.objects.filter(is_active=True)[:6],
            'recommended_products': [],
        })

def products_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.filter(is_active=True)
    
    # Get filter parameters
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', 'name')
    
    # Apply filters
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_id,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'products/products_list.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_available=True
    ).exclude(id=product.id)[:4]
    
    # Check if product is in user's wishlist
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(user=request.user, product=product).exists()
        
        # Track user behavior for recommendations
        behavior, created = UserBehavior.objects.get_or_create(
            user=request.user,
            product=product,
            action='V'  # View
        )
        if not created:
            behavior.count += 1
            behavior.save()
    
    context = {
        'product': product,
        'related_products': related_products,
        'is_in_wishlist': is_in_wishlist,
    }
    return render(request, 'products/product_detail.html', context)

def categories_list(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'products/categories_list.html', {'categories': categories})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if product is in stock
    if product.stock < quantity:
        messages.error(request, f"Sorry, only {product.stock} items of {product.name} are available.")
        return redirect('product_detail', slug=product.slug)
    
    # Try to get existing cart item
    try:
        cart_item = CartItem.objects.get(user=request.user, product=product)
        # Check if new quantity exceeds stock
        if quantity > product.stock:
            messages.error(request, f"Sorry, {quantity} {product.name} would exceed available stock.")
            return redirect('product_detail', slug=product.slug)
        
        # Replace quantity instead of adding to it
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Cart updated! {product.name} quantity set to {quantity}.")
    except CartItem.DoesNotExist:
        # Create new cart item
        cart_item = CartItem.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )
        messages.success(request, f"Added {quantity} {product.name} to your cart!")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_items = CartItem.objects.filter(user=request.user)
        cart_total = sum(item.total_price for item in cart_items)
        cart_count = sum(item.quantity for item in cart_items)
        
        return JsonResponse({
            'status': 'success',
            'message': f"Added {quantity} {product.name} to cart",
            'cart_total': cart_total,
            'cart_count': cart_count
        })
    
    return redirect('cart')

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return redirect('buy_now_checkout', product_id=product_id)

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    messages.success(request, "Cart updated.")
    return redirect('cart')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    cart_total = sum(item.total_price for item in cart_items)
    
    # Initialize values
    shipping_cost = Decimal('0.00')  # Free shipping for now
    discount_amount = Decimal('0.00')
    
    # Apply coupon discount if exists in session
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            if not coupon.is_expired():
                # Calculate discount amount
                discount_amount = (cart_total * (coupon.discount / Decimal('100'))).quantize(Decimal('0.01'))
            else:
                # Remove expired coupon from session
                del request.session['coupon_id']
        except Coupon.DoesNotExist:
            # Remove invalid coupon from session
            del request.session['coupon_id']
    
    # Calculate final total
    final_total = cart_total + shipping_cost - discount_amount
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }
    return render(request, 'products/cart.html', context)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.name} {'added to' if created else 'is already in'} wishlist."
        })
    
    if created:
        messages.success(request, f"{product.name} added to wishlist.")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")
    
    # Redirect back to the referring page, or to the product detail page
    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('product_detail', slug=product.slug)

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.name} removed from wishlist."
        })
    
    messages.success(request, f"{product.name} removed from wishlist.")
    
    # Redirect back to the referring page, or to the wishlist page
    next_url = request.META.get('HTTP_REFERER')
    if next_url and 'wishlist' not in next_url:
        return redirect(next_url)
    return redirect('wishlist')

@login_required
def wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def add_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if rating == 0:
            messages.error(request, "Please select a rating.")
            return redirect('product_detail', slug=slug)
        
        review, created = Review.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating, 'comment': comment}
        )
        
        if not created:
            review.rating = rating
            review.comment = comment
            review.save()
            messages.success(request, "Your review has been updated.")
        else:
            messages.success(request, "Your review has been added.")
        
        return redirect('product_detail', slug=slug)
    
    return redirect('product_detail', slug=slug)

@login_required
def product_reviews(request):
    reviews = Review.objects.filter(user=request.user)
    return render(request, 'products/reviews.html', {'reviews': reviews})

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get cart items
                cart_items = CartItem.objects.filter(user=request.user)
                if not cart_items.exists():
                    messages.error(request, "Your cart is empty.")
                    return redirect('cart')
                
                # Validate stock before proceeding
                for cart_item in cart_items:
                    if cart_item.quantity > cart_item.product.stock:
                        messages.error(request, f"Sorry, only {cart_item.product.stock} items of {cart_item.product.name} are available.")
                        return redirect('cart')
                
                # Calculate totals
                subtotal = sum(item.total_price for item in cart_items)
                tax_amount = subtotal * Decimal('0.1')  # 10% tax
                shipping_cost = Decimal('0.00')  # Free shipping
                total_amount = subtotal + tax_amount + shipping_cost
                
                # Handle address
                selected_address_id = request.POST.get('selected_address')
                if selected_address_id:
                    # Use selected address
                    address = get_object_or_404(Address, id=selected_address_id, user=request.user)
                    shipping_address = f"{request.user.first_name} {request.user.last_name}\n{address.address_line1}"
                    if address.address_line2:
                        shipping_address += f"\n{address.address_line2}"
                    shipping_address += f"\n{address.city}, {address.state} {address.postal_code}\n{address.country}"
                else:
                    # Use new address
                    shipping_address = f"{request.user.first_name} {request.user.last_name}\n{request.POST.get('address_line1')}"
                    if request.POST.get('address_line2'):
                        shipping_address += f"\n{request.POST.get('address_line2')}"
                    shipping_address += f"\n{request.POST.get('city')}, {request.POST.get('state')} {request.POST.get('postal_code')}\n{request.POST.get('country')}"
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=request.POST.get('first_name', request.user.first_name),
                    last_name=request.POST.get('last_name', request.user.last_name),
                    email=request.POST.get('email', request.user.email),
                    phone=request.POST.get('phone', ''),
                    shipping_address=shipping_address,
                    payment_method=request.POST.get('payment_method', 'cod'),
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    status='pending',
                    payment_status='pending'
                )
                
                # Create order items and update stock
                for cart_item in cart_items:
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        total=cart_item.total_price
                    )
                    
                    # Update product stock
                    product = cart_item.product
                    product.stock -= cart_item.quantity
                    product.save()
                    
                    # Delete cart item
                    cart_item.delete()
                
                messages.success(request, "Your order has been placed successfully!")
                return redirect('order_detail', order_id=order.order_id)
                
        except Exception as e:
            messages.error(request, f"An error occurred while placing your order: {str(e)}")
            return redirect('cart')
    
    return redirect('checkout')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'orders/track_order.html', context)

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return generate_invoice_pdf(order)

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            
            # Check if coupon is expired
            if coupon.is_expired():
                messages.error(request, 'This coupon has expired.')
                return redirect('cart')
            
            # Save coupon to session
            request.session['coupon_id'] = coupon.id
            messages.success(request, f'Coupon "{code}" applied successfully!')
            
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
            request.session['coupon_id'] = None
            
    return redirect('cart')

@login_required
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            wishlist_item = WishlistItem.objects.filter(user=request.user, product=product)
            
            if wishlist_item.exists():
                # Remove from wishlist
                wishlist_item.delete()
                message = f"{product.name} removed from wishlist."
                is_in_wishlist = False
            else:
                # Add to wishlist
                WishlistItem.objects.create(user=request.user, product=product)
                message = f"{product.name} added to wishlist."
                is_in_wishlist = True
            
            # Get updated wishlist count
            wishlist_count = WishlistItem.objects.filter(user=request.user).count()
            
            return JsonResponse({
                'success': True,
                'message': message,
                'is_in_wishlist': is_in_wishlist,
                'wishlist_count': wishlist_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }, status=400)

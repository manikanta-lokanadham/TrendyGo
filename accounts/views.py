from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import UserProfile, Address
from products.models import WishlistItem  # Import WishlistItem from products app
from .serializers import UserProfileSerializer, AddressSerializer
from .forms import UserRegistrationForm, UserProfileForm, ProfileUpdateForm, AddressForm
from orders.models import Order
from django.http import JsonResponse

# Views will be added as we develop features

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                
                # Check if this is an admin login attempt
                if request.path.startswith('/admin/'):
                    if user.is_superuser:
                        return redirect('admin:index')
                    else:
                        messages.error(request, 'You do not have permission to access the admin site.')
                        return redirect('home')
                
                # Handle regular login
                if next_url:
                    return redirect(next_url)
                if user.is_superuser:
                    return redirect('admin:index')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return render(request, 'accounts/logout.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    # Get recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get total orders count
    total_orders = Order.objects.filter(user=request.user).count()
    
    # Get wishlist count
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    
    # Get address count
    address_count = Address.objects.filter(user=request.user).count()
    
    context = {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'wishlist_count': wishlist_count,
        'address_count': address_count,
        'active_tab': 'dashboard',
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if form.is_valid():
            # Update User model fields
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Update Profile model fields
            profile = form.save(commit=False)
            profile.user = user
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
            
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        # Pre-populate form with user and profile data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': request.user.profile.phone,
            'bio': request.user.profile.bio,
        }
        form = ProfileUpdateForm(instance=request.user.profile, initial=initial_data)
    
    context = {
        'form': form,
        'active_tab': 'profile',
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/orders_list.html', {'orders': orders, 'active_tab': 'orders'})

@login_required
def add_address(request):
    if request.method == 'POST':
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        
        # Set as default if this is the first address
        is_default = not Address.objects.filter(user=request.user).exists()
        
        address = Address.objects.create(
            user=request.user,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        
        messages.success(request, 'Address added successfully.')
        
        # Check if we need to return to checkout
        next_page = request.POST.get('next')
        if next_page == 'checkout':
            return redirect('checkout', selected_address=address.id)
        return redirect('addresses')
    
    return redirect('addresses')

@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country')
        address.save()
        
        messages.success(request, 'Address updated successfully.')
        
        # Check if we need to return to checkout
        next_page = request.POST.get('next')
        if next_page == 'checkout':
            return redirect('checkout', selected_address=address.id)
        return redirect('addresses')
    
    return redirect('addresses')

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # If this was the default address, make another address default
        if address.is_default:
            other_address = Address.objects.filter(user=request.user).exclude(id=address_id).first()
            if other_address:
                other_address.is_default = True
                other_address.save()
        
        address.delete()
        messages.success(request, 'Address deleted successfully.')
    
    # Check if we need to return to checkout
    next_page = request.GET.get('next')
    if next_page == 'checkout':
        return redirect('checkout')
    return redirect('addresses')

@login_required
def set_default_address(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Remove default from other addresses
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set new default
        address.is_default = True
        address.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Default address updated successfully.',
                'address_id': address.id
            })
        
        messages.success(request, 'Default address updated successfully.')
        
        # Check if we need to return to checkout
        next_page = request.POST.get('next')
        if next_page == 'checkout':
            return redirect('checkout', selected_address=address.id)
    
    return redirect('addresses')

@login_required
def addresses(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {
        'addresses': addresses,
        'next': request.GET.get('next')
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        # Process password change
        pass
    return render(request, 'accounts/change_password.html', {'active_tab': 'password'})

@login_required
def customer_support(request):
    if request.method == 'POST':
        # Handle support ticket submission
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        # Here you would typically create a support ticket or send an email
        messages.success(request, 'Your support request has been submitted. We will get back to you soon.')
        return redirect('customer_support')
    return render(request, 'accounts/customer_support.html')

@login_required
def download_invoice(request, order_id):
    # This will be implemented in the orders app
    pass

def admin_signup_request(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        reason = request.POST.get('reason')
        
        # Send email to admin
        subject = 'New Admin Access Request'
        message = f"""
        A new admin access request has been submitted:
        
        Name: {name}
        Email: {email}
        Reason: {reason}
        
        Please review and respond accordingly.
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Your admin access request has been submitted. We will review it and get back to you soon.')
        except Exception as e:
            messages.error(request, 'There was an error submitting your request. Please try again later.')
        
        return redirect('login')
    
    return redirect('login')

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@login_required
def account_wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'accounts/account_wishlist.html', {
        'wishlist_items': wishlist_items,
        'active_tab': 'wishlist'
    })

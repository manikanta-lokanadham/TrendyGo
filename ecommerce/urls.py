"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from products import views as product_views
from products.views import (
    products_list, product_detail, categories_list,
    add_to_cart, remove_from_cart, update_cart, cart,
    add_to_wishlist, remove_from_wishlist, wishlist,
    checkout, place_order, order_history, order_detail,
    track_order, add_review, product_reviews, buy_now,
    apply_coupon
)
from accounts.views import (
    register, profile, add_address, delete_address,
    customer_support, login_view, logout_view
)
# from blog.views import blog_list, blog_detail  # Temporarily commented out

# Customize admin site
admin.site.login_template = 'admin/login.html'
admin.site.logout_template = 'accounts/logout.html'

urlpatterns = [
    # Main pages
    path('', product_views.home, name='home'),
    path('admin/', admin.site.urls),
    # path('ckeditor/', include('ckeditor_uploader.urls')),  # Commenting this out for now
    
    # Product related URLs
    path('products/', product_views.products_list, name='products_list'),
    path('products/<slug:slug>/', product_views.product_detail, name='product_detail'),
    path('categories/', product_views.categories_list, name='categories_list'),
    path('search/', product_views.search_products, name='search_products'),
    
    # Cart & Wishlist
    path('cart/', cart, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart, name='update_cart'),
    path('cart/apply-coupon/', apply_coupon, name='apply_coupon'),
    path('wishlist/', wishlist, name='wishlist'),
    path('api/products/wishlist/toggle/<int:product_id>/', product_views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    
    # Checkout & Orders
    path('checkout/', checkout, name='checkout'),
    path('place-order/', place_order, name='place_order'),
    path('buy-now/<int:product_id>/', buy_now, name='buy_now'),
    path('orders/', include('orders.urls')),
    
    # Authentication URLs
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('account/', profile, name='profile'),
    path('account/password/change/', 
         auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'),
         name='change_password'),
    path('account/password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
         name='password_change_done'),
    path('account/password/reset/',
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('account/password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('account/password/reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    
    # User Profile & Support
    path('account/address/add/', add_address, name='add_address'),
    path('account/address/delete/<int:address_id>/', delete_address, name='delete_address'),
    path('support/', customer_support, name='customer_support'),
    path('reviews/', product_reviews, name='product_reviews'),
    path('products/<slug:slug>/review/', add_review, name='add_review'),
    
    # Blog URLs - Temporarily commented out
    # path('blog/', blog_list, name='blog_list'),
    # path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    
    # API URLs
    path('api/accounts/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media and static files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

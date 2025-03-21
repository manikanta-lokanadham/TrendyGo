from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet, AddressViewSet, dashboard, profile, orders_list,
    add_address, addresses, edit_address, delete_address, change_password,
    login_view, logout_view, register, admin_signup_request, set_default_address,
    account_wishlist
)

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('admin-signup-request/', admin_signup_request, name='admin_signup_request'),
    path('', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('orders/', orders_list, name='orders_list'),
    path('addresses/', addresses, name='addresses'),
    path('addresses/add/', add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', delete_address, name='delete_address'),
    path('addresses/set-default/<int:address_id>/', set_default_address, name='set_default_address'),
    path('change-password/', change_password, name='change_password'),
    path('wishlist/', account_wishlist, name='account_wishlist'),
    path('', include(router.urls)),
] 
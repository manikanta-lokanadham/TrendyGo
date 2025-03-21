from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_history, name='order_history'),
    path('buy-now/<int:product_id>/checkout/', views.buy_now_checkout, name='buy_now_checkout'),
    path('<str:order_id>/', views.order_detail, name='order_detail'),
    path('<str:order_id>/track/', views.track_order, name='track_order'),
    path('<str:order_id>/invoice/', views.download_invoice, name='download_invoice'),
] 
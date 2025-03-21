from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.get_recommendations, name='recommendations'),
    path('preferences/', views.user_preferences, name='preferences'),
] 
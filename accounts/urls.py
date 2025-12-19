from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # URL to Create the payment (Frontend uses this)
    path('deposit/nowpayments/', views.create_nowpayments_deposit, name='nowpayments_deposit'),
    
    # URL for NOWPayments to call (Backend listener)
    path('deposit/nowpayments/ipn/', views.nowpayments_ipn, name='nowpayments_ipn'),
]
"""
Delta Coin URL Configuration
"""
from django.urls import path
from . import views_delta

app_name = 'delta'

urlpatterns = [
    # Wallet endpoints
    path('balance/', views_delta.get_wallet_balance, name='balance'),
    path('wallet/', views_delta.get_wallet_details, name='wallet'),
    
    # Transaction endpoints
    path('transactions/', views_delta.get_transaction_history, name='transactions'),
    path('transfer/', views_delta.transfer_delta, name='transfer'),
    
    # Product endpoints
    path('products/', views_delta.list_products, name='products'),
    path('purchase/', views_delta.purchase_product, name='purchase'),
    path('purchases/', views_delta.get_purchase_history, name='purchases'),
    
    # Leaderboard
    path('leaderboard/', views_delta.get_leaderboard, name='leaderboard'),
]

"""
Delta Coin Serializers

DRF serializers for Delta coin models.
"""
from rest_framework import serializers
from .models_delta import (
    DeltaWallet,
    DeltaTransaction,
    DeltaEarningRule,
    DeltaProduct,
    DeltaPurchase
)


class DeltaWalletSerializer(serializers.ModelSerializer):
    """Serializer for Delta wallet."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    formatted_balance = serializers.CharField(read_only=True)
    
    class Meta:
        model = DeltaWallet
        fields = [
            'id',
            'user_email',
            'balance',
            'formatted_balance',
            'total_earned',
            'total_spent',
            'is_active',
            'is_frozen',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class DeltaTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Delta transaction."""
    
    wallet_user = serializers.EmailField(source='wallet.user.email', read_only=True)
    formatted_amount = serializers.CharField(read_only=True)
    related_user_email = serializers.EmailField(source='related_user.email', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeltaTransaction
        fields = [
            'id',
            'wallet_user',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'formatted_amount',
            'balance_before',
            'balance_after',
            'status',
            'status_display',
            'related_user_email',
            'reference_id',
            'reference_type',
            'description',
            'metadata',
            'is_reversed',
            'created_at'
        ]
        read_only_fields = fields


class DeltaEarningRuleSerializer(serializers.ModelSerializer):
    """Serializer for earning rules."""
    
    class Meta:
        model = DeltaEarningRule
        fields = [
            'id',
            'name',
            'description',
            'amount',
            'is_active',
            'conditions'
        ]
        read_only_fields = fields


class DeltaProductSerializer(serializers.ModelSerializer):
    """Serializer for Delta products."""
    
    formatted_price = serializers.CharField(read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    
    class Meta:
        model = DeltaProduct
        fields = [
            'id',
            'name',
            'description',
            'product_type',
            'product_type_display',
            'price',
            'formatted_price',
            'is_available',
            'is_limited',
            'quantity_available',
            'icon',
            'metadata',
            'created_at'
        ]
        read_only_fields = fields


class DeltaPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for Delta purchases."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_data = DeltaProductSerializer(source='product', read_only=True)
    transaction_data = DeltaTransactionSerializer(source='transaction', read_only=True)
    
    class Meta:
        model = DeltaPurchase
        fields = [
            'id',
            'user_email',
            'product_name',
            'product_data',
            'transaction_data',
            'quantity',
            'total_price',
            'is_active',
            'purchased_at'
        ]
        read_only_fields = fields

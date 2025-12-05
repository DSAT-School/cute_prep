"""
Delta Coin API Views

RESTful API endpoints for Delta coin operations.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.db.models import Q
from .services_delta import DeltaService
from .serializers_delta import (
    DeltaWalletSerializer,
    DeltaTransactionSerializer,
    DeltaProductSerializer,
    DeltaPurchaseSerializer
)
from .models_delta import DeltaWallet, DeltaTransaction, DeltaProduct, DeltaPurchase


class DeltaPagination(PageNumberPagination):
    """Pagination for Delta endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """
    Get user's current Delta balance and wallet info.
    
    GET /api/delta/balance/
    
    Returns:
        {
            "balance": "1000.00",
            "formatted_balance": "1000.00 Δ",
            "total_earned": "1500.00",
            "total_spent": "500.00",
            "is_active": true,
            "is_frozen": false
        }
    """
    try:
        summary = DeltaService.get_wallet_summary(request.user)
        
        return Response({
            'balance': str(summary['balance']),
            'formatted_balance': summary['formatted_balance'],
            'total_earned': str(summary['total_earned']),
            'total_spent': str(summary['total_spent']),
            'is_active': summary['is_active'],
            'is_frozen': summary['is_frozen'],
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_history(request):
    """
    Get user's Delta transaction history.
    
    GET /api/delta/transactions/
    
    Query params:
        - page: Page number
        - page_size: Results per page
        - type: Filter by transaction type
        - start_date: Filter from date
        - end_date: Filter to date
    
    Returns paginated list of transactions.
    """
    try:
        wallet = DeltaService.get_or_create_wallet(request.user)
        
        # Base queryset
        transactions = DeltaTransaction.objects.filter(wallet=wallet)
        
        # Filters
        tx_type = request.query_params.get('type')
        if tx_type:
            transactions = transactions.filter(transaction_type=tx_type)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        
        end_date = request.query_params.get('end_date')
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        # Paginate
        paginator = DeltaPagination()
        page = paginator.paginate_queryset(transactions, request)
        
        serializer = DeltaTransactionSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_details(request):
    """
    Get comprehensive wallet details including recent transactions.
    
    GET /api/delta/wallet/
    """
    try:
        summary = DeltaService.get_wallet_summary(request.user)
        wallet_data = DeltaWalletSerializer(summary['wallet']).data
        recent_tx = DeltaTransactionSerializer(summary['recent_transactions'], many=True).data
        
        return Response({
            'wallet': wallet_data,
            'recent_transactions': recent_tx,
            'total_transactions': summary['total_transactions']
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_delta(request):
    """
    Transfer Delta to another user.
    
    POST /api/delta/transfer/
    
    Body:
        {
            "recipient_email": "user@example.com",
            "amount": "50.00",
            "description": "Optional message"
        }
    """
    try:
        recipient_email = request.data.get('recipient_email')
        amount = request.data.get('amount')
        description = request.data.get('description', 'Delta transfer')
        
        if not recipient_email or not amount:
            return Response(
                {'error': 'recipient_email and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find recipient
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            recipient = User.objects.get(email=recipient_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Recipient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Perform transfer
        sender_tx, recipient_tx = DeltaService.transfer_delta(
            from_user=request.user,
            to_user=recipient,
            amount=amount,
            description=description
        )
        
        return Response({
            'success': True,
            'message': f'Transferred {amount} Δ to {recipient_email}',
            'sender_transaction': DeltaTransactionSerializer(sender_tx).data,
            'recipient_transaction': DeltaTransactionSerializer(recipient_tx).data
        })
        
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_products(request):
    """
    List available Delta products.
    
    GET /api/delta/products/
    
    Query params:
        - type: Filter by product type
        - available: Filter by availability (true/false)
    """
    try:
        products = DeltaProduct.objects.filter(is_available=True)
        
        # Filters
        product_type = request.query_params.get('type')
        if product_type:
            products = products.filter(product_type=product_type)
        
        serializer = DeltaProductSerializer(products, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_product(request):
    """
    Purchase a product with Delta coins.
    
    POST /api/delta/purchase/
    
    Body:
        {
            "product_id": "uuid",
            "quantity": 1
        }
    """
    try:
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        purchase = DeltaService.purchase_product(
            user=request.user,
            product_id=product_id,
            quantity=quantity
        )
        
        serializer = DeltaPurchaseSerializer(purchase)
        
        return Response({
            'success': True,
            'message': 'Purchase completed successfully',
            'purchase': serializer.data
        })
        
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_purchase_history(request):
    """
    Get user's purchase history.
    
    GET /api/delta/purchases/
    """
    try:
        purchases = DeltaPurchase.objects.filter(user=request.user)
        
        paginator = DeltaPagination()
        page = paginator.paginate_queryset(purchases, request)
        
        serializer = DeltaPurchaseSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leaderboard(request):
    """
    Get Delta leaderboard (top earners).
    
    GET /api/delta/leaderboard/
    
    Query params:
        - limit: Number of users to return (default: 10)
    """
    try:
        limit = int(request.query_params.get('limit', 10))
        
        # Get top wallets by total earned
        top_wallets = DeltaWallet.objects.filter(
            is_active=True
        ).select_related('user').order_by('-total_earned')[:limit]
        
        leaderboard = []
        for idx, wallet in enumerate(top_wallets, start=1):
            leaderboard.append({
                'rank': idx,
                'user_email': wallet.user.email,
                'total_earned': str(wallet.total_earned),
                'current_balance': str(wallet.balance),
                'is_current_user': wallet.user == request.user
            })
        
        return Response(leaderboard)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

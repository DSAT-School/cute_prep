"""
Delta Coin Service Layer

Secure business logic for Delta coin operations.
All methods use database transactions for atomicity.
"""
from decimal import Decimal
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models_delta import (
    DeltaWallet,
    DeltaTransaction,
    DeltaEarningRule,
    DeltaProduct,
    DeltaPurchase
)


class DeltaService:
    """Service class for Delta coin operations."""
    
    @staticmethod
    def get_or_create_wallet(user):
        """
        Get or create wallet for user.
        
        Args:
            user: User instance
            
        Returns:
            DeltaWallet instance
        """
        wallet, created = DeltaWallet.objects.get_or_create(
            user=user,
            defaults={
                'balance': Decimal('0.00'),
                'is_active': True
            }
        )
        return wallet
    
    @staticmethod
    @db_transaction.atomic
    def add_delta(
        user,
        amount,
        transaction_type='earn',
        description='',
        reference_id=None,
        reference_type=None,
        metadata=None,
        created_by=None
    ):
        """
        Add Delta to user's wallet (atomic operation).
        
        Args:
            user: User instance
            amount: Decimal amount to add
            transaction_type: Type of transaction
            description: Transaction description
            reference_id: Optional external reference
            reference_type: Type of reference
            metadata: Additional data dict
            created_by: User who created transaction (for admin)
            
        Returns:
            DeltaTransaction instance
            
        Raises:
            ValidationError: If wallet is frozen or inactive
        """
        # Convert to Decimal
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        
        # Get wallet with lock to prevent race conditions
        wallet = DeltaWallet.objects.select_for_update().get(user=user)
        
        # Validate wallet status
        if not wallet.is_active:
            raise ValidationError("Wallet is not active")
        if wallet.is_frozen:
            raise ValidationError("Wallet is frozen")
        
        # Record balance before
        balance_before = wallet.balance
        
        # Update wallet
        wallet.balance += amount
        wallet.total_earned += amount
        wallet.save(update_fields=['balance', 'total_earned', 'updated_at'])
        
        # Create transaction record
        transaction = DeltaTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            status='completed',
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            metadata=metadata or {},
            created_by=created_by
        )
        
        return transaction
    
    @staticmethod
    @db_transaction.atomic
    def deduct_delta(
        user,
        amount,
        transaction_type='spend',
        description='',
        reference_id=None,
        reference_type=None,
        metadata=None,
        created_by=None
    ):
        """
        Deduct Delta from user's wallet (atomic operation).
        
        Args:
            user: User instance
            amount: Decimal amount to deduct
            transaction_type: Type of transaction
            description: Transaction description
            reference_id: Optional external reference
            reference_type: Type of reference
            metadata: Additional data dict
            created_by: User who created transaction (for admin)
            
        Returns:
            DeltaTransaction instance
            
        Raises:
            ValidationError: If insufficient balance, wallet frozen, etc.
        """
        # Convert to Decimal
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        
        # Get wallet with lock
        wallet = DeltaWallet.objects.select_for_update().get(user=user)
        
        # Validate wallet status
        if not wallet.is_active:
            raise ValidationError("Wallet is not active")
        if wallet.is_frozen:
            raise ValidationError("Wallet is frozen")
        
        # Check sufficient balance
        if wallet.balance < amount:
            raise ValidationError(f"Insufficient balance. Have {wallet.balance} Δ, need {amount} Δ")
        
        # Record balance before
        balance_before = wallet.balance
        
        # Update wallet
        wallet.balance -= amount
        wallet.total_spent += amount
        wallet.save(update_fields=['balance', 'total_spent', 'updated_at'])
        
        # Create transaction record
        transaction = DeltaTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            status='completed',
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            metadata=metadata or {},
            created_by=created_by
        )
        
        return transaction
    
    @staticmethod
    @db_transaction.atomic
    def transfer_delta(from_user, to_user, amount, description='Transfer'):
        """
        Transfer Delta between users (atomic operation).
        
        Args:
            from_user: Sender user
            to_user: Recipient user
            amount: Amount to transfer
            description: Transfer description
            
        Returns:
            tuple: (sender_transaction, recipient_transaction)
            
        Raises:
            ValidationError: If transfer fails
        """
        amount = Decimal(str(amount))
        
        if from_user == to_user:
            raise ValidationError("Cannot transfer to yourself")
        
        # Deduct from sender
        sender_tx = DeltaService.deduct_delta(
            user=from_user,
            amount=amount,
            transaction_type='transfer',
            description=f"{description} (sent to {to_user.email})",
            metadata={'to_user_id': str(to_user.id)}
        )
        
        try:
            # Add to recipient
            recipient_tx = DeltaService.add_delta(
                user=to_user,
                amount=amount,
                transaction_type='transfer',
                description=f"{description} (received from {from_user.email})",
                metadata={'from_user_id': str(from_user.id)}
            )
            
            # Link transactions
            sender_tx.related_user = to_user
            sender_tx.save(update_fields=['related_user'])
            
            recipient_tx.related_user = from_user
            recipient_tx.save(update_fields=['related_user'])
            
            return (sender_tx, recipient_tx)
            
        except Exception as e:
            # If recipient transaction fails, we need to refund sender
            # The atomic decorator will roll back the entire transaction
            raise ValidationError(f"Transfer failed: {str(e)}")
    
    @staticmethod
    @db_transaction.atomic
    def reverse_transaction(transaction, reason='', reversed_by_user=None):
        """
        Reverse a transaction (refund/undo).
        
        Args:
            transaction: DeltaTransaction to reverse
            reason: Reason for reversal
            reversed_by_user: Admin user performing reversal
            
        Returns:
            DeltaTransaction: Reversal transaction
            
        Raises:
            ValidationError: If transaction cannot be reversed
        """
        if transaction.is_reversed:
            raise ValidationError("Transaction already reversed")
        
        if transaction.status != 'completed':
            raise ValidationError("Can only reverse completed transactions")
        
        wallet = transaction.wallet
        
        # Determine reversal operation
        if transaction.transaction_type in ['earn', 'bonus', 'admin_add', 'transfer']:
            # These added Delta, so reverse by deducting
            reversal_tx = DeltaService.deduct_delta(
                user=wallet.user,
                amount=transaction.amount,
                transaction_type='reversal',
                description=f"Reversal: {transaction.description}. Reason: {reason}",
                reference_id=str(transaction.id),
                reference_type='transaction_reversal',
                metadata={'original_tx_id': str(transaction.id), 'reason': reason},
                created_by=reversed_by_user
            )
        else:
            # These deducted Delta, so reverse by adding
            reversal_tx = DeltaService.add_delta(
                user=wallet.user,
                amount=transaction.amount,
                transaction_type='reversal',
                description=f"Reversal: {transaction.description}. Reason: {reason}",
                reference_id=str(transaction.id),
                reference_type='transaction_reversal',
                metadata={'original_tx_id': str(transaction.id), 'reason': reason},
                created_by=reversed_by_user
            )
        
        # Mark original as reversed
        transaction.is_reversed = True
        transaction.reversed_by = reversal_tx
        transaction.save(update_fields=['is_reversed', 'reversed_by'])
        
        return reversal_tx
    
    @staticmethod
    def award_for_activity(user, activity_name, **kwargs):
        """
        Award Delta based on earning rule.
        
        Args:
            user: User to award
            activity_name: Name of earning rule
            **kwargs: Additional context for transaction
            
        Returns:
            DeltaTransaction or None
        """
        try:
            rule = DeltaEarningRule.objects.get(name=activity_name, is_active=True)
            
            # Check conditions if any
            conditions = rule.conditions
            if conditions:
                # Example: check minimum accuracy
                if 'min_accuracy' in conditions:
                    accuracy = kwargs.get('accuracy', 0)
                    if accuracy < conditions['min_accuracy']:
                        return None
            
            transaction = DeltaService.add_delta(
                user=user,
                amount=rule.amount,
                transaction_type='earn',
                description=rule.description,
                reference_id=kwargs.get('reference_id'),
                reference_type=kwargs.get('reference_type'),
                metadata=kwargs.get('metadata', {})
            )
            
            return transaction
            
        except DeltaEarningRule.DoesNotExist:
            # No rule found, don't award
            return None
    
    @staticmethod
    @db_transaction.atomic
    def purchase_product(user, product_id, quantity=1):
        """
        Purchase a product with Delta coins.
        
        Args:
            user: User making purchase
            product_id: Product UUID
            quantity: Quantity to purchase
            
        Returns:
            DeltaPurchase instance
            
        Raises:
            ValidationError: If purchase fails
        """
        # Get product with lock if limited
        if DeltaProduct.objects.filter(id=product_id, is_limited=True).exists():
            product = DeltaProduct.objects.select_for_update().get(id=product_id)
        else:
            product = DeltaProduct.objects.get(id=product_id)
        
        # Validate product availability
        if not product.is_available:
            raise ValidationError("Product is not available")
        
        if product.is_limited:
            if not product.quantity_available or product.quantity_available < quantity:
                raise ValidationError("Insufficient product quantity available")
        
        # Calculate total price
        total_price = product.price * quantity
        
        # Deduct Delta
        transaction = DeltaService.deduct_delta(
            user=user,
            amount=total_price,
            transaction_type='spend',
            description=f"Purchased {product.name} x{quantity}",
            reference_id=str(product.id),
            reference_type='product_purchase',
            metadata={
                'product_id': str(product.id),
                'product_name': product.name,
                'quantity': quantity,
                'unit_price': str(product.price)
            }
        )
        
        # Create purchase record
        purchase = DeltaPurchase.objects.create(
            user=user,
            product=product,
            transaction=transaction,
            quantity=quantity,
            total_price=total_price
        )
        
        # Update product quantity if limited
        if product.is_limited:
            product.quantity_available -= quantity
            if product.quantity_available <= 0:
                product.is_available = False
            product.save(update_fields=['quantity_available', 'is_available'])
        
        return purchase
    
    @staticmethod
    def get_wallet_summary(user):
        """
        Get comprehensive wallet summary.
        
        Args:
            user: User instance
            
        Returns:
            dict: Wallet summary with stats
        """
        wallet = DeltaService.get_or_create_wallet(user)
        
        # Get transaction stats
        recent_transactions = DeltaTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:10]
        
        total_transactions = DeltaTransaction.objects.filter(wallet=wallet).count()
        
        return {
            'wallet': wallet,
            'balance': wallet.balance,
            'formatted_balance': wallet.formatted_balance,
            'total_earned': wallet.total_earned,
            'total_spent': wallet.total_spent,
            'total_transactions': total_transactions,
            'recent_transactions': recent_transactions,
            'is_active': wallet.is_active,
            'is_frozen': wallet.is_frozen,
        }

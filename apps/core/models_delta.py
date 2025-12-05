"""
Delta Coin System Models

Secure and scalable virtual currency system for DSAT SCHOOL platform.
Features:
- Wallet management
- Transaction tracking with audit trail
- Transaction types (earn, spend, transfer, refund, admin_adjustment)
- Balance validation and atomic operations
- Transaction reversal support
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class DeltaWallet(models.Model):
    """
    User's Delta coin wallet.
    
    Each user has one wallet containing their Delta balance.
    Uses decimal for precise currency handling.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique wallet identifier")
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delta_wallet',
        help_text=_("Wallet owner")
    )
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Current Delta balance (cannot be negative)")
    )
    total_earned = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Total Deltas earned lifetime")
    )
    total_spent = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Total Deltas spent lifetime")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether wallet is active")
    )
    is_frozen = models.BooleanField(
        default=False,
        help_text=_("If true, no transactions allowed (for security)")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Wallet creation timestamp")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Last update timestamp")
    )
    
    class Meta:
        db_table = 'delta_wallets'
        verbose_name = _("Delta Wallet")
        verbose_name_plural = _("Delta Wallets")
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.balance} Δ"
    
    @property
    def formatted_balance(self):
        """Return formatted balance with Delta symbol."""
        return f"{self.balance} Δ"


class DeltaTransaction(models.Model):
    """
    Record of Delta coin transaction.
    
    All transactions are immutable once created for audit purposes.
    Supports various transaction types and includes complete audit trail.
    """
    
    TRANSACTION_TYPES = [
        ('earn', _('Earn')),           # User earned Delta (e.g., completing practice)
        ('spend', _('Spend')),         # User spent Delta (e.g., purchasing items)
        ('transfer', _('Transfer')),   # Transfer between users
        ('refund', _('Refund')),       # Refund transaction
        ('bonus', _('Bonus')),         # Bonus/reward from system
        ('admin_add', _('Admin Add')), # Admin added Delta
        ('admin_deduct', _('Admin Deduct')), # Admin removed Delta
        ('reversal', _('Reversal')),   # Transaction reversal
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('reversed', _('Reversed')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique transaction identifier")
    )
    wallet = models.ForeignKey(
        DeltaWallet,
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text=_("Wallet involved in transaction")
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        help_text=_("Type of transaction")
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Transaction amount (always positive)")
    )
    balance_before = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text=_("Wallet balance before transaction")
    )
    balance_after = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text=_("Wallet balance after transaction")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text=_("Transaction status")
    )
    
    # Optional fields for different transaction contexts
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delta_related_transactions',
        help_text=_("Related user (for transfers)")
    )
    reference_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("External reference ID (e.g., practice session ID, purchase ID)")
    )
    reference_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text=_("Type of reference (e.g., 'practice_session', 'store_purchase')")
    )
    description = models.TextField(
        help_text=_("Transaction description")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional transaction metadata")
    )
    
    # Reversal tracking
    is_reversed = models.BooleanField(
        default=False,
        help_text=_("Whether this transaction has been reversed")
    )
    reversed_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversed_transaction',
        help_text=_("Reversal transaction reference")
    )
    
    # Admin tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delta_transactions_created',
        help_text=_("User who created this transaction (for admin actions)")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("Transaction timestamp")
    )
    
    class Meta:
        db_table = 'delta_transactions'
        verbose_name = _("Delta Transaction")
        verbose_name_plural = _("Delta Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['reference_id', 'reference_type']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} Δ - {self.wallet.user.email}"
    
    @property
    def formatted_amount(self):
        """Return formatted amount with Delta symbol."""
        return f"{self.amount} Δ"


class DeltaEarningRule(models.Model):
    """
    Rules for earning Delta coins.
    
    Defines how many Deltas users earn for different activities.
    Allows easy configuration without code changes.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_("Rule name (e.g., 'correct_answer', 'complete_practice')")
    )
    description = models.TextField(
        help_text=_("Description of earning rule")
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Delta amount to award")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this rule is currently active")
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Optional conditions for earning (e.g., minimum accuracy)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'delta_earning_rules'
        verbose_name = _("Delta Earning Rule")
        verbose_name_plural = _("Delta Earning Rules")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.amount} Δ"


class DeltaProduct(models.Model):
    """
    Products/items that can be purchased with Delta coins.
    
    Could be features, content, badges, etc.
    """
    
    PRODUCT_TYPES = [
        ('feature', _('Feature')),
        ('content', _('Content')),
        ('badge', _('Badge')),
        ('boost', _('Boost')),
        ('cosmetic', _('Cosmetic')),
        ('other', _('Other')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=200,
        help_text=_("Product name")
    )
    description = models.TextField(
        help_text=_("Product description")
    )
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        help_text=_("Type of product")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_("Price in Delta coins")
    )
    is_available = models.BooleanField(
        default=True,
        help_text=_("Whether product is available for purchase")
    )
    is_limited = models.BooleanField(
        default=False,
        help_text=_("Whether product has limited quantity")
    )
    quantity_available = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Available quantity (for limited products)")
    )
    icon = models.CharField(
        max_length=100,
        default='fas fa-star',
        help_text=_("Font Awesome icon class")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional product data")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'delta_products'
        verbose_name = _("Delta Product")
        verbose_name_plural = _("Delta Products")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.price} Δ"
    
    @property
    def formatted_price(self):
        """Return formatted price with Delta symbol."""
        return f"{self.price} Δ"


class DeltaPurchase(models.Model):
    """
    Record of Delta product purchases.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delta_purchases'
    )
    product = models.ForeignKey(
        DeltaProduct,
        on_delete=models.PROTECT,
        related_name='purchases'
    )
    transaction = models.OneToOneField(
        DeltaTransaction,
        on_delete=models.PROTECT,
        related_name='purchase',
        help_text=_("Associated Delta transaction")
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether purchase is active/valid")
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'delta_purchases'
        verbose_name = _("Delta Purchase")
        verbose_name_plural = _("Delta Purchases")
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['user', '-purchased_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"

"""
Delta Coin Admin Interface

Django admin configuration for Delta coin system.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models_delta import (
    DeltaWallet,
    DeltaTransaction,
    DeltaEarningRule,
    DeltaProduct,
    DeltaPurchase
)


@admin.register(DeltaWallet)
class DeltaWalletAdmin(admin.ModelAdmin):
    """Admin interface for Delta wallets."""
    
    list_display = [
        'user_email',
        'balance_display',
        'total_earned_display',
        'total_spent_display',
        'status_badge',
        'created_at'
    ]
    list_filter = ['is_active', 'is_frozen', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'transaction_history_link']
    
    fieldsets = (
        ('User Information', {
            'fields': ('id', 'user', 'transaction_history_link')
        }),
        ('Balance', {
            'fields': ('balance', 'total_earned', 'total_spent')
        }),
        ('Status', {
            'fields': ('is_active', 'is_frozen')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def balance_display(self, obj):
        return format_html('<strong style="color: #9967b9;">{} Δ</strong>', obj.balance)
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'balance'
    
    def total_earned_display(self, obj):
        return format_html('<span style="color: green;">{} Δ</span>', obj.total_earned)
    total_earned_display.short_description = 'Total Earned'
    
    def total_spent_display(self, obj):
        return format_html('<span style="color: #fdcc4c;">{} Δ</span>', obj.total_spent)
    total_spent_display.short_description = 'Total Spent'
    
    def status_badge(self, obj):
        if obj.is_frozen:
            return format_html('<span style="color: red; font-weight: bold;">FROZEN</span>')
        elif not obj.is_active:
            return format_html('<span style="color: gray;">INACTIVE</span>')
        else:
            return format_html('<span style="color: green;">ACTIVE</span>')
    status_badge.short_description = 'Status'
    
    def transaction_history_link(self, obj):
        if obj.pk:
            url = reverse('admin:core_deltatransaction_changelist') + f'?wallet__id__exact={obj.id}'
            return format_html('<a href="{}" target="_blank">View Transactions</a>', url)
        return '-'
    transaction_history_link.short_description = 'Transactions'
    
    actions = ['freeze_wallets', 'unfreeze_wallets', 'deactivate_wallets', 'activate_wallets']
    
    def freeze_wallets(self, request, queryset):
        updated = queryset.update(is_frozen=True)
        self.message_user(request, f'{updated} wallet(s) frozen.')
    freeze_wallets.short_description = 'Freeze selected wallets'
    
    def unfreeze_wallets(self, request, queryset):
        updated = queryset.update(is_frozen=False)
        self.message_user(request, f'{updated} wallet(s) unfrozen.')
    unfreeze_wallets.short_description = 'Unfreeze selected wallets'
    
    def deactivate_wallets(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} wallet(s) deactivated.')
    deactivate_wallets.short_description = 'Deactivate selected wallets'
    
    def activate_wallets(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} wallet(s) activated.')
    activate_wallets.short_description = 'Activate selected wallets'


@admin.register(DeltaTransaction)
class DeltaTransactionAdmin(admin.ModelAdmin):
    """Admin interface for Delta transactions."""
    
    list_display = [
        'id_short',
        'wallet_user',
        'type_badge',
        'amount_display',
        'balance_change',
        'status_badge',
        'created_at'
    ]
    list_filter = [
        'transaction_type',
        'status',
        'is_reversed',
        'created_at'
    ]
    search_fields = [
        'wallet__user__email',
        'description',
        'reference_id'
    ]
    readonly_fields = [
        'id',
        'wallet',
        'transaction_type',
        'amount',
        'balance_before',
        'balance_after',
        'status',
        'related_user',
        'reference_id',
        'reference_type',
        'description',
        'metadata',
        'is_reversed',
        'reversed_by',
        'created_by',
        'created_at'
    ]
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'id',
                'wallet',
                'transaction_type',
                'amount',
                'status'
            )
        }),
        ('Balance Information', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('References', {
            'fields': ('related_user', 'reference_id', 'reference_type')
        }),
        ('Description & Metadata', {
            'fields': ('description', 'metadata')
        }),
        ('Reversal Information', {
            'fields': ('is_reversed', 'reversed_by')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at')
        })
    )
    
    def has_add_permission(self, request):
        # Transactions should only be created through service layer
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Transactions are immutable for audit purposes
        return False
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def wallet_user(self, obj):
        return obj.wallet.user.email
    wallet_user.short_description = 'User'
    wallet_user.admin_order_field = 'wallet__user__email'
    
    def type_badge(self, obj):
        colors = {
            'earn': 'green',
            'spend': '#fdcc4c',
            'transfer': 'blue',
            'refund': 'purple',
            'bonus': 'green',
            'admin_add': 'darkgreen',
            'admin_deduct': 'red',
            'reversal': 'gray'
        }
        color = colors.get(obj.transaction_type, 'black')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    type_badge.short_description = 'Type'
    
    def amount_display(self, obj):
        return format_html('<strong>{} Δ</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def balance_change(self, obj):
        change = obj.balance_after - obj.balance_before
        color = 'green' if change > 0 else '#fdcc4c'
        symbol = '+' if change > 0 else ''
        return format_html('<span style="color: {};">{}{} Δ</span>', color, symbol, change)
    balance_change.short_description = 'Change'
    
    def status_badge(self, obj):
        colors = {
            'completed': 'green',
            'pending': 'orange',
            'failed': 'red',
            'reversed': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_badge.short_description = 'Status'


@admin.register(DeltaEarningRule)
class DeltaEarningRuleAdmin(admin.ModelAdmin):
    """Admin interface for earning rules."""
    
    list_display = ['name', 'amount_display', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('name', 'description', 'amount')
        }),
        ('Configuration', {
            'fields': ('is_active', 'conditions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def amount_display(self, obj):
        return format_html('<strong style="color: #9967b9;">{} Δ</strong>', obj.amount)
    amount_display.short_description = 'Award Amount'
    
    actions = ['activate_rules', 'deactivate_rules']
    
    def activate_rules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} rule(s) activated.')
    activate_rules.short_description = 'Activate selected rules'
    
    def deactivate_rules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} rule(s) deactivated.')
    deactivate_rules.short_description = 'Deactivate selected rules'


@admin.register(DeltaProduct)
class DeltaProductAdmin(admin.ModelAdmin):
    """Admin interface for Delta products."""
    
    list_display = [
        'name',
        'product_type',
        'price_display',
        'availability_badge',
        'quantity_status',
        'created_at'
    ]
    list_filter = ['product_type', 'is_available', 'is_limited', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'product_type', 'icon')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available', 'is_limited', 'quantity_available')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def price_display(self, obj):
        return format_html('<strong style="color: #9967b9;">{} Δ</strong>', obj.price)
    price_display.short_description = 'Price'
    
    def availability_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green; font-weight: bold;">AVAILABLE</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">UNAVAILABLE</span>')
    availability_badge.short_description = 'Status'
    
    def quantity_status(self, obj):
        if not obj.is_limited:
            return format_html('<span style="color: gray;">Unlimited</span>')
        elif obj.quantity_available and obj.quantity_available > 0:
            return format_html('<span style="color: green;">{} left</span>', obj.quantity_available)
        else:
            return format_html('<span style="color: red;">Out of stock</span>')
    quantity_status.short_description = 'Quantity'
    
    actions = ['make_available', 'make_unavailable']
    
    def make_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} product(s) made available.')
    make_available.short_description = 'Make available'
    
    def make_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} product(s) made unavailable.')
    make_unavailable.short_description = 'Make unavailable'


@admin.register(DeltaPurchase)
class DeltaPurchaseAdmin(admin.ModelAdmin):
    """Admin interface for Delta purchases."""
    
    list_display = [
        'id_short',
        'user_email',
        'product_name',
        'quantity',
        'total_price_display',
        'is_active',
        'purchased_at'
    ]
    list_filter = ['is_active', 'purchased_at', 'product__product_type']
    search_fields = ['user__email', 'product__name']
    readonly_fields = [
        'id',
        'user',
        'product',
        'transaction',
        'quantity',
        'total_price',
        'purchased_at'
    ]
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('id', 'user', 'product', 'quantity', 'total_price')
        }),
        ('Transaction', {
            'fields': ('transaction',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamp', {
            'fields': ('purchased_at',)
        })
    )
    
    def has_add_permission(self, request):
        # Purchases should only be created through service layer
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Purchases are immutable
        return False
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Product'
    
    def total_price_display(self, obj):
        return format_html('<strong style="color: #9967b9;">{} Δ</strong>', obj.total_price)
    total_price_display.short_description = 'Total Price'
    
    actions = ['deactivate_purchases', 'activate_purchases']
    
    def deactivate_purchases(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} purchase(s) deactivated.')
    deactivate_purchases.short_description = 'Deactivate purchases'
    
    def activate_purchases(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} purchase(s) activated.')
    activate_purchases.short_description = 'Activate purchases'

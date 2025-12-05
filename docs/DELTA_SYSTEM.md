# Delta Coin System Documentation

## Overview

The Delta Coin System is DSAT SCHOOL's virtual currency platform that rewards users for engagement and allows them to purchase premium features, content, and benefits.

**Key Features:**
- ✅ Secure wallet management with atomic transactions
- ✅ Comprehensive transaction audit trail
- ✅ Automatic rewards for practice activities
- ✅ Product marketplace for premium features
- ✅ Transfer system between users
- ✅ Admin dashboard for monitoring and management
- ✅ RESTful API for all operations
- ✅ Real-time balance updates in navbar

---

## Architecture

### Components

1. **Models** (`apps/core/models_delta.py`)
   - `DeltaWallet`: User's coin balance and lifetime stats
   - `DeltaTransaction`: Immutable transaction records
   - `DeltaEarningRule`: Configurable earning rules
   - `DeltaProduct`: Store items for purchase
   - `DeltaPurchase`: Purchase history records

2. **Service Layer** (`apps/core/services_delta.py`)
   - Business logic for all Delta operations
   - Atomic database transactions for consistency
   - Balance validation and security checks

3. **API Views** (`apps/core/views_delta.py`)
   - RESTful endpoints for Delta operations
   - DRF-based with pagination
   - Authentication required

4. **Admin Interface** (`apps/core/admin_delta.py`)
   - Comprehensive management tools
   - Read-only transaction history
   - Wallet freeze/unfreeze capabilities

5. **Frontend Components**
   - Navbar balance widget (auto-updates)
   - Delta Store page
   - Earning notifications
   - Purchase confirmation modals

---

## Database Schema

### DeltaWallet
```python
- id (UUID, PK)
- user (FK → User, OneToOne)
- balance (Decimal, ≥0)
- total_earned (Decimal)
- total_spent (Decimal)
- is_active (Boolean)
- is_frozen (Boolean)
- created_at (DateTime)
- updated_at (DateTime)
```

### DeltaTransaction
```python
- id (UUID, PK)
- wallet (FK → DeltaWallet)
- transaction_type (Choice: earn, spend, transfer, bonus, admin_add, etc.)
- amount (Decimal, >0)
- balance_before (Decimal)
- balance_after (Decimal)
- status (Choice: pending, completed, failed, reversed)
- related_user (FK → User, nullable)
- reference_id (String, indexed)
- reference_type (String)
- description (Text)
- metadata (JSON)
- is_reversed (Boolean)
- reversed_by (FK → self)
- created_by (FK → User, nullable)
- created_at (DateTime, indexed)
```

### DeltaEarningRule
```python
- id (UUID, PK)
- name (String, unique)
- description (Text)
- amount (Decimal)
- is_active (Boolean)
- conditions (JSON)
- created_at (DateTime)
- updated_at (DateTime)
```

### DeltaProduct
```python
- id (UUID, PK)
- name (String)
- description (Text)
- product_type (Choice: feature, content, badge, boost, etc.)
- price (Decimal)
- is_available (Boolean)
- is_limited (Boolean)
- quantity_available (Integer, nullable)
- icon (String, FontAwesome class)
- metadata (JSON)
```

### DeltaPurchase
```python
- id (UUID, PK)
- user (FK → User)
- product (FK → DeltaProduct)
- transaction (FK → DeltaTransaction, OneToOne)
- quantity (Integer, ≥1)
- total_price (Decimal)
- is_active (Boolean)
- purchased_at (DateTime)
```

---

## API Endpoints

### GET `/api/delta/balance/`
Get user's current balance and wallet info.

**Response:**
```json
{
  "balance": "1000.00",
  "formatted_balance": "1000.00 Δ",
  "total_earned": "1500.00",
  "total_spent": "500.00",
  "is_active": true,
  "is_frozen": false
}
```

### GET `/api/delta/transactions/`
Get transaction history (paginated).

**Query Params:**
- `page`: Page number
- `page_size`: Results per page (max 100)
- `type`: Filter by transaction type
- `start_date`: Filter from date
- `end_date`: Filter to date

**Response:**
```json
{
  "count": 50,
  "next": "...",
  "previous": null,
  "results": [...]
}
```

### GET `/api/delta/wallet/`
Get comprehensive wallet details with recent transactions.

### POST `/api/delta/transfer/`
Transfer Delta to another user.

**Body:**
```json
{
  "recipient_email": "user@example.com",
  "amount": "50.00",
  "description": "Optional message"
}
```

### GET `/api/delta/products/`
List available products.

**Query Params:**
- `type`: Filter by product type

### POST `/api/delta/purchase/`
Purchase a product.

**Body:**
```json
{
  "product_id": "uuid",
  "quantity": 1
}
```

### GET `/api/delta/leaderboard/`
Get top Delta earners.

**Query Params:**
- `limit`: Number of users (default: 10)

---

## Service Layer Usage

### Award Delta for Activity
```python
from apps.core.services_delta import DeltaService

# Award based on earning rule
transaction = DeltaService.award_for_activity(
    user=user,
    activity_name='complete_practice_session',
    reference_id=str(session.id),
    reference_type='practice_session',
    accuracy=85.5  # Optional metadata
)
```

### Add Delta Manually
```python
from decimal import Decimal

transaction = DeltaService.add_delta(
    user=user,
    amount=Decimal('50.00'),
    transaction_type='bonus',
    description='Welcome bonus',
    metadata={'reason': 'signup'}
)
```

### Deduct Delta
```python
transaction = DeltaService.deduct_delta(
    user=user,
    amount=Decimal('100.00'),
    transaction_type='spend',
    description='Purchased premium feature'
)
```

### Transfer Between Users
```python
sender_tx, recipient_tx = DeltaService.transfer_delta(
    from_user=sender,
    to_user=recipient,
    amount=Decimal('25.00'),
    description='Gift'
)
```

### Purchase Product
```python
purchase = DeltaService.purchase_product(
    user=user,
    product_id=product_uuid,
    quantity=1
)
```

### Reverse Transaction
```python
reversal_tx = DeltaService.reverse_transaction(
    transaction=original_tx,
    reason='Refund requested',
    reversed_by_user=admin_user
)
```

---

## Earning Rules (Default)

| Activity | Amount | Conditions |
|----------|--------|------------|
| Daily Login | 10 Δ | First login of the day |
| Complete Practice Session | 20 Δ | Any completion |
| Correct Answer | 5 Δ | Per correct answer |
| Perfect Practice (100%) | 50 Δ | Accuracy = 100% |
| High Accuracy Practice (80%+) | 30 Δ | Accuracy ≥ 80% |
| First Practice Ever | 100 Δ | One-time bonus |
| 3-Day Streak | 50 Δ | Practice 3 days in a row |
| 7-Day Streak | 100 Δ | Practice 7 days in a row |
| Complete Profile | 25 Δ | Fill out profile info |
| Refer Friend | 100 Δ | Friend completes signup |

**Manage Rules:**
```bash
python manage.py setup_delta_rules
```

---

## Integration with Practice System

Delta rewards are automatically awarded when a practice session is completed:

**In `apps/practice/views.py` → `end_practice()`:**
```python
# Awards:
# - First practice bonus (if applicable): 100 Δ
# - Perfect practice (100%): 50 Δ
# - High accuracy (80%+): 30 Δ
# - Complete session: 20 Δ
# - Per correct answer: 5 Δ each
```

Results page shows earned Delta with animated banner.

---

## Frontend Components

### Navbar Balance Widget
Located in `templates/components/navbar.html`:
- Real-time balance display
- Gradient background (primary → secondary)
- Auto-loads on page load
- Refreshes after earning Delta

### Delta Store
Located at `/delta/store/`:
- Browse available products
- Purchase with Delta coins
- View transaction history
- Real-time balance updates

### Earning Notifications
Shown on results page after practice:
- Animated banner with earned amount
- Auto-refreshes navbar balance
- Dismissible notification

---

## Admin Management

### Django Admin Interface
Access at `/admin/`:

**Delta Wallets:**
- View all user wallets
- Freeze/unfreeze wallets
- Activate/deactivate wallets
- View transaction history per wallet

**Delta Transactions:**
- Read-only transaction log
- Filter by type, status, date
- View balance changes
- Cannot delete (audit trail)

**Delta Earning Rules:**
- Create/edit earning rules
- Set amounts and conditions
- Activate/deactivate rules
- No code deployment needed

**Delta Products:**
- Add products to store
- Set pricing and availability
- Manage limited quantity items
- Configure icons and metadata

**Delta Purchases:**
- View purchase history
- Deactivate/refund purchases
- Track product sales
- Read-only for audit

### Admin Actions
- **Freeze Wallets**: Prevent all transactions
- **Adjust Balances**: Use `admin_add` or `admin_deduct` transaction types
- **Reverse Transactions**: Built-in reversal system with audit trail
- **View Analytics**: Check top earners, spending patterns

---

## Security Features

1. **Atomic Transactions**: All operations use database transactions
2. **Balance Validation**: Cannot go negative
3. **Wallet Freezing**: Emergency security measure
4. **Audit Trail**: Complete immutable transaction history
5. **User Verification**: All operations verify user ownership
6. **Rate Limiting**: API endpoints support throttling
7. **CSRF Protection**: All POST requests require CSRF token

---

## Testing

Run Delta system tests:
```bash
# All tests
pytest apps/core/tests/test_delta.py -v

# Specific test
pytest apps/core/tests/test_delta.py::test_award_delta -v
```

Test coverage includes:
- Wallet creation
- Adding/deducting Delta
- Transfers between users
- Purchase flows
- Transaction reversals
- Balance validation
- Concurrency handling

---

## Management Commands

### Setup Earning Rules
```bash
python manage.py setup_delta_rules
```
Creates/updates default earning rules.

### Award Bonus to Users
```python
# Create custom command in apps/core/management/commands/
from django.core.management.base import BaseCommand
from apps.core.services_delta import DeltaService
from apps.core.models import User
from decimal import Decimal

class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.filter(is_active=True):
            DeltaService.add_delta(
                user=user,
                amount=Decimal('100.00'),
                transaction_type='bonus',
                description='Holiday bonus!'
            )
```

---

## Performance Considerations

1. **Indexing**: Key fields indexed for fast queries
2. **Select for Update**: Prevents race conditions on wallet updates
3. **Pagination**: All list endpoints paginated
4. **Caching**: Consider caching wallet balances for high traffic
5. **Background Jobs**: Large Delta distributions should use Celery

---

## Future Enhancements

- [ ] Daily login rewards (automatic)
- [ ] Achievements system with Delta rewards
- [ ] Delta gifting between friends
- [ ] Seasonal/limited-time products
- [ ] Subscription services paid with Delta
- [ ] Mini-games to earn Delta
- [ ] Donation/charity features
- [ ] Delta to real rewards conversion
- [ ] Referral program tracking
- [ ] Streak bonus multipliers

---

## Troubleshooting

### Balance Not Updating
- Check if wallet is frozen: `user.delta_wallet.is_frozen`
- Verify wallet is active: `user.delta_wallet.is_active`
- Check transaction status: Should be 'completed'

### Purchase Failing
- Verify sufficient balance
- Check product availability
- Ensure product quantity available (if limited)
- Check for validation errors in response

### Transactions Not Appearing
- Transactions are created in atomic blocks
- If error occurs, entire transaction rolls back
- Check Django logs for exceptions

### Admin Can't Delete Transactions
- By design - transactions are immutable
- Use `reverse_transaction()` for refunds
- Maintains complete audit trail

---

## Support

For issues or questions:
1. Check Django admin for transaction logs
2. Review error logs in `logs/` directory
3. Test with Django shell: `python manage.py shell`
4. Contact development team

---

## License

Part of DSAT SCHOOL Practice Portal
© 2024 DSAT SCHOOL. All rights reserved.

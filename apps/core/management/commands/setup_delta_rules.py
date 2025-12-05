"""
Management command to setup initial Delta earning rules.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.core.models_delta import DeltaEarningRule


class Command(BaseCommand):
    """Setup initial Delta earning rules."""
    
    help = 'Creates initial Delta earning rules'
    
    def handle(self, *args, **options):
        """Execute the command."""
        
        rules = [
            {
                'name': 'daily_login',
                'description': 'Login to the platform',
                'amount': Decimal('10.00'),
                'is_active': True,
                'conditions': {}
            },
            {
                'name': 'complete_practice_session',
                'description': 'Complete a practice session',
                'amount': Decimal('20.00'),
                'is_active': True,
                'conditions': {}
            },
            {
                'name': 'correct_answer',
                'description': 'Answer a question correctly',
                'amount': Decimal('5.00'),
                'is_active': True,
                'conditions': {}
            },
            {
                'name': 'perfect_practice',
                'description': 'Complete a practice session with 100% accuracy',
                'amount': Decimal('50.00'),
                'is_active': True,
                'conditions': {'min_accuracy': 100}
            },
            {
                'name': 'high_accuracy_practice',
                'description': 'Complete a practice session with 80%+ accuracy',
                'amount': Decimal('30.00'),
                'is_active': True,
                'conditions': {'min_accuracy': 80}
            },
            {
                'name': 'first_practice',
                'description': 'Complete your first practice session (bonus)',
                'amount': Decimal('100.00'),
                'is_active': True,
                'conditions': {}
            },
            {
                'name': 'weekly_streak_3',
                'description': 'Practice 3 days in a row',
                'amount': Decimal('50.00'),
                'is_active': True,
                'conditions': {'min_streak': 3}
            },
            {
                'name': 'weekly_streak_7',
                'description': 'Practice 7 days in a row',
                'amount': Decimal('100.00'),
                'is_active': True,
                'conditions': {'min_streak': 7}
            },
            {
                'name': 'profile_complete',
                'description': 'Complete your profile information',
                'amount': Decimal('25.00'),
                'is_active': True,
                'conditions': {}
            },
            {
                'name': 'refer_friend',
                'description': 'Refer a friend who completes signup',
                'amount': Decimal('100.00'),
                'is_active': True,
                'conditions': {}
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for rule_data in rules:
            rule, created = DeltaEarningRule.objects.update_or_create(
                name=rule_data['name'],
                defaults={
                    'description': rule_data['description'],
                    'amount': rule_data['amount'],
                    'is_active': rule_data['is_active'],
                    'conditions': rule_data['conditions']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created rule: {rule.name} ({rule.amount} Δ)')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated rule: {rule.name} ({rule.amount} Δ)')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Setup complete! Created {created_count} rules, updated {updated_count} rules.'
            )
        )

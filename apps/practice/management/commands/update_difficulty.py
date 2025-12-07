"""
Management command to update difficulty field for existing questions from JSON file.

Usage:
    python manage.py update_difficulty questions.json
    python manage.py update_difficulty questions.json --dry-run
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.practice.models import Question


class Command(BaseCommand):
    """Update difficulty field for existing questions."""

    help = 'Update difficulty field for existing questions from JSON file'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON file containing questions with difficulty field'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        json_file = options['json_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )

        try:
            # Load JSON data
            self.stdout.write('📖 Loading JSON file...')
            with open(json_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)

            total_questions = len(questions_data)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Loaded {total_questions} questions from file')
            )

            # Update questions
            with transaction.atomic():
                stats = self.update_difficulty(questions_data, dry_run)
                
                if dry_run:
                    raise Exception("Dry run - rolling back transaction")

        except FileNotFoundError:
            raise CommandError(f'File not found: {json_file}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')
        except Exception as e:
            if not dry_run:
                raise CommandError(f'Error updating difficulty: {e}')

        # Display statistics
        self.display_stats(stats, dry_run)

    def update_difficulty(self, questions_data, dry_run):
        """Update difficulty field for questions."""
        stats = {
            'updated': 0,
            'not_found': 0,
            'no_difficulty': 0,
            'errors': []
        }

        for idx, question_data in enumerate(questions_data, 1):
            try:
                # Progress indicator
                if idx % 100 == 0:
                    self.stdout.write(f'Processing question {idx}/{len(questions_data)}...')

                identifier_id = question_data.get('identifier_id')
                difficulty = question_data.get('difficulty')

                if not identifier_id:
                    stats['errors'].append({
                        'index': idx,
                        'error': 'Missing identifier_id'
                    })
                    continue

                if not difficulty:
                    stats['no_difficulty'] += 1
                    continue

                # Find question in database
                try:
                    question = Question.objects.get(identifier_id=identifier_id)
                    
                    if not dry_run:
                        question.difficulty = difficulty
                        question.save(update_fields=['difficulty', 'updated_at'])
                    
                    stats['updated'] += 1
                    
                except Question.DoesNotExist:
                    stats['not_found'] += 1
                    continue

            except Exception as e:
                stats['errors'].append({
                    'index': idx,
                    'identifier_id': question_data.get('identifier_id', 'Unknown'),
                    'error': str(e)
                })
                continue

        return stats

    def display_stats(self, stats, dry_run):
        """Display update statistics."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('📊 UPDATE STATISTICS')
        )
        self.stdout.write('='*60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  DRY RUN - No changes were made to database')
            )

        self.stdout.write(f'\n✅ Questions updated: {stats["updated"]}')
        self.stdout.write(f'❓ Questions not found: {stats["not_found"]}')
        self.stdout.write(f'⚠️  Questions without difficulty: {stats["no_difficulty"]}')
        self.stdout.write(f'❌ Errors: {len(stats["errors"])}')

        if stats['errors']:
            self.stdout.write(
                self.style.ERROR(f'\n❌ {len(stats["errors"])} ERRORS OCCURRED:')
            )
            # Show first 10 errors
            for error in stats['errors'][:10]:
                self.stdout.write(
                    f'  - Question #{error["index"]} '
                    f'({error.get("identifier_id", "N/A")}): {error["error"]}'
                )
            
            if len(stats['errors']) > 10:
                self.stdout.write(
                    f'\n  ... and {len(stats["errors"]) - 10} more errors'
                )

        self.stdout.write('='*60 + '\n')

        if not dry_run and stats['updated'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Successfully updated {stats["updated"]} questions')
            )

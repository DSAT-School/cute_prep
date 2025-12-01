"""
Management command to import questions from JSON file.

Simplified version for single Question model.

Usage:
    python manage.py import_questions test.json
    python manage.py import_questions test.json --dry-run
"""
import json
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.practice.models import Question


class Command(BaseCommand):
    """Import SAT questions from JSON file."""

    help = 'Import SAT questions from JSON file'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to JSON file containing questions'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip questions that already exist'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        json_file = options['json_file']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

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

            # Import questions
            with transaction.atomic():
                stats = self.import_questions(questions_data, dry_run, skip_existing)
                
                if dry_run:
                    raise Exception("Dry run - rolling back transaction")

        except FileNotFoundError:
            raise CommandError(f'File not found: {json_file}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')
        except Exception as e:
            if not dry_run:
                raise CommandError(f'Error importing questions: {e}')

        # Display statistics
        self.display_stats(stats, dry_run)

    def import_questions(self, questions_data, dry_run, skip_existing):
        """Import questions directly into Question model."""
        stats = {
            'questions_created': 0,
            'questions_updated': 0,
            'questions_skipped': 0,
            'errors': []
        }

        for idx, question_data in enumerate(questions_data, 1):
            try:
                # Progress indicator
                if idx % 100 == 0:
                    self.stdout.write(f'Processing question {idx}/{len(questions_data)}...')

                identifier_id = question_data.get('identifier_id')
                if not identifier_id:
                    stats['errors'].append({
                        'index': idx,
                        'error': 'Missing identifier_id'
                    })
                    continue

                # Check if question exists
                existing = Question.objects.filter(identifier_id=identifier_id).first()
                
                if existing and skip_existing:
                    stats['questions_skipped'] += 1
                    continue

                # Parse question UUID
                try:
                    question_uuid = uuid.UUID(question_data.get('questionId'))
                except (ValueError, TypeError, KeyError):
                    question_uuid = uuid.uuid4()

                # Prepare question data
                question_fields = {
                    'identifier_id': identifier_id,
                    'question_id': question_uuid,
                    'domain_name': question_data.get('domain_name', ''),
                    'domain_code': question_data.get('domain_code', ''),
                    'skill_name': question_data.get('skill_name', ''),
                    'skill_code': question_data.get('skill_code', ''),
                    'provider_name': question_data.get('provider_name', 'College Board'),
                    'provider_code': question_data.get('provider_code', 'cb'),
                    'question_type': question_data.get('question_type', 'mcq'),
                    'stimulus': question_data.get('stimulus', None),  # Can be null
                    'stem': question_data.get('stem', ''),
                    'explanation': question_data.get('explanation', ''),
                    'mcq_answer': question_data.get('mcq_answer', ''),
                    'mcq_option_list': question_data.get('mcq_option_list', None),
                    'tutorial_link': question_data.get('questionTutorialLink', ''),
                    'is_active': True
                }

                if not dry_run:
                    if existing:
                        # Update existing question
                        for field, value in question_fields.items():
                            setattr(existing, field, value)
                        existing.save()
                        stats['questions_updated'] += 1
                    else:
                        # Create new question
                        Question.objects.create(**question_fields)
                        stats['questions_created'] += 1
                else:
                    if existing:
                        stats['questions_updated'] += 1
                    else:
                        stats['questions_created'] += 1

            except Exception as e:
                stats['errors'].append({
                    'index': idx,
                    'identifier_id': question_data.get('identifier_id', 'Unknown'),
                    'error': str(e)
                })
                continue

        return stats

    def display_stats(self, stats, dry_run):
        """Display import statistics."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('📊 IMPORT STATISTICS')
        )
        self.stdout.write('='*60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  DRY RUN - No changes were made to database')
            )

        self.stdout.write(f'\n✅ Questions created: {stats["questions_created"]}')
        self.stdout.write(f'🔄 Questions updated: {stats["questions_updated"]}')
        self.stdout.write(f'⏭️  Questions skipped: {stats["questions_skipped"]}')
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

        if not dry_run:
            total = (stats['questions_created'] + stats['questions_updated'] + 
                    stats['questions_skipped'] + len(stats['errors']))
            if total > 0:
                success_rate = (
                    (stats['questions_created'] + stats['questions_updated']) / total
                ) * 100
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Success rate: {success_rate:.2f}%')
                )

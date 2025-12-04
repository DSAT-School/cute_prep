"""
Admin configuration for practice application.

Simplified admin for single Question model.
"""
from django.contrib import admin
from django.utils.html import format_html, strip_tags

from .models import Question, PracticeSession, UserAnswer, MarkedQuestion, MasteredQuestion


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin for Question model - simplified version."""

    list_display = [
        'identifier_id',
        'domain_code',
        'skill_code',
        'question_type',
        'has_stimulus',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'question_type',
        'is_active',
        'domain_code',
        'skill_code',
        'provider_code',
        'created_at'
    ]
    search_fields = [
        'identifier_id',
        'question_id',
        'domain_name',
        'skill_name',
        'stem'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'id',
        'question_id',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Identification', {
            'fields': ('identifier_id', 'question_id')
        }),
        ('Classification', {
            'fields': (
                'domain_name',
                'domain_code',
                'skill_name',
                'skill_code',
                'provider_name',
                'provider_code',
                'question_type'
            )
        }),
        ('Content', {
            'fields': ('stimulus', 'stem', 'explanation')
        }),
        ('MCQ Options', {
            'fields': ('mcq_answer', 'mcq_option_list'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tutorial_link', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_stimulus(self, obj):
        """Check if question has stimulus."""
        if obj.stimulus:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">-</span>')
    has_stimulus.short_description = 'Stimulus'


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    """Admin for PracticeSession model."""
    
    list_display = [
        'session_key',
        'user',
        'status',
        'questions_answered',
        'correct_answers',
        'accuracy_display',
        'total_time_display',
        'started_at'
    ]
    list_filter = ['status', 'started_at', 'domain_code', 'skill_code']
    search_fields = ['session_key', 'user__email', 'user__username']
    readonly_fields = ['id', 'session_key', 'started_at', 'updated_at']
    ordering = ['-started_at']
    
    def accuracy_display(self, obj):
        """Display accuracy rate with color coding."""
        rate = obj.accuracy_rate
        if rate >= 70:
            color = 'green'
        elif rate >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            rate
        )
    accuracy_display.short_description = 'Accuracy'
    
    def total_time_display(self, obj):
        """Display total time in readable format."""
        minutes = obj.total_time_seconds // 60
        seconds = obj.total_time_seconds % 60
        return f"{minutes}m {seconds}s"
    total_time_display.short_description = 'Total Time'


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    """Admin for UserAnswer model."""
    
    list_display = [
        'user',
        'question_identifier',
        'user_answer',
        'correct_answer',
        'is_correct_display',
        'time_taken_display',
        'answered_at'
    ]
    list_filter = ['is_correct', 'answered_at']
    search_fields = [
        'user__email',
        'user__username',
        'question__identifier_id',
        'session__session_key'
    ]
    readonly_fields = ['id', 'answered_at']
    ordering = ['-answered_at']
    
    def question_identifier(self, obj):
        """Display question identifier."""
        return obj.question.identifier_id
    question_identifier.short_description = 'Question'
    
    def is_correct_display(self, obj):
        """Display correctness with visual indicator."""
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ Correct</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Incorrect</span>')
    is_correct_display.short_description = 'Result'
    
    def time_taken_display(self, obj):
        """Display time taken in readable format."""
        if obj.time_taken_seconds < 60:
            return f"{obj.time_taken_seconds}s"
        minutes = obj.time_taken_seconds // 60
        seconds = obj.time_taken_seconds % 60
        return f"{minutes}m {seconds}s"
    time_taken_display.short_description = 'Time Taken'


@admin.register(MarkedQuestion)
class MarkedQuestionAdmin(admin.ModelAdmin):
    """Admin for MarkedQuestion model."""
    
    list_display = [
        'user',
        'question_identifier',
        'domain_skill',
        'marked_at'
    ]
    list_filter = ['marked_at', 'user']
    search_fields = [
        'user__email',
        'user__username',
        'question__identifier_id',
        'question__domain_name',
        'question__skill_name'
    ]
    readonly_fields = ['id', 'marked_at']
    ordering = ['-marked_at']
    
    def question_identifier(self, obj):
        """Display question identifier."""
        return obj.question.identifier_id
    question_identifier.short_description = 'Question'
    
    def domain_skill(self, obj):
        """Display domain and skill."""
        return f"{obj.question.domain_code} - {obj.question.skill_name}"
    domain_skill.short_description = 'Domain & Skill'


@admin.register(MasteredQuestion)
class MasteredQuestionAdmin(admin.ModelAdmin):
    """Admin for MasteredQuestion model."""
    
    list_display = [
        'user',
        'question_identifier',
        'domain_skill',
        'mastered_at'
    ]
    list_filter = ['mastered_at', 'user']
    search_fields = [
        'user__email',
        'user__username',
        'question__identifier_id',
        'question__domain_name',
        'question__skill_name'
    ]
    readonly_fields = ['id', 'mastered_at']
    ordering = ['-mastered_at']
    
    def question_identifier(self, obj):
        """Display question identifier."""
        return obj.question.identifier_id
    question_identifier.short_description = 'Question'
    
    def domain_skill(self, obj):
        """Display domain and skill."""
        return f"{obj.question.domain_code} - {obj.question.skill_name}"
    domain_skill.short_description = 'Domain & Skill'

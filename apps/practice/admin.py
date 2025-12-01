"""
Admin configuration for practice application.

Simplified admin for single Question model.
"""
from django.contrib import admin
from django.utils.html import format_html, strip_tags

from .models import Question


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

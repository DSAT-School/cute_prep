"""
Models for practice application.

Simplified single-model approach for SAT question bank.
All question data stored in one model for simplicity and maintainability.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Question(models.Model):
    """
    SAT Question model - stores all question data in a single denormalized structure.
    
    This model contains all fields from the question JSON including domain, skill,
    provider information, question content, and answer options.
    """

    # Primary identifiers
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier")
    )
    identifier_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("Human-readable identifier (e.g., 'JKZRJ')")
    )
    question_id = models.UUIDField(
        db_index=True,
        help_text=_("UUID from original source")
    )

    # Domain and skill information (denormalized - stored as text)
    domain_name = models.CharField(
        max_length=200,
        db_index=True,
        help_text=_("Domain name (e.g., 'Craft and Structure')")
    )
    domain_code = models.CharField(
        max_length=20,
        db_index=True,
        help_text=_("Domain code (e.g., 'CAS')")
    )
    skill_name = models.CharField(
        max_length=200,
        help_text=_("Skill name (e.g., 'Cross-Text Connections')")
    )
    skill_code = models.CharField(
        max_length=20,
        db_index=True,
        help_text=_("Skill code (e.g., 'CTC')")
    )

    # Provider information
    provider_name = models.CharField(
        max_length=200,
        default='College Board',
        help_text=_("Provider name")
    )
    provider_code = models.CharField(
        max_length=20,
        default='cb',
        help_text=_("Provider code")
    )

    # Question type
    question_type = models.CharField(
        max_length=20,
        default='mcq',
        db_index=True,
        help_text=_("Type of question (mcq, grid_in, etc.)")
    )

    # Question content
    stimulus = models.TextField(
        blank=True,
        null=True,
        help_text=_("Question context/passage (HTML) - Optional")
    )
    stem = models.TextField(
        help_text=_("The actual question text (HTML)")
    )
    explanation = models.TextField(
        blank=True,
        help_text=_("Detailed explanation (HTML)")
    )

    # MCQ specific fields
    mcq_answer = models.CharField(
        max_length=10,
        blank=True,
        help_text=_("Correct answer for MCQ (A, B, C, D)")
    )
    mcq_option_list = models.JSONField(
        blank=True,
        null=True,
        help_text=_("MCQ options as JSON {A: text, B: text, C: text, D: text}")
    )

    # Optional fields
    tutorial_link = models.URLField(
        blank=True,
        help_text=_("Optional tutorial link")
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether question is active for practice")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when question was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when question was last updated")
    )

    class Meta:
        db_table = 'practice_questions'
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['identifier_id']),
            models.Index(fields=['question_id']),
            models.Index(fields=['domain_code', 'skill_code']),
            models.Index(fields=['domain_code', 'is_active']),
            models.Index(fields=['skill_code', 'is_active']),
            models.Index(fields=['question_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.identifier_id} - {self.domain_code}/{self.skill_code}"

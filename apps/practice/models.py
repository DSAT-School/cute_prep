"""
Models for practice application.

Simplified single-model approach for SAT question bank.
All question data stored in one model for simplicity and maintainability.
"""
import uuid
from django.conf import settings
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

    # SPR specific fields
    spr_answer = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Correct answer(s) for SPR questions as JSON list e.g., ['2.5', '5/2']")
    )

    # Optional fields
    tutorial_link = models.URLField(
        blank=True,
        help_text=_("Optional tutorial link")
    )
    
    # Difficulty level
    DIFFICULTY_CHOICES = [
        ('E', _('Easy')),
        ('M', _('Medium')),
        ('H', _('Hard')),
    ]
    difficulty = models.CharField(
        max_length=1,
        choices=DIFFICULTY_CHOICES,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Question difficulty level (E=Easy, M=Medium, H=Hard)")
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


class PracticeSession(models.Model):
    """
    Practice session tracking.
    
    Tracks when a user starts a practice session with specific filters.
    """
    
    SESSION_STATUS_CHOICES = [
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('abandoned', _('Abandoned')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique session identifier")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_sessions',
        help_text=_("User taking the practice")
    )
    
    # Session metadata
    session_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Unique session key")
    )
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text=_("Session status")
    )
    
    # Filter parameters
    domain_code = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Filtered domain code")
    )
    skill_code = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Filtered skill code")
    )
    provider_code = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Filtered provider code")
    )
    
    # Adaptive mode tracking
    is_adaptive = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether this is an adaptive practice session")
    )
    current_difficulty_level = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('E', 'Easy'), ('M', 'Medium'), ('H', 'Hard')],
        help_text=_("Current difficulty level in adaptive mode")
    )
    
    # Session stats
    total_questions = models.IntegerField(
        default=0,
        help_text=_("Total questions in this session")
    )
    questions_answered = models.IntegerField(
        default=0,
        help_text=_("Number of questions answered")
    )
    correct_answers = models.IntegerField(
        default=0,
        help_text=_("Number of correct answers")
    )
    total_time_seconds = models.IntegerField(
        default=0,
        help_text=_("Total time spent in seconds")
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When session started")
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When session was completed")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Last updated timestamp")
    )
    
    class Meta:
        db_table = 'practice_sessions'
        verbose_name = _("Practice Session")
        verbose_name_plural = _("Practice Sessions")
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['session_key']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Session {self.session_key[:8]}"
    
    @property
    def accuracy_rate(self):
        """Calculate accuracy rate."""
        if self.questions_answered == 0:
            return 0
        return (self.correct_answers / self.questions_answered) * 100


class UserAnswer(models.Model):
    """
    User's answer to a specific question in a practice session.
    
    Tracks individual answers with timing and correctness.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier")
    )
    session = models.ForeignKey(
        PracticeSession,
        on_delete=models.CASCADE,
        related_name='answers',
        help_text=_("Practice session")
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers',
        help_text=_("Question that was answered")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_answers',
        help_text=_("User who answered")
    )
    
    # Answer data
    user_answer = models.CharField(
        max_length=500,
        help_text=_("Answer provided by user")
    )
    correct_answer = models.CharField(
        max_length=500,
        help_text=_("Correct answer")
    )
    is_correct = models.BooleanField(
        help_text=_("Whether answer was correct")
    )
    
    # Timing
    time_taken_seconds = models.IntegerField(
        default=0,
        help_text=_("Time taken to answer in seconds")
    )
    
    # Metadata
    answered_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the answer was submitted")
    )
    
    class Meta:
        db_table = 'practice_user_answers'
        verbose_name = _("User Answer")
        verbose_name_plural = _("User Answers")
        ordering = ['-answered_at']
        indexes = [
            models.Index(fields=['session', 'question']),
            models.Index(fields=['user', 'is_correct']),
            models.Index(fields=['answered_at']),
        ]
        unique_together = [['session', 'question']]
    
    def __str__(self):
        return f"{self.user.email} - {self.question.identifier_id} ({'✓' if self.is_correct else '✗'})"


class MarkedQuestion(models.Model):
    """
    Questions marked for review by users.
    
    Allows users to flag questions for later review.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='marked_questions',
        help_text=_("User who marked the question")
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='marked_by_users',
        help_text=_("Question that was marked")
    )
    marked_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the question was marked")
    )
    
    class Meta:
        db_table = 'practice_marked_questions'
        verbose_name = _("Marked Question")
        verbose_name_plural = _("Marked Questions")
        ordering = ['-marked_at']
        unique_together = [['user', 'question']]
        indexes = [
            models.Index(fields=['user', 'marked_at']),
            models.Index(fields=['question']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.question.identifier_id}"


class MasteredQuestion(models.Model):
    """
    Questions marked as mastered by users.
    
    Tracks questions that users have fully understood and mastered.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mastered_questions',
        help_text=_("User who mastered the question")
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='mastered_by_users',
        help_text=_("Question that was mastered")
    )
    mastered_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the question was marked as mastered")
    )
    
    class Meta:
        db_table = 'practice_mastered_questions'
        verbose_name = _("Mastered Question")
        verbose_name_plural = _("Mastered Questions")
        ordering = ['-mastered_at']
        unique_together = [['user', 'question']]
        indexes = [
            models.Index(fields=['user', 'mastered_at']),
            models.Index(fields=['question']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.question.identifier_id}"

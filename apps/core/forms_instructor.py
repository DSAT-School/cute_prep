"""
Forms for instructor features.

Forms for instructors to manage questions and other content.
"""
import uuid
from django import forms
from apps.practice.models import Question


class QuestionForm(forms.ModelForm):
    """
    Form for creating and editing SAT questions.
    Includes all necessary fields for both English and Math questions.
    """
    
    # Override question_id to generate automatically
    question_id = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Auto-generated UUID"
    )
    
    class Meta:
        model = Question
        fields = [
            'identifier_id',
            'question_id',
            'domain_name',
            'domain_code',
            'skill_name',
            'skill_code',
            'provider_name',
            'provider_code',
            'question_type',
            'stimulus',
            'stem',
            'explanation',
            'mcq_answer',
            'mcq_option_list',
            'spr_answer',
            'tutorial_link',
            'difficulty',
            'is_active',
        ]
        
        widgets = {
            'identifier_id': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., JKZRJ'
            }),
            'domain_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., Craft and Structure'
            }),
            'domain_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., CAS'
            }),
            'skill_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., Cross-Text Connections'
            }),
            'skill_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., CTC'
            }),
            'provider_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., College Board'
            }),
            'provider_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'e.g., cb'
            }),
            'question_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm'
            }, choices=[
                ('mcq', 'Multiple Choice Question (MCQ)'),
                ('spr', 'Student Produced Response (Grid-in)'),
            ]),
            'stimulus': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'rows': 6,
                'placeholder': 'Question passage or context (optional, supports HTML)'
            }),
            'stem': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'rows': 4,
                'placeholder': 'The actual question text (required, supports HTML)'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'rows': 4,
                'placeholder': 'Detailed explanation of the answer (supports HTML)'
            }),
            'mcq_answer': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm'
            }, choices=[
                ('', 'Select correct answer'),
                ('A', 'A'),
                ('B', 'B'),
                ('C', 'C'),
                ('D', 'D'),
            ]),
            'mcq_option_list': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm font-mono',
                'rows': 6,
                'placeholder': '{\n  "A": "Option A text",\n  "B": "Option B text",\n  "C": "Option C text",\n  "D": "Option D text"\n}'
            }),
            'spr_answer': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm font-mono',
                'rows': 3,
                'placeholder': '["2.5", "5/2"]'
            }),
            'tutorial_link': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm',
                'placeholder': 'https://example.com/tutorial'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary text-sm'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary focus:ring-primary'
            }),
        }
        
        labels = {
            'identifier_id': 'Question Identifier',
            'domain_name': 'Domain Name',
            'domain_code': 'Domain Code',
            'skill_name': 'Skill Name',
            'skill_code': 'Skill Code',
            'provider_name': 'Provider Name',
            'provider_code': 'Provider Code',
            'question_type': 'Question Type',
            'stimulus': 'Stimulus/Passage',
            'stem': 'Question Stem',
            'explanation': 'Answer Explanation',
            'mcq_answer': 'Correct Answer (MCQ)',
            'mcq_option_list': 'MCQ Options (JSON)',
            'spr_answer': 'Correct Answer(s) (SPR/Grid-in)',
            'tutorial_link': 'Tutorial Link',
            'difficulty': 'Difficulty Level',
            'is_active': 'Active',
        }
        
        help_texts = {
            'identifier_id': 'Unique human-readable ID (e.g., JKZRJ)',
            'question_id': 'Auto-generated UUID',
            'domain_name': 'SAT domain (e.g., Information and Ideas, Algebra)',
            'domain_code': 'Short domain code (e.g., II, ALG)',
            'skill_name': 'Specific skill being tested',
            'skill_code': 'Short skill code',
            'question_type': 'MCQ for multiple choice, SPR for grid-in',
            'stimulus': 'Optional passage or context (supports HTML)',
            'stem': 'The question text (required, supports HTML)',
            'mcq_option_list': 'JSON object with keys A, B, C, D for MCQ questions',
            'spr_answer': 'JSON array of acceptable answers for grid-in questions',
            'difficulty': 'Question difficulty level',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Auto-generate question_id if creating new question
        if not self.instance.pk:
            self.fields['question_id'].initial = uuid.uuid4()
    
    def clean_identifier_id(self):
        """Ensure identifier_id is unique."""
        identifier_id = self.cleaned_data.get('identifier_id')
        
        # Check if identifier exists (excluding current instance if editing)
        query = Question.objects.filter(identifier_id=identifier_id)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError('A question with this identifier already exists.')
        
        return identifier_id
    
    def clean(self):
        """Validate question type specific fields."""
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        
        if question_type == 'mcq':
            # Validate MCQ fields
            mcq_answer = cleaned_data.get('mcq_answer')
            mcq_option_list = cleaned_data.get('mcq_option_list')
            
            if not mcq_answer:
                self.add_error('mcq_answer', 'MCQ questions must have a correct answer selected.')
            
            if not mcq_option_list:
                self.add_error('mcq_option_list', 'MCQ questions must have answer options.')
            else:
                # Validate JSON structure
                import json
                try:
                    if isinstance(mcq_option_list, str):
                        options = json.loads(mcq_option_list)
                    else:
                        options = mcq_option_list
                    
                    if not isinstance(options, dict):
                        self.add_error('mcq_option_list', 'Options must be a JSON object.')
                    elif not all(k in options for k in ['A', 'B', 'C', 'D']):
                        self.add_error('mcq_option_list', 'Options must include A, B, C, and D keys.')
                    
                    # Store as dict for saving
                    cleaned_data['mcq_option_list'] = options
                except json.JSONDecodeError:
                    self.add_error('mcq_option_list', 'Invalid JSON format.')
        
        elif question_type == 'spr':
            # Validate SPR fields
            spr_answer = cleaned_data.get('spr_answer')
            
            if not spr_answer:
                self.add_error('spr_answer', 'SPR questions must have at least one correct answer.')
            else:
                # Validate JSON structure
                import json
                try:
                    if isinstance(spr_answer, str):
                        answers = json.loads(spr_answer)
                    else:
                        answers = spr_answer
                    
                    if not isinstance(answers, list):
                        self.add_error('spr_answer', 'Answers must be a JSON array.')
                    elif len(answers) == 0:
                        self.add_error('spr_answer', 'At least one answer must be provided.')
                    
                    # Store as list for saving
                    cleaned_data['spr_answer'] = answers
                except json.JSONDecodeError:
                    self.add_error('spr_answer', 'Invalid JSON format.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the question instance."""
        instance = super().save(commit=False)
        
        # Ensure question_id is set
        if not instance.question_id:
            instance.question_id = uuid.uuid4()
        
        if commit:
            instance.save()
        
        return instance

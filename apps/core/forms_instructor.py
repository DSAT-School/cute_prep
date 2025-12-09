"""
Forms for instructor features.

Forms for instructors to manage questions and other content.
"""
import uuid
from django import forms
from apps.practice.models import Question


# SAT Domain and Skill choices
DOMAIN_CHOICES = [
    ('', '-- Select Domain --'),
    # English/Reading & Writing Domains
    ('Information and Ideas', 'Information and Ideas (English)'),
    ('Craft and Structure', 'Craft and Structure (English)'),
    ('Expression of Ideas', 'Expression of Ideas (English)'),
    ('Standard English Conventions', 'Standard English Conventions (English)'),
    # Math Domains
    ('Algebra', 'Algebra (Math)'),
    ('Advanced Math', 'Advanced Math (Math)'),
    ('Problem-Solving and Data Analysis', 'Problem-Solving and Data Analysis (Math)'),
    ('Geometry and Trigonometry', 'Geometry and Trigonometry (Math)'),
]

ENGLISH_DOMAIN_CHOICES = [
    ('', '-- Select Domain --'),
    ('Information and Ideas', 'Information and Ideas'),
    ('Craft and Structure', 'Craft and Structure'),
    ('Expression of Ideas', 'Expression of Ideas'),
    ('Standard English Conventions', 'Standard English Conventions'),
]

MATH_DOMAIN_CHOICES = [
    ('', '-- Select Domain --'),
    ('Algebra', 'Algebra'),
    ('Advanced Math', 'Advanced Math'),
    ('Problem-Solving and Data Analysis', 'Problem-Solving and Data Analysis'),
    ('Geometry and Trigonometry', 'Geometry and Trigonometry'),
]

SKILL_CHOICES = [
    ('', '-- Select Skill --'),
    # English Skills
    ('Central Ideas and Details', 'Central Ideas and Details'),
    ('Command of Evidence', 'Command of Evidence'),
    ('Inferences', 'Inferences'),
    ('Words in Context', 'Words in Context'),
    ('Text Structure and Purpose', 'Text Structure and Purpose'),
    ('Cross-Text Connections', 'Cross-Text Connections'),
    ('Rhetorical Synthesis', 'Rhetorical Synthesis'),
    ('Transitions', 'Transitions'),
    ('Boundaries', 'Boundaries'),
    ('Form, Structure, and Sense', 'Form, Structure, and Sense'),
    # Math Skills
    ('Linear equations in one variable', 'Linear equations in one variable'),
    ('Linear equations in two variables', 'Linear equations in two variables'),
    ('Linear functions', 'Linear functions'),
    ('Systems of two linear equations in two variables', 'Systems of two linear equations in two variables'),
    ('Linear inequalities in one or two variables', 'Linear inequalities in one or two variables'),
    ('Equivalent expressions', 'Equivalent expressions'),
    ('Nonlinear equations in one variable', 'Nonlinear equations in one variable'),
    ('Systems of equations in two variables', 'Systems of equations in two variables'),
    ('Nonlinear functions', 'Nonlinear functions'),
    ('Ratios, rates, proportional relationships, and units', 'Ratios, rates, proportional relationships, and units'),
    ('Percentages', 'Percentages'),
    ('One-variable data: distributions and measures of center and spread', 'One-variable data: distributions and measures of center and spread'),
    ('Two-variable data: models and scatterplots', 'Two-variable data: models and scatterplots'),
    ('Probability and conditional probability', 'Probability and conditional probability'),
    ('Inference from sample statistics and margin of error', 'Inference from sample statistics and margin of error'),
    ('Evaluating statistical claims: observational studies and experiments', 'Evaluating statistical claims: observational studies and experiments'),
    ('Area and volume', 'Area and volume'),
    ('Lines, angles, and triangles', 'Lines, angles, and triangles'),
    ('Right triangles and trigonometry', 'Right triangles and trigonometry'),
    ('Circles', 'Circles'),
]

ENGLISH_SKILL_CHOICES = [
    ('', '-- Select Skill --'),
    ('Central Ideas and Details', 'Central Ideas and Details'),
    ('Command of Evidence', 'Command of Evidence'),
    ('Inferences', 'Inferences'),
    ('Words in Context', 'Words in Context'),
    ('Text Structure and Purpose', 'Text Structure and Purpose'),
    ('Cross-Text Connections', 'Cross-Text Connections'),
    ('Rhetorical Synthesis', 'Rhetorical Synthesis'),
    ('Transitions', 'Transitions'),
    ('Boundaries', 'Boundaries'),
    ('Form, Structure, and Sense', 'Form, Structure, and Sense'),
]

MATH_SKILL_CHOICES = [
    ('', '-- Select Skill --'),
    ('Linear equations in one variable', 'Linear equations in one variable'),
    ('Linear equations in two variables', 'Linear equations in two variables'),
    ('Linear functions', 'Linear functions'),
    ('Systems of two linear equations in two variables', 'Systems of two linear equations in two variables'),
    ('Linear inequalities in one or two variables', 'Linear inequalities in one or two variables'),
    ('Equivalent expressions', 'Equivalent expressions'),
    ('Nonlinear equations in one variable', 'Nonlinear equations in one variable'),
    ('Systems of equations in two variables', 'Systems of equations in two variables'),
    ('Nonlinear functions', 'Nonlinear functions'),
    ('Ratios, rates, proportional relationships, and units', 'Ratios, rates, proportional relationships, and units'),
    ('Percentages', 'Percentages'),
    ('One-variable data: distributions and measures of center and spread', 'One-variable data: distributions and measures of center and spread'),
    ('Two-variable data: models and scatterplots', 'Two-variable data: models and scatterplots'),
    ('Probability and conditional probability', 'Probability and conditional probability'),
    ('Inference from sample statistics and margin of error', 'Inference from sample statistics and margin of error'),
    ('Evaluating statistical claims: observational studies and experiments', 'Evaluating statistical claims: observational studies and experiments'),
    ('Area and volume', 'Area and volume'),
    ('Lines, angles, and triangles', 'Lines, angles, and triangles'),
    ('Right triangles and trigonometry', 'Right triangles and trigonometry'),
    ('Circles', 'Circles'),
]


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
    
    # Individual MCQ option fields (easier UX than JSON)
    mcq_option_a = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
            'rows': 2,
            'placeholder': 'Option A text (supports LaTeX)',
            'id': 'id_mcq_option_a'
        }),
        label='Option A'
    )
    
    mcq_option_b = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
            'rows': 2,
            'placeholder': 'Option B text (supports LaTeX)',
            'id': 'id_mcq_option_b'
        }),
        label='Option B'
    )
    
    mcq_option_c = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
            'rows': 2,
            'placeholder': 'Option C text (supports LaTeX)',
            'id': 'id_mcq_option_c'
        }),
        label='Option C'
    )
    
    mcq_option_d = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
            'rows': 2,
            'placeholder': 'Option D text (supports LaTeX)',
            'id': 'id_mcq_option_d'
        }),
        label='Option D'
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
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'e.g., JKZRJ'
            }),
            'domain_name': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'id': 'id_domain_name'
            }, choices=DOMAIN_CHOICES),
            'domain_code': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-600 cursor-not-allowed',
                'placeholder': 'Auto-filled',
                'readonly': 'readonly',
                'id': 'id_domain_code'
            }),
            'skill_name': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'id': 'id_skill_name'
            }, choices=SKILL_CHOICES),
            'skill_code': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-600 cursor-not-allowed',
                'placeholder': 'Auto-filled',
                'readonly': 'readonly',
                'id': 'id_skill_code'
            }),
            'provider_name': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'e.g., College Board'
            }),
            'provider_code': forms.TextInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'e.g., cb'
            }),
            'question_type': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors'
            }, choices=[
                ('mcq', 'Multiple Choice Question (MCQ)'),
                ('spr', 'Student Produced Response (Grid-in)'),
            ]),
            'stimulus': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 6,
                'placeholder': 'Question passage or context (optional, supports HTML and LaTeX)',
                'id': 'id_stimulus'
            }),
            'stem': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 4,
                'placeholder': 'The actual question text (required, supports HTML and LaTeX)',
                'id': 'id_stem'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 4,
                'placeholder': 'Detailed explanation of the answer (supports HTML and LaTeX)',
                'id': 'id_explanation'
            }),
            'mcq_answer': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors'
            }, choices=[
                ('', 'Select correct answer'),
                ('A', 'A'),
                ('B', 'B'),
                ('C', 'C'),
                ('D', 'D'),
            ]),
            'mcq_option_list': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 6,
                'placeholder': '{\n  "A": "Option A text",\n  "B": "Option B text",\n  "C": "Option C text",\n  "D": "Option D text"\n}',
                'id': 'id_mcq_option_list'
            }),
            'spr_answer': forms.Textarea(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors resize-y',
                'rows': 3,
                'placeholder': '["2.5", "5/2"]'
            }),
            'tutorial_link': forms.URLInput(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
                'placeholder': 'https://example.com/tutorial'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors'
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
        # Extract subject parameter if provided
        subject = kwargs.pop('subject', None)
        
        super().__init__(*args, **kwargs)
        
        # Auto-generate question_id if creating new question
        if not self.instance.pk:
            self.fields['question_id'].initial = uuid.uuid4()
        
        # Set domain and skill choices based on subject
        if subject == 'english':
            self.fields['domain_name'].widget.choices = ENGLISH_DOMAIN_CHOICES
            self.fields['skill_name'].widget.choices = ENGLISH_SKILL_CHOICES
        elif subject == 'math':
            self.fields['domain_name'].widget.choices = MATH_DOMAIN_CHOICES
            self.fields['skill_name'].widget.choices = MATH_SKILL_CHOICES
        else:
            # Use all choices for general form
            self.fields['domain_name'].widget.choices = DOMAIN_CHOICES
            self.fields['skill_name'].widget.choices = SKILL_CHOICES
        
        # Populate individual MCQ fields if editing existing question
        if self.instance.pk and self.instance.mcq_option_list:
            options = self.instance.mcq_option_list
            if isinstance(options, dict):
                self.fields['mcq_option_a'].initial = options.get('A', '')
                self.fields['mcq_option_b'].initial = options.get('B', '')
                self.fields['mcq_option_c'].initial = options.get('C', '')
                self.fields['mcq_option_d'].initial = options.get('D', '')
    
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
            mcq_option_a = cleaned_data.get('mcq_option_a', '').strip()
            mcq_option_b = cleaned_data.get('mcq_option_b', '').strip()
            mcq_option_c = cleaned_data.get('mcq_option_c', '').strip()
            mcq_option_d = cleaned_data.get('mcq_option_d', '').strip()
            
            if not mcq_answer:
                self.add_error('mcq_answer', 'Please select the correct answer.')
            
            # Check that all options are filled
            if not mcq_option_a:
                self.add_error('mcq_option_a', 'Option A is required for MCQ questions.')
            if not mcq_option_b:
                self.add_error('mcq_option_b', 'Option B is required for MCQ questions.')
            if not mcq_option_c:
                self.add_error('mcq_option_c', 'Option C is required for MCQ questions.')
            if not mcq_option_d:
                self.add_error('mcq_option_d', 'Option D is required for MCQ questions.')
            
            # Build the mcq_option_list from individual fields
            if mcq_option_a and mcq_option_b and mcq_option_c and mcq_option_d:
                cleaned_data['mcq_option_list'] = {
                    'A': mcq_option_a,
                    'B': mcq_option_b,
                    'C': mcq_option_c,
                    'D': mcq_option_d
                }
        
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
        
        # Build mcq_option_list from individual fields if MCQ question
        if instance.question_type == 'mcq':
            instance.mcq_option_list = self.cleaned_data.get('mcq_option_list')
        
        if commit:
            instance.save()
        
        return instance

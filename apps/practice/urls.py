"""
URL configuration for practice app.
"""
from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    # Practice modules/filter page
    path('modules/', views.practice_modules_view, name='modules'),
    
    # Practice interface - main view with URL parameters
    path('', views.practice_view, name='practice'),
    
    # Results page
    path('results/<uuid:session_id>/', views.practice_results, name='results'),
    
    # Mistake log
    path('mistake-log/', views.mistake_log_view, name='mistake_log'),
    
    # API endpoints for AJAX
    path('api/question/<uuid:question_id>/', views.get_question, name='get_question'),
    path('api/check-answer/<uuid:question_id>/', views.check_answer, name='check_answer'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
    path('api/end-practice/', views.end_practice, name='end_practice'),
    path('api/mark-question/', views.mark_question_for_review, name='mark_question'),
    path('api/marked-questions/', views.get_marked_questions, name='marked_questions'),
    path('api/master-question/', views.master_question, name='master_question'),
    path('api/mastered-questions/', views.get_mastered_questions, name='mastered_questions'),
    path('api/session-answers/<uuid:session_id>/', views.get_session_answers, name='session_answers'),
    path('api/attempted-questions/', views.get_attempted_questions, name='attempted_questions'),
]

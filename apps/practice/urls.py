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
    
    # API endpoints for AJAX
    path('api/question/<uuid:question_id>/', views.get_question, name='get_question'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
]

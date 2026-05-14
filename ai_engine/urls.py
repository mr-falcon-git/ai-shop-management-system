from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_dashboard, name='ai_dashboard'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),
]

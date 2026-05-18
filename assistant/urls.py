from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.chat, name='chat'),
    path('clear/', views.clear_chat, name='clear_chat'),
]

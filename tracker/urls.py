from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('meal/add/', views.add_meal, name='add_meal'),
    path('exercise/add/', views.add_exercise, name='add_exercise'),
    path('body/add/', views.add_body, name='add_body'),
    path('history/', views.history, name='history'),
]

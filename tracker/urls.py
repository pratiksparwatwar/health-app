from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('meal/add/', views.add_meal, name='add_meal'),
    path('exercise/add/', views.add_exercise, name='add_exercise'),
    path('body/add/', views.add_body, name='add_body'),
    path('history/', views.history, name='history'),
    path('estimate-nutrition/', views.estimate_nutrition, name='estimate_nutrition'),
    path('estimate-exercise/', views.estimate_exercise_calories, name='estimate_exercise_calories'),
    path('recommend-foods/', views.recommend_foods, name='recommend_foods'),
]

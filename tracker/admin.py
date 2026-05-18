from django.contrib import admin
from .models import MealLog, ExerciseLog, WeightLog, WaterLog


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'meal_type', 'estimated_calories', 'food_description']
    list_filter = ['meal_type', 'date']
    search_fields = ['user__username', 'food_description']
    date_hierarchy = 'date'


@admin.register(ExerciseLog)
class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'exercise_type', 'duration_minutes', 'intensity']
    list_filter = ['intensity', 'date']
    search_fields = ['user__username', 'exercise_type']
    date_hierarchy = 'date'


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'weight_kg']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'amount_ml']
    search_fields = ['user__username']
    date_hierarchy = 'date'

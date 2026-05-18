from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class MealLog(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='other')
    food_description = models.TextField()
    estimated_calories = models.PositiveIntegerField(null=True, blank=True)
    protein_grams = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.meal_type} on {self.date}"


class ExerciseLog(models.Model):
    INTENSITY_CHOICES = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercises')
    date = models.DateField(default=timezone.now)
    exercise_type = models.CharField(max_length=100, help_text='e.g. Running, Yoga, Cycling')
    duration_minutes = models.PositiveIntegerField()
    intensity = models.CharField(max_length=20, choices=INTENSITY_CHOICES, default='moderate')
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.exercise_type} on {self.date}"


class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField(default=timezone.now)
    weight_kg = models.FloatField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.weight_kg}kg on {self.date}"


class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    date = models.DateField(default=timezone.now)
    amount_ml = models.PositiveIntegerField(help_text='Amount in millilitres')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.amount_ml}ml on {self.date}"

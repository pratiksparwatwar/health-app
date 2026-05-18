from django import forms
from .models import MealLog, ExerciseLog, WeightLog, WaterLog


class MealLogForm(forms.ModelForm):
    class Meta:
        model = MealLog
        fields = ['date', 'meal_type', 'food_description', 'estimated_calories', 'protein_grams', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'food_description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class ExerciseLogForm(forms.ModelForm):
    class Meta:
        model = ExerciseLog
        fields = ['date', 'exercise_type', 'duration_minutes', 'intensity', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['date', 'weight_kg', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class WaterLogForm(forms.ModelForm):
    class Meta:
        model = WaterLog
        fields = ['date', 'amount_ml']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import timedelta

from .models import MealLog, ExerciseLog, WeightLog, WaterLog
from .forms import MealLogForm, ExerciseLogForm, WeightLogForm, WaterLogForm


@login_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    user = request.user

    # Today's summary
    todays_meals = MealLog.objects.filter(user=user, date=today)
    todays_exercises = ExerciseLog.objects.filter(user=user, date=today)
    todays_water = WaterLog.objects.filter(user=user, date=today).aggregate(total=Sum('amount_ml'))['total'] or 0
    latest_weight = WeightLog.objects.filter(user=user).first()

    # Weekly totals
    weekly_calories = MealLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('estimated_calories'))['total'] or 0
    weekly_exercise_mins = ExerciseLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('duration_minutes'))['total'] or 0
    weekly_water = WaterLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('amount_ml'))['total'] or 0

    context = {
        'today': today,
        'todays_meals': todays_meals,
        'todays_calories': todays_meals.aggregate(total=Sum('estimated_calories'))['total'] or 0,
        'todays_exercises': todays_exercises,
        'todays_exercise_mins': todays_exercises.aggregate(total=Sum('duration_minutes'))['total'] or 0,
        'todays_water_ml': todays_water,
        'latest_weight': latest_weight,
        'weekly_calories': weekly_calories,
        'weekly_exercise_mins': weekly_exercise_mins,
        'weekly_water_liters': round(weekly_water / 1000, 1),
    }
    return render(request, 'tracker/dashboard.html', context)


@login_required
def add_meal(request):
    if request.method == 'POST':
        form = MealLogForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user
            meal.save()
            messages.success(request, 'Meal logged successfully.')
            return redirect('tracker:dashboard')
    else:
        form = MealLogForm(initial={'date': timezone.now().date()})
    return render(request, 'tracker/add_meal.html', {'form': form})


@login_required
def add_exercise(request):
    if request.method == 'POST':
        form = ExerciseLogForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.user = request.user
            exercise.save()
            messages.success(request, 'Exercise logged successfully.')
            return redirect('tracker:dashboard')
    else:
        form = ExerciseLogForm(initial={'date': timezone.now().date()})
    return render(request, 'tracker/add_exercise.html', {'form': form})


@login_required
def add_body(request):
    """Combined view for logging weight and water intake."""
    weight_form = WeightLogForm(initial={'date': timezone.now().date()})
    water_form = WaterLogForm(initial={'date': timezone.now().date()})

    if request.method == 'POST':
        if 'log_weight' in request.POST:
            weight_form = WeightLogForm(request.POST)
            if weight_form.is_valid():
                entry = weight_form.save(commit=False)
                entry.user = request.user
                entry.save()
                messages.success(request, 'Weight logged successfully.')
                return redirect('tracker:dashboard')
        elif 'log_water' in request.POST:
            water_form = WaterLogForm(request.POST)
            if water_form.is_valid():
                entry = water_form.save(commit=False)
                entry.user = request.user
                entry.save()
                messages.success(request, 'Water intake logged.')
                return redirect('tracker:dashboard')

    return render(request, 'tracker/add_body.html', {'weight_form': weight_form, 'water_form': water_form})


@login_required
def history(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    user = request.user

    meals = MealLog.objects.filter(user=user, date__gte=week_ago)
    exercises = ExerciseLog.objects.filter(user=user, date__gte=week_ago)
    weights = WeightLog.objects.filter(user=user, date__gte=week_ago)
    water = WaterLog.objects.filter(user=user, date__gte=week_ago)

    context = {
        'meals': meals,
        'exercises': exercises,
        'weights': weights,
        'water': water,
        'week_ago': week_ago,
        'today': today,
    }
    return render(request, 'tracker/history.html', context)

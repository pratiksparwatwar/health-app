from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import timedelta
import json
import openai

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
@require_POST
def estimate_nutrition(request):
    """Call DeepSeek to estimate calories and protein for a food description."""
    try:
        data = json.loads(request.body)
        food = data.get('food', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not food:
        return JsonResponse({'error': 'No food description provided'}, status=400)

    if not settings.DEEPSEEK_API_KEY:
        return JsonResponse({'error': 'AI not configured'}, status=503)

    try:
        client = openai.OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition expert. When given a food description, "
                        "respond with ONLY a JSON object in this exact format: "
                        '{"calories": <integer>, "protein": <float>, "note": "<brief note>"} '
                        "Estimate for a typical single serving. No extra text."
                    ),
                },
                {"role": "user", "content": f"Estimate nutrition for: {food}"},
            ],
            max_tokens=100,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if DeepSeek wraps in ```json ... ```
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JsonResponse({
            'calories': int(result.get('calories', 0)),
            'protein': round(float(result.get('protein', 0)), 1),
            'note': result.get('note', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

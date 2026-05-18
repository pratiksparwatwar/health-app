from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import timedelta
import json
import openai

from .models import MealLog, ExerciseLog, WeightLog, WaterLog
from .forms import MealLogForm, ExerciseLogForm, WeightLogForm, WaterLogForm


def _calc_daily_goals(profile):
    """
    Return (calorie_target, water_goal_ml, protein_target) based on user profile using
    the Mifflin-St Jeor BMR formula with a moderate activity multiplier.
    Falls back to sensible defaults when profile data is incomplete.
    """
    weight = getattr(profile, 'weight_kg', None)
    height = getattr(profile, 'height_cm', None)
    age    = getattr(profile, 'age', None)
    gender = getattr(profile, 'gender', 'O')
    goal   = getattr(profile, 'goal', 'health')

    if weight and height and age:
        if gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        elif gender == 'F':
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 78  # average

        tdee = bmr * 1.55  # moderate activity

        goal_multiplier = {'lose': 0.85, 'gain': 1.15, 'muscle': 1.15}.get(goal, 1.0)
        calorie_target = round(tdee * goal_multiplier)
    else:
        calorie_target = 2000  # generic default

    # 35 ml per kg body weight, clamped to 2000–3500 ml
    if weight:
        water_goal_ml = max(2000, min(3500, round(weight * 35)))
    else:
        water_goal_ml = 2500

    # Protein target: g per kg body weight varies by goal
    protein_per_kg = {'muscle': 2.0, 'gain': 1.6, 'lose': 1.2}.get(goal, 0.8)
    protein_target = round(weight * protein_per_kg) if weight else 50

    return calorie_target, water_goal_ml, protein_target


@login_required
def dashboard(request):
    today    = timezone.now().date()
    week_ago = today - timedelta(days=7)
    user     = request.user

    # --- Today ---
    todays_meals     = MealLog.objects.filter(user=user, date=today)
    todays_exercises = ExerciseLog.objects.filter(user=user, date=today)
    todays_water_ml  = WaterLog.objects.filter(user=user, date=today).aggregate(
        total=Sum('amount_ml'))['total'] or 0
    latest_weight    = WeightLog.objects.filter(user=user).first()

    todays_calories       = todays_meals.aggregate(total=Sum('estimated_calories'))['total'] or 0
    todays_exercise_mins  = todays_exercises.aggregate(total=Sum('duration_minutes'))['total'] or 0
    todays_calories_burned = todays_exercises.aggregate(total=Sum('calories_burned'))['total'] or 0
    net_calories          = todays_calories - todays_calories_burned

    # --- Weekly ---
    weekly_calories      = MealLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('estimated_calories'))['total'] or 0
    weekly_exercise_mins = ExerciseLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('duration_minutes'))['total'] or 0
    weekly_water         = WaterLog.objects.filter(user=user, date__gte=week_ago).aggregate(
        total=Sum('amount_ml'))['total'] or 0

    # --- Goals ---
    profile = getattr(user, 'profile', None)
    calorie_target, water_goal_ml, protein_target = _calc_daily_goals(profile) if profile else (2000, 2500, 50)

    calorie_pct = min(100, round(todays_calories / calorie_target * 100)) if calorie_target else 0
    water_pct   = min(100, round(todays_water_ml / water_goal_ml * 100)) if water_goal_ml else 0

    # --- Protein ---
    todays_protein    = todays_meals.aggregate(total=Sum('protein_grams'))['total'] or 0
    todays_protein    = round(todays_protein, 1)
    protein_pct       = min(100, round(todays_protein / protein_target * 100)) if protein_target else 0
    remaining_protein = max(0, round(protein_target - todays_protein))
    diet_pref         = getattr(profile, 'dietary_preference', 'non_veg') if profile else 'non_veg'

    # --- Weight chart (last 30 days) ---
    weight_logs = WeightLog.objects.filter(
        user=user, date__gte=today - timedelta(days=30)
    ).order_by('date')
    weight_chart_labels = [str(w.date) for w in weight_logs]
    weight_chart_data   = [w.weight_kg for w in weight_logs]

    context = {
        'today': today,
        'todays_meals': todays_meals,
        'todays_calories': todays_calories,
        'todays_exercises': todays_exercises,
        'todays_exercise_mins': todays_exercise_mins,
        'todays_calories_burned': todays_calories_burned,
        'net_calories': net_calories,
        'todays_water_ml': todays_water_ml,
        'latest_weight': latest_weight,
        # Weekly
        'weekly_calories': weekly_calories,
        'weekly_exercise_mins': weekly_exercise_mins,
        'weekly_water_liters': round(weekly_water / 1000, 1),
        # Goals
        'calorie_target': calorie_target,
        'water_goal_ml': water_goal_ml,
        'water_goal_liters': round(water_goal_ml / 1000, 1),
        'calorie_pct': calorie_pct,
        'water_pct': water_pct,
        # Protein
        'protein_target': protein_target,
        'todays_protein': todays_protein,
        'protein_pct': protein_pct,
        'remaining_protein': remaining_protein,
        'diet_pref': diet_pref,
        # Chart
        'weight_chart_labels': json.dumps(weight_chart_labels),
        'weight_chart_data': json.dumps(weight_chart_data),
        'has_weight_data': len(weight_chart_labels) > 0,
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
    weight_form = WeightLogForm(initial={'date': timezone.now().date()})
    water_form  = WaterLogForm(initial={'date': timezone.now().date()})

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
    today    = timezone.now().date()
    week_ago = today - timedelta(days=7)
    user     = request.user

    meals     = MealLog.objects.filter(user=user, date__gte=week_ago)
    exercises = ExerciseLog.objects.filter(user=user, date__gte=week_ago)
    weights   = WeightLog.objects.filter(user=user, date__gte=week_ago)
    water     = WaterLog.objects.filter(user=user, date__gte=week_ago)

    context = {
        'meals': meals, 'exercises': exercises,
        'weights': weights, 'water': water,
        'week_ago': week_ago, 'today': today,
    }
    return render(request, 'tracker/history.html', context)


# ── AI endpoints ────────────────────────────────────────────────────────────

def _deepseek_client():
    return openai.OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


@login_required
@require_POST
def estimate_nutrition(request):
    """Return AI-estimated calories and protein for a food description."""
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
        response = _deepseek_client().chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition expert. When given a food description, "
                        "respond with ONLY a JSON object: "
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
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JsonResponse({
            'calories': int(result.get('calories', 0)),
            'protein':  round(float(result.get('protein', 0)), 1),
            'note':     result.get('note', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def estimate_exercise_calories(request):
    """Return AI-estimated calories burned for an exercise session."""
    try:
        data     = json.loads(request.body)
        exercise = data.get('exercise', '').strip()
        duration = data.get('duration', '')
        intensity = data.get('intensity', '')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not exercise or not duration:
        return JsonResponse({'error': 'Missing exercise or duration'}, status=400)
    if not settings.DEEPSEEK_API_KEY:
        return JsonResponse({'error': 'AI not configured'}, status=503)

    # Include user weight for a better estimate if available
    profile = getattr(request.user, 'profile', None)
    weight_info = f" (person weighs approximately {profile.weight_kg} kg)" if (profile and profile.weight_kg) else ""

    try:
        response = _deepseek_client().chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fitness expert. When given an exercise description, "
                        "respond with ONLY a JSON object: "
                        '{"calories_burned": <integer>, "note": "<brief note>"} '
                        "No extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Estimate calories burned: {exercise}, {duration} minutes, "
                        f"{intensity} intensity{weight_info}."
                    ),
                },
            ],
            max_tokens=80,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JsonResponse({
            'calories_burned': int(result.get('calories_burned', 0)),
            'note':            result.get('note', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def recommend_foods(request):
    """Return AI food suggestions to meet the remaining protein quota for the day."""
    try:
        data = json.loads(request.body)
        remaining_protein = float(data.get('remaining_protein', 0))
    except (json.JSONDecodeError, KeyError, ValueError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not settings.DEEPSEEK_API_KEY:
        return JsonResponse({'error': 'AI not configured'}, status=503)

    profile = getattr(request.user, 'profile', None)
    diet_pref = getattr(profile, 'dietary_preference', 'non_veg') if profile else 'non_veg'

    diet_labels = {
        'veg':     'strict vegetarian (no eggs, no meat, no fish — only plant-based foods like dal, paneer, tofu, nuts, beans)',
        'veg_egg': 'vegetarian who eats eggs but no meat or fish',
        'non_veg': 'non-vegetarian (can eat chicken, fish, eggs, meat, dairy, and plant-based foods)',
    }
    diet_desc = diet_labels.get(diet_pref, diet_labels['non_veg'])

    try:
        response = _deepseek_client().chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition expert. Suggest foods to help a person meet their daily protein target. "
                        "Respond with ONLY a JSON array of exactly 5 options: "
                        '[{"food": "<name>", "portion": "<serving size>", "protein_g": <number>, "calories": <number>}] '
                        "Make the options varied and practical. No extra text, no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"I am {diet_desc}. I still need {remaining_protein:.0f}g more protein today. "
                        "Suggest 5 easy foods I can eat now to get closer to my target."
                    ),
                },
            ],
            max_tokens=350,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JsonResponse({'recommendations': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

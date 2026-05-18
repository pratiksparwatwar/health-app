from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from tracker.models import MealLog, ExerciseLog, WeightLog
from .models import ChatMessage

import openai


def _build_user_summary(user):
    """Fetch the user's last 7 days of data and format it as a brief text summary."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    profile = getattr(user, 'profile', None)
    profile_info = ""
    if profile:
        profile_info = (
            f"Age: {profile.age or 'N/A'}, Gender: {profile.get_gender_display()}, "
            f"Height: {profile.height_cm or 'N/A'} cm, Goal: {profile.get_goal_display()}, "
            f"Diet: {profile.get_dietary_preference_display()}"
        )

    meals = MealLog.objects.filter(user=user, date__gte=week_ago).order_by('date')
    meal_lines = [
        f"  - {m.date} {m.get_meal_type_display()}: {m.food_description} "
        f"(~{m.estimated_calories or '?'} kcal, {m.protein_grams or '?'}g protein)"
        for m in meals
    ]

    exercises = ExerciseLog.objects.filter(user=user, date__gte=week_ago).order_by('date')
    exercise_lines = [
        f"  - {e.date}: {e.exercise_type}, {e.duration_minutes} min, {e.get_intensity_display()} intensity"
        for e in exercises
    ]

    weights = WeightLog.objects.filter(user=user, date__gte=week_ago).order_by('date')
    weight_lines = [f"  - {w.date}: {w.weight_kg} kg" for w in weights]

    summary = f"""User profile: {profile_info}

Last 7 days of meals:
{chr(10).join(meal_lines) if meal_lines else '  (no meals logged)'}

Last 7 days of exercise:
{chr(10).join(exercise_lines) if exercise_lines else '  (no exercise logged)'}

Recent weight entries:
{chr(10).join(weight_lines) if weight_lines else '  (no weight logged)'}"""
    return summary


def _call_deepseek(user_question, user_summary):
    """Call DeepSeek API (OpenAI-compatible) with the user's question and health context."""
    client = openai.OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )

    system_prompt = (
        "You are a friendly and knowledgeable wellness assistant for a family health tracking app. "
        "You help users with general diet and exercise suggestions based on their logged data. "
        "IMPORTANT: You do NOT provide medical diagnoses or replace professional medical advice. "
        "Always add a brief disclaimer when relevant. Be encouraging, practical, and concise."
    )

    response = client.chat.completions.create(
        model=settings.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Here is my health data from the last 7 days:\n\n{user_summary}\n\n"
                    f"My question: {user_question}"
                ),
            },
        ],
        max_tokens=800,
        temperature=0.7,
    )
    return response.choices[0].message.content


@login_required
def chat(request):
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('created_at')

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
        if not user_message:
            messages.warning(request, 'Please enter a message.')
            return redirect('assistant:chat')

        if not settings.DEEPSEEK_API_KEY:
            messages.error(request, 'AI assistant is not configured. Please set DEEPSEEK_API_KEY.')
            return redirect('assistant:chat')

        # Save user message
        ChatMessage.objects.create(user=request.user, role='user', content=user_message)

        try:
            user_summary = _build_user_summary(request.user)
            ai_reply = _call_deepseek(user_message, user_summary)
        except Exception as e:
            ai_reply = f"Sorry, I encountered an error: {str(e)}. Please try again later."

        # Save assistant reply
        ChatMessage.objects.create(user=request.user, role='assistant', content=ai_reply)
        return redirect('assistant:chat')

    return render(request, 'assistant/chat.html', {'chat_history': chat_history})


@login_required
def clear_chat(request):
    if request.method == 'POST':
        ChatMessage.objects.filter(user=request.user).delete()
        messages.success(request, 'Chat history cleared.')
    return redirect('assistant:chat')

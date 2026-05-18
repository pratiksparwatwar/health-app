# Family Health Tracker

A private family web app to log meals, exercise, body weight, water intake, and get AI-powered wellness suggestions powered by **DeepSeek AI**.

## Features

- **Family accounts** — register, login, each user belongs to a named family group
- **Meal logging** — breakfast, lunch, dinner, snacks with calorie/protein estimates
- **Exercise tracking** — type, duration, intensity
- **Body tracking** — weight and water intake logs
- **Weekly history** — view the past 7 days at a glance
- **AI Wellness Assistant** — ask DeepSeek AI for personalised suggestions based on your actual logged data
- **Django admin** — manage all data via `/admin/`

---

## Local Setup

### 1. Clone and create virtual environment

```bash
cd health_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your DEEPSEEK_API_KEY and SECRET_KEY
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 3. Run migrations and create superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) — you'll be redirected to login.

---

## Project Structure

```
health_app/
├── config/          # Django settings, root URLs, WSGI
├── accounts/        # Auth: register, login, profile, Family model
├── tracker/         # MealLog, ExerciseLog, WeightLog, WaterLog
├── assistant/       # AI chat using DeepSeek (OpenAI-compatible)
├── templates/       # base.html shared layout
├── static/css/      # custom.css
├── .env.example
├── requirements.txt
└── manage.py
```

---

## DeepSeek API

The app uses DeepSeek's **OpenAI-compatible** API via the `openai` Python library. Set `DEEPSEEK_API_KEY` in your `.env`.

Get your API key at: [https://platform.deepseek.com](https://platform.deepseek.com)

The AI assistant is safe — the API key is never exposed to the frontend, all calls happen server-side.

---

## Deployment on Render

### render.yaml (optional — or configure manually)

1. **Create a new Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Set **Build Command**:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
4. Set **Start Command**:
   ```
   gunicorn config.wsgi:application
   ```
5. Add **Environment Variables** in the Render dashboard:
   - `SECRET_KEY` — generate a strong random key
   - `DEBUG` — `False`
   - `ALLOWED_HOSTS` — `your-app-name.onrender.com`
   - `DATABASE_URL` — auto-provided if you add a Render PostgreSQL instance
   - `DEEPSEEK_API_KEY` — your DeepSeek API key

6. Add a **PostgreSQL** database in Render and link it — the `DATABASE_URL` env var is set automatically.

### Notes for Railway

Same env vars apply. Set `RAILWAY_STATIC_URL` is not needed — WhiteNoise handles static files automatically.

---

## Security Notes

- `DEEPSEEK_API_KEY` is only read server-side — never in templates or JS
- Each user can only see **their own** logs (all queries filter by `user=request.user`)
- Django CSRF protection is enabled on all forms
- Passwords are hashed by Django's default validators
- Set `DEBUG=False` in production

---

## Admin

Visit `/admin/` and log in with your superuser. All models (Family, UserProfile, MealLog, ExerciseLog, WeightLog, WaterLog, ChatMessage) are registered.

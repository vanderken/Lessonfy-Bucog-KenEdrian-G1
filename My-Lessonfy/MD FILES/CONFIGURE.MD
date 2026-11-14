# Lessonfy: Configuration

Everything configurable lives in two places: `.env` (local) and the Render dashboard (production). `lessonfy/settings.py` reads them. Never hardcode secrets.

## Environment variables

| Variable | Local `.env` | Render | What it does |
|---|---|---|---|
| `SECRET_KEY` | Generated key | Different generated key | Signs sessions and CSRF tokens. Required. |
| `DEBUG` | `True` | `False` | Shows detailed errors when True. Must be False in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Your Render hostname (added automatically via `RENDER_EXTERNAL_HOSTNAME`) | Which hostnames Django will answer to |
| `PYTHON_VERSION` | not needed | Same Python version as your computer | Tells Render which Python to use. Django 6.1 needs Python 3.12 or newer. Check Render's docs for the versions it supports. |
| `DATABASE_URL` | Supabase session pooler string | Same string | Where all data is stored |

If `SECRET_KEY` or `DATABASE_URL` is missing, the app refuses to start and tells you which one.

## Supabase

- Use the **session pooler** string (not the direct connection) in `DATABASE_URL`.
- All tables are created by Django migrations. Never create them by hand in the dashboard.
- After your tables exist (end of Phase 2, step 2.7), turn on **Row Level Security** for each table so they are not exposed through Supabase's public API. Django connects with its own database credentials, so the app keeps working.
- If a connection error mentions SSL, add `?sslmode=require` to the end of `DATABASE_URL`.

## What `settings.py` configures

| Area | Setting | Note |
|---|---|---|
| Secrets | `load_dotenv`, `SECRET_KEY`, `DEBUG` | From `.env` |
| Database | `dj_database_url.parse(DATABASE_URL)` | `conn_max_age=600` reuses connections |
| Templates | `DIRS = [BASE_DIR / "templates"]` | Project-level `templates/` folder |
| Static files | `STATICFILES_DIRS`, `STATIC_ROOT`, WhiteNoise storage | `collectstatic` writes to `staticfiles/`. Without `STATICFILES_DIRS` Django cannot find the project-level `static/` folder. |
| Middleware | WhiteNoise right after `SecurityMiddleware` | Added only when `DEBUG=False`. In development, `runserver` serves static files. |
| Auth | `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` | Used from Phase 1 |
| Production hardening | Secure cookies, proxy SSL header | Only active when `DEBUG=False` |

## Row Level Security (step 2.7)

In the Supabase **SQL Editor**, run this once after `python manage.py migrate`. It turns on RLS for every table in the `public` schema (Django's tables too). Django keeps working because it connects with the database owner login. Run it again after you add new tables.

```sql
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;
```

Check: Table Editor shows "RLS enabled" on each table, and the app still loads.

## `AUTH_USER_MODEL`

`AUTH_USER_MODEL = "core.User"` is already set. Never change it after the first `migrate`.

## Deploying to Render (Phase 8)

Create a **Web Service** from your GitHub repo and set:

| Field | Value |
|---|---|
| Build command | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| Start command | `gunicorn lessonfy.wsgi` |
| Environment variables | `SECRET_KEY` (new one), `DEBUG=False`, `DATABASE_URL` |

Render's exact labels and defaults change over time, so check its current docs if something looks different. Add variables in the dashboard. Never commit `.env`.

Before deploying, test locally with `DEBUG=False` (step 8.5) to catch static file problems early.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "SECRET_KEY is not set" | `.env` missing or not filled in |
| "DATABASE_URL is not set" | Same |
| Password authentication failed | Wrong DB password, or special characters not URL-encoded |
| Can't reach the database | Used the direct string instead of the session pooler, or a typo in the host |
| Styles missing in production | `collectstatic` not run, or WhiteNoise middleware missing |
| `migrate` complains about the user model | You migrated before the custom user model existed. Reset the Supabase database and run `migrate` again. |
| `ModuleNotFoundError: docx` or `whitenoise` | Packages not installed. Run `pip install -r requirements.txt` inside the venv. |
| Reader has no styles or buttons do nothing | Static files not found. Check `STATICFILES_DIRS` in settings and hard refresh (Ctrl+F5). |
| `CSRF verification failed` on Render | Open the site on its `https://` address. The Render hostname is trusted automatically. |

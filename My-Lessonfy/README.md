# Lessonfy

A web-based personalized study reader (Python Django + Supabase PostgreSQL): lessons split into sections, bionic reading, focus mode and timer, background sounds, and pins that save highlighted text into colored collections.

`LESSONFY.html` is the prototype the reader is based on.

## Run it

```
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env   (then fill it in)
python manage.py migrate
python manage.py test
python manage.py runserver
```

Docs, in order:

1. `MD FILES/DOWNLOAD.MD`: what to install and which accounts to create
2. `MD FILES/SETUP.MD`: get the project running
3. `MD FILES/CONFIGURE.MD`: environment variables, Supabase, Render
4. `MD FILES/TECH STACK.MD`: what is used and why
5. `MD FILES/PROJECT STRUCTURE.MD`: where every piece of code lives
6. `MD FILES/AI RULES.MD` and `MD FILES/WORK PROGRESS.MD`: the rules and the step-by-step build guide
7. `MD FILES/FIX REPORT.MD`: what was wrong and what changed in the last review

Status: all features built (phases 0 to 7). Left: RLS, manual device/browser checks, deploy (see WORK PROGRESS).

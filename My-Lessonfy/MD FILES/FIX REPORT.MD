# Lessonfy: Fix Report

Review of the project against `LESSONFY.html` (the prototype) and the MD files.
Result: phases 0 to 3 worked, phases 4 to 7 were empty placeholders. They are built now.

## TL;DR

- Reader, settings, pins, collections, dashboard: **built** to match the prototype.
- 9 bugs/risks in the old code: **fixed**.
- 38 automated Django tests + 30 browser-logic checks: **pass**.
- You still must: install packages, run `migrate`, turn on RLS, check on phone/second browser, deploy.

## Bugs and risks found (and fixed)

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | `settings.py` | `SECRET_KEY` hardcoded, `DEBUG=True` hardcoded, `ALLOWED_HOSTS=[]`. `.env` was never read for them. | Read from `.env`. App refuses to start if `SECRET_KEY` or `DATABASE_URL` is missing. |
| 2 | `settings.py` | No `STATICFILES_DIRS`. Django could not find your `static/` folder, so CSS and JS would 404. | Added `STATICFILES_DIRS`, `STATIC_ROOT`, WhiteNoise (production). |
| 3 | `settings.py` | WhiteNoise, production cookies/HTTPS, Render host, CSRF origins all missing. | Added. Tested with `DEBUG=False` + gunicorn. |
| 4 | `settings.py` | `MAILERS` setting (not needed) made `check --deploy` fail. | Removed. |
| 5 | `models.py` | Sound choices were `rain/cafe/white_noise`. Docs and prototype say brown, white, rain. No brown noise at all. | New choices + data fix in migration 0007. |
| 6 | `models.py` | No volume, background color, timer, section progress, or "got it" on pins. | Added fields (migration 0007). |
| 7 | register / login | `A@x.com` and `a@x.com` could be two accounts. Register sent you to a temporary page. | Email is lowercase and unique ignoring case. Register goes to dashboard. |
| 8 | `forms.py` | `.docx` upload crashed with a 500 error if `python-docx` was missing (it is **not** installed in your venv). | Clear error message. Run `pip install -r requirements.txt`. |
| 9 | panels | Windows line breaks (`\r\n`) are counted as 2 characters in Python but 1 in the browser. That would shift every pin. | Text is saved with `\n` only. Old rows are fixed by the migration. |

Also fixed:

- Deleting a section left gaps in the numbering (1, 3, 4). Now renumbered.
- Editing a section's text now removes its old pins (they would point at wrong words).
- Duplicate collection names are blocked (per user, ignoring case).
- `requirements.txt` has version ranges. `.env.example` was missing; it is back.
- Docs were out of date (`AI_RULES.md` names, Phase 0 text, empty checkboxes). Updated.

## What was added

- `templates/base.html`: shared layout and navigation (step 7.2).
- Reader (`reader.html`, `reader.css`, `bionic.js`, `settings.js`, `pins.js`): sections, progress bar, bionic reading, focus one section, text size, line spacing, light/dark, background color, sounds + volume, focus timer.
- Pins: select text, pick a collection, highlight in its color, list on the side grouped by collection, jump to pin, "Got it", remove, clear. Works with bionic on or off.
- Collections page: create, rename, recolor, delete (deleting also deletes its pins, after a confirm page).
- Dashboard: lessons with progress, Read/Edit/Delete, pin counts per collection.
- Upload page: file **or pasted text** (like "Use your own text" in the prototype).
- Styles in `app.css` using the prototype's colors and the Atkinson Hyperlegible font.
- 38 tests in `core/tests.py`: user separation, pin checks, settings checks, uploads, collections.

## Where I followed the prototype instead of the docs

You said the app should work like `LESSONFY.html`, so I did this. Tell me if you want any of it changed back.

| Topic | Docs said | Now |
|---|---|---|
| Sounds | local audio files | Generated in the browser (Web Audio). No files, nothing to download. |
| Focus mode | hide everything except text | "Focus one section": dims all other sections. |
| Timer | not mentioned | Focus timer 15/3, 25/5, 45/10 (from the prototype). |
| Highlight colors | not mentioned | Each collection has a color. The 3 prototype colors are the first choices. |
| Section size | up to 1500 characters | About 420 characters, split on sentences (like the prototype). |
| Theme | light / dark / sepia | light / dark + a background color (default, cream, mint, sky). |

## Do this now (in order)

1. Copy these files over your project. Keep your own `.env`, `venv/` and `.git/`.
2. In your venv: `pip install -r requirements.txt`
3. `python manage.py migrate` (runs migration 0007 on Supabase)
4. `python manage.py test` (should say OK)
5. `python manage.py runserver`, register, upload a file, press Read.
6. Supabase SQL Editor: run the RLS block from `CONFIGURE.MD` (step 2.7).
7. Do the checks 8.1, 8.2, 8.4 in `WORK PROGRESS.MD` (phone width, keyboard, second browser).
8. Deploy on Render (set `PYTHON_VERSION`, see `CONFIGURE.MD`).
9. Commit: `git add . && git commit -m "phases 4-7, fixes"`

## Safety note

Your `.env` (with the real database URL) was inside the zip you shared. It is not in git, which is good. If that zip went anywhere public or shared, reset the Supabase database password and make a new `SECRET_KEY`.

## Not built (on purpose)

- Learning report (bonus B.1). Pin counts first, as planned.
- Everything in the out-of-scope list in `AI RULES.MD`.
- The proposal text (`LESSONFY.MD`) still says "Anchor" once. That is the prototype's name. I did not edit your submitted proposal.

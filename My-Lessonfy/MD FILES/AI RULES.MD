# Lessonfy: AI Coding Rules

Lessonfy is a **web-based** personalized study reader (Python Django + Supabase). Read `MD FILES/LESSONFY.MD` for the full proposal. `LESSONFY.html` (the prototype) shows how the reader should look and behave. These rules override any default habits.

## 1. Stack (do not change)
- Python + Django, server-rendered templates with vanilla JavaScript. No React or other frontend framework unless I ask.
- **Supabase PostgreSQL is the project's database.** All data (users, lessons, panels, pins, collections, settings) is stored there, connected through `DATABASE_URL` (session pooler).
- **Auth is Django's built-in auth** with a custom user model (email as `USERNAME_FIELD`, unique email). Do NOT use Supabase Auth.
- Do NOT use the Supabase JS client or Supabase Storage. Django talks to the database directly.
- Deployment target: Render (gunicorn + whitenoise).
- Web only. No mobile app.

## 2. Database
- The Django ORM and migrations are the only source of truth for the schema. Never suggest creating tables by hand in the Supabase dashboard.
- Use `CheckConstraint` and `UniqueConstraint` for: unique email, font size range, line spacing range, valid theme and sound values.
- Every table has a primary key, proper ForeignKeys with `on_delete` chosen deliberately, and NOT NULL on required fields.
- Never hand-edit existing migration files. Change the models, then run `makemigrations`.
- Enable Row Level Security on tables in Supabase so they are not exposed through its public API.
- Every query must be scoped to `request.user`. A user must never read or modify another user's lessons, pins, collections, or settings.

## 3. Data model
`User`, `UserSettings` (one-to-one with user), `Lesson`, `Panel` (ordered, belongs to Lesson, has `is_done` for reading progress), `Collection` (belongs to user, has a color, name unique per user ignoring case), `Pin` (belongs to Panel and Collection; stores `start_offset`, `end_offset`, `text_snippet`, `resolved`).
- Panel text is always stored with `\n` line endings and no NUL characters (`normalize_text`). Pin offsets depend on this.
- New users automatically get the default collections: "Come back to this", "Confusing", "Study this".
- Users can create, rename, and delete their own collections and assign colors.

## 4. Pins and reading (critical)
- Pin offsets are character offsets (Unicode code points, not UTF-16 units) into the **raw panel text**, never into the rendered DOM.
- Bionic reading is a visual layer only. Toggling it must never change or break stored pins.
- Convert browser selections to raw-text offsets in one dedicated function (`rangeOffsets` in `static/js/pins.js`). The server re-checks every offset against the stored text.
- "Jump to pin" scrolls to the stored range and visually highlights it.
- The sidebar lists pins with text snippets, grouped by collection.

## 5. Features
- Lesson creation: manual (title, subtitle, unlimited panels) and automatic (`.txt` and `.docx` upload, auto-split into panels using `python-docx` for Word files).
- Validate uploads: file type, file size limit, and empty or unreadable files.
- Reading settings: bionic toggle, font size slider, line spacing slider, background color, light/dark theme, focus mode, background sound + volume, focus timer length. They are saved to `UserSettings` and loaded on page render.
- Focus timer (15/3, 25/5, 45/10) is part of the reader, as in the prototype.
- Reading progress: each section can be marked done; the dashboard shows done counts.
- Background sounds: silence, brown noise, white noise, soft rain only. The noise is generated in the browser with the Web Audio API (like the prototype), so no audio files are needed. It starts on a user click (browsers block autoplay).
- Dashboard: lessons with edit/delete, and pin counts per collection.
- Learning reports are a bonus. Build the pin counts first.

## 6. Web / UI
- Responsive layout that works on desktop and phone browsers.
- Accessibility matters (target users include students with ADHD): keyboard navigable, visible focus states, sufficient contrast in light and dark themes, no flashing or auto-moving elements.
- Reading view: comfortable line length, settings applied instantly without a page reload and saved in the background.
- Focus mode ("Focus one section") dims every section except the active one, as in the prototype. It is one checkbox, so it is always easy to exit.
- Show loading and error states for saves, uploads, and pin actions.
- Test in Chrome and at least one other browser (Selection API behavior differs slightly).

## 7. Out of scope (do NOT add)
Mobile app, real-time collaboration or sharing, spaced repetition, export/print, OCR or photo upload, binaural beats or external music, LMS or calendar integration, SMS or push notifications, video or embedded media, AI-generated summaries.

## 8. Security
- Never hardcode secrets. Use `.env` and keep it in `.gitignore`.
- CSRF protection stays on for every POST, including `fetch` calls.
- Escape all user content when rendering. Never mark user text as safe.
- Delete actions require POST and a confirmation, never a GET link.

## 9. Workflow
- Build in small vertical slices: auth, lessons, reader, settings, pins, collections, dashboard.
- Before changing multiple files, say which files will change and why.
- Do not refactor or add features I didn't ask for.
- Explain any new package before installing it, and add it to `requirements.txt`.
- After each feature, tell me how to test it manually.
- If a requirement is unclear, ask instead of guessing.
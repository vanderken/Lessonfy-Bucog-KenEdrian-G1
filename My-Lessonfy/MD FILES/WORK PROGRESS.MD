# Lessonfy: Build Guide (small steps, easy to resume)

Work through this one step at a time. Every step is small (about 15 to 30 minutes) and has a clear **Done when**, so you always know when to stop and when you can move on.

---

## 📍 RESUME HERE (update this every session)

- **Last step finished:** 7.2 (code written and tested). Phases 4 to 7 were built to match `LESSONFY.html`.
- **Next step:** 2.7 (turn on RLS, SQL is in CONFIGURE.MD), then run the manual checks 8.1, 8.2, 8.4.
- **Where I stopped / what I was thinking:** Run `pip install -r requirements.txt`, then `python manage.py migrate` (new migration 0007), then `python manage.py test`.
- **Known problem I'm avoiding or stuck on:** none

---

## How to work (the routine)

**Starting a session (2 minutes)**
1. Open this file and read only "Resume here".
2. Pick the ONE next unchecked step. Ignore everything else.
3. Set a 25-minute timer.

**During the step**
- Give the AI only that step, not the whole project. Use the prompt template below.
- Don't open new ideas. If a new idea pops up, write it in the **Parking Lot** at the bottom and keep going.
- Run the "Done when" check yourself before ticking the box.

**Ending a step (2 minutes, even if you only did one)**
1. `git add . && git commit -m "step X.X: what you did"`
2. Tick the checkbox.
3. Update "Resume here".

**If you're stuck**
- Two AI attempts and it's still broken? Stop. Write the error in "Resume here", commit what works (or `git stash`), and take a break or do a different step. Come back fresh.
- Never let the AI "fix everything" at once. Ask it to fix one error.

**Small wins matter.** One ticked box is a real session. A short session counts.

---

## Prompt template for each step

```
Read MD FILES/AI RULES.MD and MD FILES/LESSONFY.MD.
Do ONLY this step: [paste the step title and its Done when]
Before changing files, list which files you'll change.
After, tell me exactly how to test it.
Don't add anything else.
```

---

## Phase 0: Setup (about 2 hours total, split it up) [done]

- [x] **0.1 Create the Supabase project.** Save the database password in a password manager. *Done when:* project shows in the Supabase dashboard.
- [x] **0.2 Get the connection string.** In Supabase, click **Connect** and copy the **session pooler** string. *Done when:* you have it saved somewhere private (not in chat, not in git).
- [x] **0.3 Make the project folder and virtual environment.** Install: `django "psycopg[binary]" python-dotenv dj-database-url whitenoise gunicorn python-docx`. *Done when:* `python -m django --version` prints a version.
- [x] **0.4 Create the Django project and app.** `django-admin startproject lessonfy .` then `python manage.py startapp core`. *Done when:* `python manage.py runserver` shows the Django welcome page.
- [x] **0.5 Add `.env` and `.gitignore`.** Put `SECRET_KEY`, `DEBUG`, `DATABASE_URL` in `.env`. Add `.env`, `venv/`, `__pycache__/` to `.gitignore`. *Done when:* `git status` does NOT list `.env`.
- [x] **0.6 Add the docs to the repo.** Put `lessonfy-proposal.md`, `AI_RULES.md` (rename to your tool's file name if needed), and this guide in the root. *Done when:* all three are in the folder.
- [x] **0.7 First git commit.** *Done when:* `git log` shows one commit.
- [x] **0.8 Point Django at Supabase.** Update settings to read `DATABASE_URL`. Do NOT run migrate yet. *Done when:* `python manage.py check` passes with no errors.

---

## Phase 1: Accounts [done]

- [x] **1.1 Custom user model.** Email as the login field, unique email. Set `AUTH_USER_MODEL`, then `makemigrations` and `migrate`. *Done when:* the user table appears in the Supabase Table Editor.
- [x] **1.2 Register page.** *Done when:* you can create an account and see the row in Supabase.
- [x] **1.3 Login and logout.** *Done when:* you can log in, see you're logged in, and log out.
- [x] **1.4 Protect pages.** Require login for everything except login and register. *Done when:* visiting the dashboard while logged out sends you to login.
- [x] **1.5 Placeholder dashboard page.** *Done when:* after login you land on a page that says "Dashboard".

---

## Phase 2: Database tables (models only, no screens yet) [done except 2.7]

- [x] **2.1 `UserSettings` model.** One-to-one with user, with CHECK constraints for font size and line spacing ranges, theme, bionic, focus mode, sound. *Done when:* migration runs and the table exists in Supabase.
- [x] **2.2 `Collection` model.** Belongs to a user, has name and color. *Done when:* migration runs.
- [x] **2.3 Auto-create defaults on signup.** New users get a `UserSettings` row and the 3 default collections ("Come back to this", "Confusing", "Study this"). *Done when:* registering a new account creates those rows.
- [x] **2.4 `Lesson` and `Panel` models.** Panel has an order number and belongs to a lesson. *Done when:* migration runs.
- [x] **2.5 `Pin` model.** Belongs to a panel and a collection, with `start_offset`, `end_offset`, `text_snippet`. *Done when:* migration runs.
- [x] **2.6 Register models in Django admin and add test data.** *Done when:* you can create a lesson with 2 panels in `/admin`.
- [ ] **2.7 Turn on Row Level Security in Supabase** for your tables. *Done when:* RLS shows as enabled and your Django app still works.

---

## Phase 3: Lessons

- [x] **3.1 Dashboard lists your lessons.** Only the logged-in user's. *Done when:* the test lesson from 2.6 shows up, and another user can't see it.
- [x] **3.2 Create a lesson manually (title and subtitle).** *Done when:* the new lesson appears on the dashboard.
- [x] **3.3 Add panels to a lesson.** *Done when:* you can add 3 panels and they keep their order.
- [x] **3.4 Edit and delete panels.** *Done when:* both work.
- [x] **3.5 Edit and delete a lesson.** Deleting needs a POST and a confirmation. *Done when:* a deleted lesson disappears along with its panels.
- [x] **3.6 Upload a `.txt` file to auto-create a lesson.** Split into panels by blank lines or a max length. *Done when:* a text file becomes a lesson with several panels.
- [x] **3.7 Upload a `.docx` file.** Uses `python-docx`. *Done when:* a Word file becomes a lesson.
- [x] **3.8 Upload validation.** Check file type, size limit, empty file. *Done when:* bad files show a clear error message instead of crashing.

---

## Phase 4: Reader and settings

- [x] **4.1 Reader page shows a lesson's panels.** *Done when:* you can open a lesson and read all panels.
- [x] **4.2 Navigate between panels.** Next, previous, or a panel list. *Done when:* you can move through the lesson.
- [x] **4.3 Font size slider.** Applies instantly, not saved yet. *Done when:* the text resizes as you drag.
- [x] **4.4 Line spacing slider.** *Done when:* spacing changes instantly.
- [x] **4.5 Light/dark theme and background color.** *Done when:* the reader switches theme.
- [x] **4.6 Bionic reading toggle.** Visual only, built on top of the raw text. *Done when:* toggling on and off changes the display and the raw text is unchanged.
- [x] **4.7 Focus mode.** Hides everything except the text and an exit button. *Done when:* you can enter and exit it.
- [x] **4.8 Background sounds.** Silence, brown noise, white noise, soft rain. Starts on click. *Done when:* each option plays and silence stops it.
- [x] **4.9 Save settings to the database.** Use `fetch` with the CSRF token. *Done when:* changing a setting updates the `UserSettings` row in Supabase.
- [x] **4.10 Load saved settings when the page opens.** *Done when:* refresh the page, log out and in again, and your settings are still applied.

---

## Phase 5: Pins (the hardest part, go slowly)

- [x] **5.1 Selection to offsets function.** One function that converts a text selection into start and end offsets in the **raw panel text**. Add a few unit tests. *Done when:* tests pass, including with bionic reading on.
- [x] **5.2 Selecting text shows a small popup** with the list of collections. *Done when:* selecting text shows the popup.
- [x] **5.3 Save a pin.** *Done when:* choosing a collection creates a `Pin` row with the right offsets and snippet.
- [x] **5.4 Show saved pins as highlights** in the collection's color. *Done when:* reloading the page still shows your highlights.
- [x] **5.5 Sidebar list of pins** with snippets, grouped by collection. *Done when:* every pin on the lesson appears in the sidebar.
- [x] **5.6 Jump to pin.** Click a pin to scroll to it and flash-highlight it. *Done when:* it works for a pin on another panel too.
- [x] **5.7 Bionic check.** Toggle bionic on and off with pins present. *Done when:* highlights stay in exactly the right place both ways.
- [x] **5.8 Delete a pin.** *Done when:* it disappears from the text and the sidebar.

---

## Phase 6: Collections

- [x] **6.1 Collections list page.** *Done when:* you see your 3 defaults.
- [x] **6.2 Create a collection with a color.** *Done when:* it appears in the pin popup.
- [x] **6.3 Rename a collection.** *Done when:* the new name shows everywhere.
- [x] **6.4 Change a collection's color.** *Done when:* existing pins update to the new color.
- [x] **6.5 Delete a collection.** Decide what happens to its pins (delete them, or block deletion until empty). *Done when:* deleting behaves the way you chose with no errors.

---

## Phase 7: Dashboard finish

- [x] **7.1 Pin counts per collection on the dashboard.** *Done when:* the numbers match your actual pins.
- [x] **7.2 Quick cleanup.** Make sure every page is reachable from navigation. *Done when:* you can reach every feature without typing a URL.

---

## Phase 8: Polish and deploy

- [ ] **8.1 Phone-size check.** Open the app at a narrow width. *Done when:* nothing overflows or becomes unusable.
- [ ] **8.2 Accessibility check.** Tab through the pages, check contrast in both themes, no flashing elements. *Done when:* everything is usable by keyboard.
- [x] **8.3 Loading and error messages** for saves, uploads, and pin actions. *Done when:* a failed save tells you instead of failing silently.
- [ ] **8.4 Test in a second browser.** *Done when:* pins and selection work there too.
- [x] **8.5 Prepare for deployment.** Update `requirements.txt`, configure `whitenoise`, run `collectstatic`, set `ALLOWED_HOSTS`. *Done when:* it runs locally with `DEBUG=False`.
- [ ] **8.6 Deploy on Render.** Start command `gunicorn lessonfy.wsgi`, add your env vars in the dashboard. *Done when:* the live URL loads and you can log in.
- [ ] **8.7 Full walkthrough on the live site.** Register, create a lesson, upload a file, change settings, pin text, jump to a pin. *Done when:* nothing breaks.
- [ ] **8.8 Demo prep.** Screenshot your Supabase tables and constraints, and note the data-integrity features from your proposal. *Done when:* you have screenshots ready.

---

## Bonus (only after everything above)

- [ ] **B.1 Learning report.** Which collections or lessons have the most pins. Keep it simple.

---

## Parking Lot (new ideas go here, not into the code)

- Learning report (B.1) after the live demo works.
- Reorder sections by drag and drop.

## Bug Notes (write the error message here before you stop)

- (none open)
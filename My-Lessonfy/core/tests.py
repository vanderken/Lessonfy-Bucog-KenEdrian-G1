import json
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import MAX_PANEL_CHARS, split_into_panels
from .models import Collection, Lesson, Panel, Pin, User, UserSettings

PASSWORD = "Str0ng!pass-99"


def make_user(email="a@example.com"):
    return User.objects.create_user(email=email, password=PASSWORD)


def make_lesson(user, texts=("First section text.", "Second section text.")):
    lesson = Lesson.objects.create(user=user, title="Test lesson")
    for i, text in enumerate(texts, start=1):
        Panel.objects.create(lesson=lesson, order=i, text=text)
    return lesson


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class Base(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def post_json(self, url, data):
        return self.client.post(url, json.dumps(data), content_type="application/json")


class AccountTests(Base):
    def test_new_user_gets_settings_and_three_default_collections(self):
        names = set(Collection.objects.filter(user=self.user).values_list("name", flat=True))
        self.assertEqual(names, {"Come back to this", "Confusing", "Study this"})
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

    def test_register_logs_in_and_goes_to_dashboard(self):
        self.client.logout()
        r = self.client.post(reverse("register"), {
            "email": "New@Example.com", "password1": PASSWORD, "password2": PASSWORD})
        self.assertRedirects(r, reverse("dashboard"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_email_is_unique_ignoring_case(self):
        self.client.logout()
        r = self.client.post(reverse("register"), {
            "email": "A@EXAMPLE.com", "password1": PASSWORD, "password2": PASSWORD})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(User.objects.filter(email__iexact="a@example.com").count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(email="A@Example.COM", password=PASSWORD)

    def test_login_ignores_email_case(self):
        self.client.logout()
        r = self.client.post(reverse("login"), {"username": "A@Example.com", "password": PASSWORD})
        self.assertRedirects(r, reverse("dashboard"))

    def test_pages_need_login(self):
        self.client.logout()
        lesson = make_lesson(self.user)
        for name, args in [("dashboard", []), ("collections", []), ("reader", [lesson.pk]), ("lesson_detail", [lesson.pk])]:
            r = self.client.get(reverse(name, args=args))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn(reverse("login"), r.url)

    def test_api_returns_json_401_when_logged_out(self):
        self.client.logout()
        r = self.post_json(reverse("settings_save"), {"theme": "dark"})
        self.assertEqual(r.status_code, 401)
        self.assertIn("error", r.json())


class LessonTests(Base):
    def test_other_user_cannot_open_edit_or_delete(self):
        lesson = make_lesson(make_user("b@example.com"))
        panel = lesson.panels.first()
        for url in [
            reverse("lesson_detail", args=[lesson.pk]),
            reverse("reader", args=[lesson.pk]),
            reverse("lesson_edit", args=[lesson.pk]),
            reverse("lesson_delete", args=[lesson.pk]),
            reverse("panel_edit", args=[lesson.pk, panel.pk]),
        ]:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertEqual(self.client.post(reverse("lesson_delete", args=[lesson.pk])).status_code, 404)
        self.assertTrue(Lesson.objects.filter(pk=lesson.pk).exists())

    def test_delete_needs_post(self):
        lesson = make_lesson(self.user)
        self.assertEqual(self.client.get(reverse("lesson_delete", args=[lesson.pk])).status_code, 200)
        self.assertTrue(Lesson.objects.filter(pk=lesson.pk).exists())
        self.client.post(reverse("lesson_delete", args=[lesson.pk]))
        self.assertFalse(Lesson.objects.filter(pk=lesson.pk).exists())

    def test_deleting_a_panel_keeps_numbers_without_gaps(self):
        lesson = make_lesson(self.user, ("a", "b", "c"))
        mid = lesson.panels.get(order=2)
        self.client.post(reverse("panel_delete", args=[lesson.pk, mid.pk]))
        self.assertEqual(list(lesson.panels.values_list("order", flat=True)), [1, 2])
        self.client.post(reverse("panel_add", args=[lesson.pk]), {"text": "d"})
        self.assertEqual(list(lesson.panels.values_list("order", flat=True)), [1, 2, 3])

    def test_panel_text_is_stored_with_unix_line_endings(self):
        lesson = make_lesson(self.user, ())
        self.client.post(reverse("panel_add", args=[lesson.pk]), {"text": "line one\r\nline two"})
        self.assertEqual(lesson.panels.get().text, "line one\nline two")

    def test_editing_text_removes_old_pins(self):
        lesson = make_lesson(self.user, ("Hello world",))
        panel = lesson.panels.get()
        col = Collection.objects.filter(user=self.user).first()
        Pin.objects.create(panel=panel, collection=col, start_offset=0, end_offset=5, text_snippet="Hello")
        self.client.post(reverse("panel_edit", args=[lesson.pk, panel.pk]), {"text": "Completely new text"})
        self.assertEqual(Pin.objects.count(), 0)

    def test_dashboard_shows_only_own_lessons_and_pin_counts(self):
        mine = make_lesson(self.user)
        make_lesson(make_user("b@example.com"))
        col = Collection.objects.filter(user=self.user).first()
        Pin.objects.create(panel=mine.panels.first(), collection=col, start_offset=0, end_offset=3, text_snippet="Fir")
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(len(r.context["lessons"]), 1)
        self.assertEqual(r.context["total_pins"], 1)
        self.assertEqual({c.name: c.pin_count for c in r.context["collections"]}[col.name], 1)


class SplitAndUploadTests(Base):
    def test_split_by_blank_lines(self):
        self.assertEqual(split_into_panels("One.\r\n\r\nTwo.\n\n\n\nThree."), ["One.", "Two.", "Three."])

    def test_long_paragraph_is_split_on_sentences(self):
        text = " ".join(f"This is sentence number {i} of a long paragraph." for i in range(40))
        panels = split_into_panels(text)
        self.assertGreater(len(panels), 3)
        self.assertTrue(all(len(p) <= MAX_PANEL_CHARS for p in panels))
        self.assertEqual(" ".join(panels).split(), text.split())  # nothing lost

    def test_one_huge_word_run_is_cut(self):
        panels = split_into_panels("x" * 1000)
        self.assertTrue(all(len(p) <= MAX_PANEL_CHARS for p in panels))
        self.assertEqual("".join(panels), "x" * 1000)

    def test_upload_txt_creates_lesson_with_panels(self):
        f = SimpleUploadedFile("Notes.txt", b"Para one.\n\nPara two.")
        r = self.client.post(reverse("lesson_upload"), {"title": "", "file": f})
        lesson = Lesson.objects.get(user=self.user)
        self.assertRedirects(r, reverse("lesson_detail", args=[lesson.pk]))
        self.assertEqual(lesson.title, "Notes")
        self.assertEqual(lesson.panels.count(), 2)

    def test_upload_docx(self):
        from docx import Document
        doc = Document(); doc.add_paragraph("First paragraph."); doc.add_paragraph("Second paragraph.")
        buf = BytesIO(); doc.save(buf)
        f = SimpleUploadedFile("lesson.docx", buf.getvalue())
        self.client.post(reverse("lesson_upload"), {"title": "Word", "file": f})
        self.assertEqual(Lesson.objects.get(title="Word").panels.count(), 2)

    def test_paste_text_creates_lesson(self):
        self.client.post(reverse("lesson_upload"), {"title": "Pasted", "text": "A.\n\nB.\n\nC."})
        self.assertEqual(Lesson.objects.get(title="Pasted").panels.count(), 3)

    def test_bad_uploads_show_errors_not_crashes(self):
        cases = [
            (SimpleUploadedFile("a.pdf", b"%PDF"), "Wrong file type"),
            (SimpleUploadedFile("a.txt", b""), "empty"),
            (SimpleUploadedFile("a.txt", b"   \n\n  "), "No readable text"),
            (SimpleUploadedFile("a.docx", b"not a zip"), "damaged"),
            (SimpleUploadedFile("a.txt", b"x" * (1024 * 1024 + 1)), "too large"),
        ]
        for f, message in cases:
            r = self.client.post(reverse("lesson_upload"), {"title": "", "file": f})
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, message)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_nothing_given_is_an_error(self):
        r = self.client.post(reverse("lesson_upload"), {"title": "x"})
        self.assertContains(r, "Choose a .txt or .docx file")


class SettingsTests(Base):
    url = property(lambda self: reverse("settings_save"))

    def test_save_and_reload(self):
        r = self.post_json(self.url, {"font_size": 24, "line_spacing": 2.0, "theme": "dark", "background": "mint",
                                      "bionic_reading": False, "focus_mode": False, "sound": "rain",
                                      "volume": 0.7, "timer_preset": "45-10"})
        self.assertEqual(r.status_code, 200)
        s = UserSettings.objects.get(user=self.user)
        self.assertEqual((s.font_size, s.line_spacing, s.theme, s.sound, s.timer_preset), (24, 2.0, "dark", "rain", "45-10"))
        page = self.client.get(reverse("dashboard"))
        self.assertContains(page, 'data-theme="dark"')

    def test_invalid_values_are_rejected(self):
        for bad in [{"font_size": 99}, {"font_size": "big"}, {"line_spacing": 9}, {"theme": "neon"},
                    {"sound": "cafe"}, {"volume": 2}, {"bionic_reading": "yes"}, {"timer_preset": "1-1"}]:
            self.assertEqual(self.post_json(self.url, bad).status_code, 400, bad)
        self.assertEqual(UserSettings.objects.get(user=self.user).font_size, 19)

    def test_get_not_allowed_and_csrf_enforced(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        r = strict.post(self.url, json.dumps({"theme": "dark"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)


class PinTests(Base):
    def setUp(self):
        super().setUp()
        self.lesson = make_lesson(self.user, ("Hello brave new world 😀 again", "Second"))
        self.panel = self.lesson.panels.get(order=1)
        self.col = Collection.objects.filter(user=self.user).first()
        self.url = reverse("pin_create", args=[self.lesson.pk])

    def body(self, **kw):
        d = {"panel": self.panel.pk, "collection": self.col.pk, "start": 6, "end": 11}
        d.update(kw)
        return d

    def test_create_pin_saves_snippet_from_server_text(self):
        r = self.post_json(self.url, self.body())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Pin.objects.get().text_snippet, "brave")

    def test_offsets_count_characters_not_utf16_units(self):
        text = self.panel.text
        start = text.index("again")
        r = self.post_json(self.url, self.body(start=start, end=start + 5))
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Pin.objects.get().text_snippet, "again")

    def test_bad_offsets_rejected(self):
        n = len(self.panel.text)
        for bad in [dict(start=5, end=5), dict(start=9, end=3), dict(start=-1, end=3), dict(start=0, end=n + 1)]:
            self.assertEqual(self.post_json(self.url, self.body(**bad)).status_code, 400, bad)
        self.assertEqual(Pin.objects.count(), 0)

    def test_cannot_pin_into_other_users_data(self):
        other = make_user("b@example.com")
        other_lesson = make_lesson(other)
        other_col = Collection.objects.filter(user=other).first()
        # someone else's lesson
        self.assertEqual(self.post_json(reverse("pin_create", args=[other_lesson.pk]),
                         self.body(panel=other_lesson.panels.first().pk)).status_code, 404)
        # my lesson, someone else's collection
        self.assertEqual(self.post_json(self.url, self.body(collection=other_col.pk)).status_code, 404)
        # my lesson, a panel from another lesson
        self.assertEqual(self.post_json(self.url, self.body(panel=other_lesson.panels.first().pk)).status_code, 404)
        self.assertEqual(Pin.objects.count(), 0)

    def test_delete_and_resolve_are_scoped(self):
        pin = Pin.objects.create(panel=self.panel, collection=self.col, start_offset=0, end_offset=5, text_snippet="Hello")
        r = self.post_json(reverse("pin_resolve", args=[pin.pk]), {})
        self.assertTrue(r.json()["pin"]["resolved"])
        stranger = make_user("c@example.com")
        self.client.force_login(stranger)
        self.assertEqual(self.post_json(reverse("pin_delete", args=[pin.pk]), {}).status_code, 404)
        self.assertEqual(self.post_json(reverse("pin_resolve", args=[pin.pk]), {}).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.post_json(reverse("pin_delete", args=[pin.pk]), {}).status_code, 200)
        self.assertEqual(Pin.objects.count(), 0)

    def test_clear_removes_only_overlapping_pins(self):
        a = Pin.objects.create(panel=self.panel, collection=self.col, start_offset=0, end_offset=5, text_snippet="Hello")
        b = Pin.objects.create(panel=self.panel, collection=self.col, start_offset=12, end_offset=15, text_snippet="new")
        r = self.post_json(reverse("pins_clear", args=[self.lesson.pk]), {"panel": self.panel.pk, "start": 3, "end": 8})
        self.assertEqual(r.json()["removed"], [a.pk])
        self.assertTrue(Pin.objects.filter(pk=b.pk).exists())

    def test_mark_panel_done(self):
        r = self.post_json(reverse("panel_done", args=[self.panel.pk]), {"done": True})
        self.assertEqual(r.status_code, 200)
        self.panel.refresh_from_db()
        self.assertTrue(self.panel.is_done)
        self.assertEqual(self.post_json(reverse("panel_done", args=[self.panel.pk]), {"done": "yes"}).status_code, 400)

    def test_reader_page_has_data_and_escapes_text(self):
        Panel.objects.create(lesson=self.lesson, order=3, text="</script><script>alert(1)</script>")
        r = self.client.get(reverse("reader", args=[self.lesson.pk]))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertNotIn("</script><script>alert(1)", html)
        self.assertIn('id="reader-data"', html)
        self.assertEqual(len(r.context["reader_data"]["panels"]), 3)


class CollectionTests(Base):
    def test_list_shows_three_defaults(self):
        r = self.client.get(reverse("collections"))
        self.assertContains(r, "Come back to this")
        self.assertContains(r, "Confusing")
        self.assertContains(r, "Study this")

    def test_create_rename_recolor(self):
        self.client.post(reverse("collections"), {"name": "Exam", "color": "#8CC8F0"})
        c = Collection.objects.get(user=self.user, name="Exam")
        self.client.post(reverse("collection_edit", args=[c.pk]), {"name": "Final exam", "color": "#C9B3F5"})
        c.refresh_from_db()
        self.assertEqual((c.name, c.color), ("Final exam", "#C9B3F5"))

    def test_duplicate_name_rejected_ignoring_case(self):
        r = self.client.post(reverse("collections"), {"name": "confusing", "color": "#8CC8F0"})
        self.assertContains(r, "already have a collection")
        self.assertEqual(Collection.objects.filter(user=self.user, name__iexact="confusing").count(), 1)

    def test_two_users_can_use_the_same_name(self):
        other = make_user("b@example.com")
        self.assertTrue(Collection.objects.filter(user=other, name="Confusing").exists())

    def test_delete_removes_its_pins_after_confirmation(self):
        lesson = make_lesson(self.user)
        c = Collection.objects.create(user=self.user, name="Temp", color="#FFE45C")
        Pin.objects.create(panel=lesson.panels.first(), collection=c, start_offset=0, end_offset=3, text_snippet="Fir")
        page = self.client.get(reverse("collection_delete", args=[c.pk]))
        self.assertContains(page, "1 pin")
        self.assertTrue(Collection.objects.filter(pk=c.pk).exists())  # GET deletes nothing
        self.client.post(reverse("collection_delete", args=[c.pk]))
        self.assertFalse(Collection.objects.filter(pk=c.pk).exists())
        self.assertEqual(Pin.objects.count(), 0)

    def test_other_users_collection_is_404(self):
        c = Collection.objects.filter(user=make_user("b@example.com")).first()
        for name in ("collection_edit", "collection_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[c.pk])).status_code, 404)

    def test_quick_collection_is_recreated_if_missing(self):
        Collection.objects.filter(user=self.user, name="Come back to this").delete()
        r = self.client.post(reverse("quick_collection"))
        self.assertEqual(r.json()["collection"]["name"], "Come back to this")

import json
import os
from functools import wraps

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    CollectionForm,
    LessonForm,
    LessonUploadForm,
    PanelForm,
    RegisterForm,
)
from .models import (
    BACKGROUND_CHOICES,
    SOUND_CHOICES,
    THEME_CHOICES,
    TIMER_CHOICES,
    Collection,
    Lesson,
    Panel,
    Pin,
    UserSettings,
)

QUICK_COLLECTION = "Come back to this"  # used by the per-section quick button


# ---------- helpers ----------


def api_login_required(view):
    """Like login_required, but answers fetch() calls with JSON instead of a redirect."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Your session expired. Please log in again."}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def json_body(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def bad_request(message, status=400):
    return JsonResponse({"error": message}, status=status)


def get_settings(user):
    obj, _ = UserSettings.objects.get_or_create(user=user)
    return obj


def settings_to_dict(s):
    return {
        "theme": s.theme,
        "background": s.background,
        "font_size": s.font_size,
        "line_spacing": s.line_spacing,
        "bionic_reading": s.bionic_reading,
        "focus_mode": s.focus_mode,
        "sound": s.sound,
        "volume": s.volume,
        "timer_preset": s.timer_preset,
    }


def pin_to_dict(pin):
    return {
        "id": pin.pk,
        "panel": pin.panel_id,
        "collection": pin.collection_id,
        "start": pin.start_offset,
        "end": pin.end_offset,
        "snippet": pin.text_snippet,
        "resolved": pin.resolved,
    }


# ---------- accounts ----------


@login_required
def home(request):
    return redirect("dashboard")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


# ---------- dashboard ----------


@login_required
def dashboard(request):
    # Everything here is filtered by request.user. Never use .objects.all().
    lessons = Lesson.objects.filter(user=request.user).annotate(
        panel_count=Count("panels", distinct=True),
        done_count=Count("panels", filter=Q(panels__is_done=True), distinct=True),
    )
    collections = Collection.objects.filter(user=request.user).annotate(pin_count=Count("pins"))
    return render(
        request,
        "core/dashboard.html",
        {
            "lessons": lessons,
            "collections": collections,
            "total_pins": sum(c.pin_count for c in collections),
        },
    )


# ---------- lessons and panels ----------


@login_required
def create_lesson(request):
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.user = request.user  # owner comes from the session, not the form
            lesson.save()
            return redirect("lesson_detail", pk=lesson.pk)
    else:
        form = LessonForm()
    return render(
        request,
        "core/lesson_form.html",
        {
            "form": form,
            "heading": "New lesson",
            "submit_label": "Create lesson",
            "cancel_url": reverse("dashboard"),
        },
    )


@login_required
def edit_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect("lesson_detail", pk=lesson.pk)
    else:
        form = LessonForm(instance=lesson)
    return render(
        request,
        "core/lesson_form.html",
        {
            "form": form,
            "heading": "Edit lesson",
            "submit_label": "Save changes",
            "cancel_url": reverse("lesson_detail", args=[lesson.pk]),
        },
    )


@login_required
def delete_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    if request.method == "POST":
        lesson.delete()  # panels (and their pins) are removed by CASCADE
        return redirect("dashboard")
    # GET only shows the confirmation page. Nothing is deleted on GET.
    return render(request, "core/lesson_confirm_delete.html", {"lesson": lesson})


@login_required
def upload_lesson(request):
    if request.method == "POST":
        form = LessonUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.cleaned_data.get("file")
            title = form.cleaned_data["title"].strip()
            if not title:
                if upload:
                    title = os.path.splitext(upload.name)[0].strip()[:200]
                title = title or "Untitled lesson"
            with transaction.atomic():
                lesson = Lesson.objects.create(user=request.user, title=title)
                # Panel.save() is skipped by bulk_create, so text is already
                # normalised by split_into_panels().
                Panel.objects.bulk_create(
                    [Panel(lesson=lesson, order=i, text=t) for i, t in enumerate(form.panels, start=1)]
                )
            return redirect("lesson_detail", pk=lesson.pk)
    else:
        form = LessonUploadForm()
    return render(request, "core/lesson_upload.html", {"form": form})


@login_required
def lesson_detail(request, pk):
    # 404 if the lesson does not exist OR belongs to someone else.
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    return render(
        request,
        "core/lesson_detail.html",
        {"lesson": lesson, "panels": lesson.panels.all(), "form": PanelForm()},
    )


@login_required
@require_POST
def add_panel(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    form = PanelForm(request.POST)
    if form.is_valid():
        last = lesson.panels.aggregate(Max("order"))["order__max"] or 0
        panel = form.save(commit=False)
        panel.lesson = lesson
        panel.order = last + 1
        panel.save()
        return redirect("lesson_detail", pk=lesson.pk)
    return render(
        request,
        "core/lesson_detail.html",
        {"lesson": lesson, "panels": lesson.panels.all(), "form": form},
    )


@login_required
def edit_panel(request, pk, panel_pk):
    # The panel must belong to this lesson AND the lesson must belong to this user.
    panel = get_object_or_404(Panel, pk=panel_pk, lesson__pk=pk, lesson__user=request.user)
    old_text = panel.text  # read BEFORE the form touches the instance
    if request.method == "POST":
        form = PanelForm(request.POST, instance=panel)
        if form.is_valid():
            panel = form.save(commit=False)
            with transaction.atomic():
                if panel.text != old_text:
                    # The old pins point into text that no longer exists.
                    panel.pins.all().delete()
                    panel.is_done = False
                panel.save()
            return redirect("lesson_detail", pk=pk)
    else:
        form = PanelForm(instance=panel)
    return render(
        request,
        "core/lesson_form.html",
        {
            "form": form,
            "heading": "Edit section",
            "submit_label": "Save changes",
            "cancel_url": reverse("lesson_detail", args=[pk]),
            "note": "If you change the text, pins saved on this section are removed.",
        },
    )


@login_required
@require_POST
def delete_panel(request, pk, panel_pk):
    panel = get_object_or_404(Panel, pk=panel_pk, lesson__pk=pk, lesson__user=request.user)
    with transaction.atomic():
        panel.delete()
        # Keep order numbers 1, 2, 3 ... with no gaps.
        for i, p in enumerate(Panel.objects.filter(lesson_id=pk).order_by("order"), start=1):
            if p.order != i:
                # Going from the top, each target number is already free.
                Panel.objects.filter(pk=p.pk).update(order=i)
    return redirect("lesson_detail", pk=pk)


# ---------- reader ----------


@login_required
def reader(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    panels = list(lesson.panels.all())
    collections = list(Collection.objects.filter(user=request.user))
    pins = Pin.objects.filter(panel__lesson=lesson, collection__user=request.user)
    data = {
        "lessonId": lesson.pk,
        "title": lesson.title,
        "subtitle": lesson.subtitle,
        "panels": [{"id": p.pk, "order": p.order, "text": p.text, "done": p.is_done} for p in panels],
        "collections": [{"id": c.pk, "name": c.name, "color": c.color} for c in collections],
        "pins": [pin_to_dict(p) for p in pins],
        "settings": settings_to_dict(get_settings(request.user)),
        "quickCollection": QUICK_COLLECTION,
        "urls": {
            "settings": reverse("settings_save"),
            "quickCollection": reverse("quick_collection"),
            "pinCreate": reverse("pin_create", args=[lesson.pk]),
            "pinsClear": reverse("pins_clear", args=[lesson.pk]),
            "pinDelete": reverse("pin_delete", args=[0]),
            "pinResolve": reverse("pin_resolve", args=[0]),
            "panelDone": reverse("panel_done", args=[0]),
        },
    }
    return render(
        request,
        "core/reader.html",
        {
            "lesson": lesson,
            "reader_data": data,
            "timer_choices": TIMER_CHOICES,
            "sound_choices": SOUND_CHOICES,
            "background_choices": BACKGROUND_CHOICES,
            "s": get_settings(request.user),
        },
    )


# ---------- JSON endpoints (all POST, CSRF protected, scoped to request.user) ----------


@api_login_required
@require_POST
def settings_save(request):
    data = json_body(request)
    if data is None:
        return bad_request("Invalid request.")
    s = get_settings(request.user)
    allowed = {
        "theme": {v for v, _ in THEME_CHOICES},
        "background": {v for v, _ in BACKGROUND_CHOICES},
        "sound": {v for v, _ in SOUND_CHOICES},
        "timer_preset": {v for v, _ in TIMER_CHOICES},
    }
    for key, values in allowed.items():
        if key in data:
            if data[key] not in values:
                return bad_request(f"Invalid {key.replace('_', ' ')}.")
            setattr(s, key, data[key])
    for key in ("bionic_reading", "focus_mode"):
        if key in data:
            if not isinstance(data[key], bool):
                return bad_request(f"Invalid {key.replace('_', ' ')}.")
            setattr(s, key, data[key])
    if "font_size" in data:
        v = data["font_size"]
        if isinstance(v, bool) or not isinstance(v, int) or not 12 <= v <= 32:
            return bad_request("Text size must be between 12 and 32.")
        s.font_size = v
    if "line_spacing" in data:
        v = data["line_spacing"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 1.0 <= v <= 3.0:
            return bad_request("Line spacing must be between 1.0 and 3.0.")
        s.line_spacing = float(v)
    if "volume" in data:
        v = data["volume"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
            return bad_request("Volume must be between 0 and 1.")
        s.volume = float(v)
    s.save()
    return JsonResponse({"ok": True, "settings": settings_to_dict(s)})


@api_login_required
@require_POST
def pin_create(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    data = json_body(request)
    if data is None:
        return bad_request("Invalid request.")
    ints = {}
    for key in ("panel", "collection", "start", "end"):
        v = data.get(key)
        if isinstance(v, bool) or not isinstance(v, int):
            return bad_request("Invalid pin data.")
        ints[key] = v
    panel = Panel.objects.filter(pk=ints["panel"], lesson=lesson).first()
    collection = Collection.objects.filter(pk=ints["collection"], user=request.user).first()
    if panel is None or collection is None:
        return bad_request("Section or collection not found.", status=404)
    # Offsets count characters (code points) in the raw panel text.
    if not 0 <= ints["start"] < ints["end"] <= len(panel.text):
        return bad_request("The selected text does not match this section. Reload the page.")
    snippet = panel.text[ints["start"] : ints["end"]]
    pin = Pin.objects.create(
        panel=panel,
        collection=collection,
        start_offset=ints["start"],
        end_offset=ints["end"],
        text_snippet=snippet[:500],
    )
    return JsonResponse({"ok": True, "pin": pin_to_dict(pin)}, status=201)


@api_login_required
@require_POST
def pin_delete(request, pin_pk):
    pin = get_object_or_404(Pin, pk=pin_pk, collection__user=request.user, panel__lesson__user=request.user)
    pin.delete()
    return JsonResponse({"ok": True})


@api_login_required
@require_POST
def pin_resolve(request, pin_pk):
    pin = get_object_or_404(Pin, pk=pin_pk, collection__user=request.user, panel__lesson__user=request.user)
    data = json_body(request) or {}
    pin.resolved = data["resolved"] if isinstance(data.get("resolved"), bool) else not pin.resolved
    pin.save(update_fields=["resolved"])
    return JsonResponse({"ok": True, "pin": pin_to_dict(pin)})


@api_login_required
@require_POST
def pins_clear(request, pk):
    """Remove every pin that overlaps a selected range (the 'Clear' button)."""
    lesson = get_object_or_404(Lesson, pk=pk, user=request.user)
    data = json_body(request)
    if data is None:
        return bad_request("Invalid request.")
    panel_id, start, end = data.get("panel"), data.get("start"), data.get("end")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (panel_id, start, end)):
        return bad_request("Invalid pin data.")
    panel = Panel.objects.filter(pk=panel_id, lesson=lesson).first()
    if panel is None:
        return bad_request("Section not found.", status=404)
    qs = Pin.objects.filter(
        panel=panel, collection__user=request.user, start_offset__lt=end, end_offset__gt=start
    )
    ids = list(qs.values_list("pk", flat=True))
    qs.delete()
    return JsonResponse({"ok": True, "removed": ids})


@api_login_required
@require_POST
def panel_done(request, panel_pk):
    panel = get_object_or_404(Panel, pk=panel_pk, lesson__user=request.user)
    data = json_body(request)
    if data is None or not isinstance(data.get("done"), bool):
        return bad_request("Invalid request.")
    panel.is_done = data["done"]
    panel.save(update_fields=["is_done"])
    return JsonResponse({"ok": True, "done": panel.is_done})


@api_login_required
@require_POST
def quick_collection(request):
    """Return the id of the 'Come back to this' collection, creating it if it is missing."""
    collection = Collection.objects.filter(user=request.user, name__iexact=QUICK_COLLECTION).first()
    if collection is None:
        collection = Collection.objects.create(user=request.user, name=QUICK_COLLECTION, color="#FFE45C")
    return JsonResponse({"ok": True, "collection": {"id": collection.pk, "name": collection.name, "color": collection.color}})


# ---------- collections ----------


@login_required
def collections_list(request):
    if request.method == "POST":
        form = CollectionForm(request.POST, user=request.user)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            try:
                collection.save()
            except IntegrityError:  # two quick submits with the same name
                form.add_error("name", "You already have a collection with this name.")
            else:
                return redirect("collections")
    else:
        form = CollectionForm(user=request.user)
    collections = Collection.objects.filter(user=request.user).annotate(pin_count=Count("pins"))
    return render(request, "core/collections.html", {"collections": collections, "form": form})


@login_required
def collection_edit(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    if request.method == "POST":
        form = CollectionForm(request.POST, instance=collection, user=request.user)
        if form.is_valid():
            form.save()  # pins keep pointing at this collection, so they take the new colour
            return redirect("collections")
    else:
        form = CollectionForm(instance=collection, user=request.user)
    return render(request, "core/collection_form.html", {"form": form, "collection": collection})


@login_required
def collection_delete(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    pin_count = collection.pins.count()
    if request.method == "POST":
        collection.delete()  # its pins are deleted too (CASCADE); the page warned about it
        return redirect("collections")
    return render(request, "core/collection_confirm_delete.html", {"collection": collection, "pin_count": pin_count})

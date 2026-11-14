import io
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Collection, Lesson, Panel, User, normalize_text

MAX_UPLOAD_BYTES = 1 * 1024 * 1024  # 1 MB
MAX_PASTE_CHARS = 200_000
MAX_PANEL_CHARS = 420  # long paragraphs are cut into panels of about this length

COLOR_CHOICES = [
    ("#FFE45C", "Yellow"),
    ("#8EDBA4", "Green"),
    ("#F4A9C8", "Pink"),
    ("#8CC8F0", "Blue"),
    ("#FFB27A", "Orange"),
    ("#C9B3F5", "Purple"),
]


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class EmailLoginForm(AuthenticationForm):
    """Login form that ignores upper/lower case in the email."""

    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class ProfileForm(forms.ModelForm):
    """Lets a logged-in user view/edit their own profile info."""

    class Meta:
        model = User
        fields = ("full_name", "email", "contact_number", "photo")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        clash = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if clash.exists():
            raise ValidationError("An account with this email already exists.")
        return email


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("title", "subtitle")


class PanelForm(forms.ModelForm):
    class Meta:
        model = Panel
        fields = ("text",)
        widgets = {"text": forms.Textarea(attrs={"rows": 6})}

    def clean_text(self):
        text = normalize_text(self.cleaned_data["text"]).strip()
        if not text:
            raise ValidationError("This field is required.")
        return text


class CollectionForm(forms.ModelForm):
    color = forms.ChoiceField(choices=COLOR_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Collection
        fields = ("name", "color")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Keep an old custom colour selectable when editing.
        current = self.instance.color if self.instance and self.instance.pk else None
        if current and current.upper() not in {c.upper() for c, _ in COLOR_CHOICES}:
            self.fields["color"].choices = [(current, "Current")] + COLOR_CHOICES
        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault("color", COLOR_CHOICES[0][0])

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise ValidationError("Give the collection a name.")
        clash = Collection.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise ValidationError("You already have a collection with this name.")
        return name


def split_into_panels(text):
    """Split text into panels: by blank lines first, then by sentences up to MAX_PANEL_CHARS."""
    text = normalize_text(text).strip()
    blocks = [re.sub(r"[ \t]+", " ", b).strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    panels = []
    for block in blocks:
        if len(block) <= MAX_PANEL_CHARS:
            panels.append(block)
            continue
        sentences = re.findall(r"[^.!?\n]+[.!?]+[\"'”’)]*\s*|[^.!?]+$", block, flags=re.S) or [block]
        current = ""
        for sentence in sentences:
            while len(sentence) > MAX_PANEL_CHARS:  # one very long sentence: cut at a space
                if current.strip():
                    panels.append(current.strip())
                    current = ""
                cut = sentence.rfind(" ", 0, MAX_PANEL_CHARS)
                if cut <= 0:
                    cut = MAX_PANEL_CHARS
                panels.append(sentence[:cut].strip())
                sentence = sentence[cut:].lstrip()
            if current and len(current) + len(sentence) > MAX_PANEL_CHARS:
                panels.append(current.strip())
                current = sentence
            else:
                current += sentence
        if current.strip():
            panels.append(current.strip())
    return [p for p in panels if p]


def _read_txt(data):
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError("This text file could not be read. Save it as UTF-8 and try again.")


def _read_docx(data):
    try:
        from docx import Document
    except ImportError:  # package missing on the server
        raise ValidationError(
            "Word upload is not available yet. The server is missing python-docx."
        )
    try:
        document = Document(io.BytesIO(data))
    except Exception:
        raise ValidationError("This Word file is damaged or is not a real .docx file.")
    return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())


class LessonUploadForm(forms.Form):
    """Make a lesson from a .txt/.docx file OR from pasted text."""

    title = forms.CharField(
        max_length=200,
        required=False,
        help_text="Optional. If empty, the file name is used.",
    )
    file = forms.FileField(required=False, help_text="Only .txt or .docx, up to 1 MB.")
    text = forms.CharField(
        required=False,
        label="Or paste your text",
        widget=forms.Textarea(attrs={"rows": 8}),
        max_length=MAX_PASTE_CHARS,
        help_text="Long text is split into short sections.",
    )

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        if not upload:
            return None
        name = upload.name.lower()
        if name.endswith(".txt"):
            reader = _read_txt
        elif name.endswith(".docx"):
            reader = _read_docx
        else:
            raise ValidationError("Wrong file type. Please upload a .txt or .docx file.")
        if upload.size == 0:
            raise ValidationError("This file is empty.")
        if upload.size > MAX_UPLOAD_BYTES:
            raise ValidationError("This file is too large. The limit is 1 MB.")
        self._file_text = reader(upload.read())
        return upload

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        upload = cleaned.get("file")
        pasted = (cleaned.get("text") or "").strip()
        if not upload and not pasted:
            raise ValidationError("Choose a .txt or .docx file, or paste some text.")
        if upload and pasted:
            raise ValidationError("Use either a file or pasted text, not both.")
        panels = split_into_panels(self._file_text if upload else pasted)
        if not panels:
            raise ValidationError("No readable text was found.")
        self.panels = panels
        return cleaned

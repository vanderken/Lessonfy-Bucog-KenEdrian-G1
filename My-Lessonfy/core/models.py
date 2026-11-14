from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


ROLE_CHOICES = [
    ("student", "Student"),
    ("admin", "Admin"),
]


class User(AbstractUser):
    username = None
    email = models.EmailField("email address", unique=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")
    full_name = models.CharField(max_length=150, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        constraints = [
            # "A@x.com" and "a@x.com" are the same account.
            models.UniqueConstraint(Lower("email"), name="user_email_unique_ci"),
        ]


THEME_CHOICES = [("light", "Light"), ("dark", "Dark")]
BACKGROUND_CHOICES = [
    ("default", "Default"),
    ("cream", "Cream"),
    ("mint", "Mint"),
    ("sky", "Sky"),
]
SOUND_CHOICES = [
    ("off", "Off"),
    ("brown", "Brown noise"),
    ("white", "White noise"),
    ("rain", "Soft rain"),
]
TIMER_CHOICES = [
    ("15-3", "15 min focus / 3 min break"),
    ("25-5", "25 min focus / 5 min break"),
    ("45-10", "45 min focus / 10 min break"),
]


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    font_size = models.PositiveSmallIntegerField(default=19)
    line_spacing = models.FloatField(default=1.7)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    background = models.CharField(max_length=10, choices=BACKGROUND_CHOICES, default="default")
    bionic_reading = models.BooleanField(default=True)
    focus_mode = models.BooleanField(default=True)
    sound = models.CharField(max_length=20, choices=SOUND_CHOICES, default="off")
    volume = models.FloatField(default=0.4)
    timer_preset = models.CharField(max_length=10, choices=TIMER_CHOICES, default="25-5")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(font_size__gte=12, font_size__lte=32),
                name="usersettings_font_size_range",
            ),
            models.CheckConstraint(
                condition=Q(line_spacing__gte=1.0, line_spacing__lte=3.0),
                name="usersettings_line_spacing_range",
            ),
            models.CheckConstraint(
                condition=Q(volume__gte=0.0, volume__lte=1.0),
                name="usersettings_volume_range",
            ),
            models.CheckConstraint(
                condition=Q(theme__in=["light", "dark"]),
                name="usersettings_theme_valid",
            ),
            models.CheckConstraint(
                condition=Q(background__in=["default", "cream", "mint", "sky"]),
                name="usersettings_background_valid",
            ),
            models.CheckConstraint(
                condition=Q(sound__in=["off", "brown", "white", "rain"]),
                name="usersettings_sound_valid",
            ),
            models.CheckConstraint(
                condition=Q(timer_preset__in=["15-3", "25-5", "45-10"]),
                name="usersettings_timer_valid",
            ),
        ]

    def __str__(self):
        return f"Settings for {self.user.email}"


hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Color must be a hex code like #FF8800.",
)


class Collection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
    )
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7,
        validators=[hex_color_validator],
        default="#FFD166",
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"), "user", name="collection_unique_name_per_user"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


def normalize_text(text):
    text = (text or "").replace("\x00", "")
    return text.replace("\r\n", "\n").replace("\r", "\n")


class Lesson(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Panel(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="panels",
    )
    order = models.PositiveIntegerField()
    text = models.TextField()
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "order"],
                name="panel_unique_order_per_lesson",
            ),
        ]

    def save(self, *args, **kwargs):
        # Pin offsets point into this exact text, so it must be stored in one
        # canonical form: "\n" line endings (browsers turn "\r\n" into "\n"
        # when they parse HTML) and no NUL characters (PostgreSQL rejects them).
        self.text = normalize_text(self.text)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lesson.title} - panel {self.order}"


class Pin(models.Model):
    panel = models.ForeignKey(
        Panel,
        on_delete=models.CASCADE,
        related_name="pins",
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="pins",
    )
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()
    text_snippet = models.CharField(max_length=500)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_offset__gt=F("start_offset")),
                name="pin_end_after_start",
            ),
        ]

    def __str__(self):
        return f"Pin: {self.text_snippet[:30]}"

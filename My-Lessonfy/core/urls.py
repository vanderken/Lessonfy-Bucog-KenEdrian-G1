from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailLoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # lessons and panels
    path("lessons/new/", views.create_lesson, name="lesson_create"),
    path("lessons/upload/", views.upload_lesson, name="lesson_upload"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<int:pk>/read/", views.reader, name="reader"),
    path("lessons/<int:pk>/edit/", views.edit_lesson, name="lesson_edit"),
    path("lessons/<int:pk>/delete/", views.delete_lesson, name="lesson_delete"),
    path("lessons/<int:pk>/panels/add/", views.add_panel, name="panel_add"),
    path("lessons/<int:pk>/panels/<int:panel_pk>/edit/", views.edit_panel, name="panel_edit"),
    path("lessons/<int:pk>/panels/<int:panel_pk>/delete/", views.delete_panel, name="panel_delete"),
    # collections
    path("collections/", views.collections_list, name="collections"),
    path("collections/<int:pk>/edit/", views.collection_edit, name="collection_edit"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    # JSON endpoints used by the reader (POST only)
    path("api/settings/", views.settings_save, name="settings_save"),
    path("api/collections/quick/", views.quick_collection, name="quick_collection"),
    path("api/lessons/<int:pk>/pins/", views.pin_create, name="pin_create"),
    path("api/lessons/<int:pk>/pins/clear/", views.pins_clear, name="pins_clear"),
    path("api/pins/<int:pin_pk>/delete/", views.pin_delete, name="pin_delete"),
    path("api/pins/<int:pin_pk>/resolve/", views.pin_resolve, name="pin_resolve"),
    path("api/panels/<int:panel_pk>/done/", views.panel_done, name="panel_done"),
    # accounts
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=EmailLoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

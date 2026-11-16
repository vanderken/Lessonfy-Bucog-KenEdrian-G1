from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailLoginForm

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/student/", views.student_dashboard, name="dashboard_student"),
    path("dashboard/admin/", views.admin_dashboard, name="dashboard_admin"),
    path("dashboard/admin/users/<int:pk>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("dashboard/admin/users/<int:pk>/delete/", views.admin_user_delete, name="admin_user_delete"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("lessons/new/", views.create_lesson, name="lesson_create"),
    path("lessons/upload/", views.upload_lesson, name="lesson_upload"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<int:pk>/read/", views.reader, name="reader"),
    path("lessons/<int:pk>/edit/", views.edit_lesson, name="lesson_edit"),
    path("lessons/<int:pk>/delete/", views.delete_lesson, name="lesson_delete"),
    path("lessons/<int:pk>/panels/add/", views.add_panel, name="panel_add"),
    path("lessons/<int:pk>/panels/<int:panel_pk>/edit/", views.edit_panel, name="panel_edit"),
    path("lessons/<int:pk>/panels/<int:panel_pk>/delete/", views.delete_panel, name="panel_delete"),
    path("collections/", views.collections_list, name="collections"),
    path("collections/<int:pk>/edit/", views.collection_edit, name="collection_edit"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    path("api/settings/", views.settings_save, name="settings_save"),
    path("api/collections/quick/", views.quick_collection, name="quick_collection"),
    path("api/lessons/<int:pk>/pins/", views.pin_create, name="pin_create"),
    path("api/lessons/<int:pk>/pins/clear/", views.pins_clear, name="pins_clear"),
    path("api/pins/<int:pin_pk>/delete/", views.pin_delete, name="pin_delete"),
    path("api/pins/<int:pin_pk>/resolve/", views.pin_resolve, name="pin_resolve"),
    path("api/panels/<int:panel_pk>/done/", views.panel_done, name="panel_done"),
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

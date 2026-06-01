from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    path("wpisy/", views.post_list, name="post_list"),
    path(
        "wpis/<int:year>/<int:month>/<int:day>/<slug:slug>/",
        views.post_detail,
        name="post_detail",
    ),
    path("wpis/nowy/", views.post_create, name="post_create"),
    path("wpis/<int:pk>/edytuj/", views.post_edit, name="post_edit"),
    path("wpis/<int:pk>/usun/", views.post_delete, name="post_delete"),
    path("wpis/<int:pk>/polub/", views.post_like, name="post_like"),
    path("kategoria/<slug:slug>/", views.category_detail, name="category_detail"),
    path("szukaj/", views.search, name="search"),
    path("profil/<str:username>/", views.profile_detail, name="profile_detail"),
    path("profil/edytuj/moj-profil/", views.profile_edit, name="profile_edit"),
    path(
        "konto/logowanie/",
        auth_views.LoginView.as_view(template_name="blog/login.html"),
        name="login",
    ),
    path("konto/wylogowanie/", auth_views.LogoutView.as_view(), name="logout"),
    path("konto/rejestracja/", views.register, name="register"),
    path(
        "konto/reset-hasla/",
        auth_views.PasswordResetView.as_view(
            template_name="blog/password_reset.html",
            email_template_name="blog/emails/password_reset_email.html",
            subject_template_name="blog/emails/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "konto/reset-hasla/wyslano/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="blog/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "konto/reset-hasla/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="blog/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "konto/reset-hasla/gotowe/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="blog/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
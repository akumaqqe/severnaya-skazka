from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    AdminReportsView,
    DashboardView,
    HomeView,
    LearningResultCreateView,
    LearningResultDeleteView,
    LearningResultUpdateView,
    PollListView,
    RatingView,
    StaffPollDeleteView,
    StaffPollListView,
    poll_detail,
    register,
    staff_poll_create,
    staff_poll_update,
    vote_poll,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("register/", register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="registration/logged_out.html"),
        name="logout",
    ),
    path("polls/", PollListView.as_view(), name="poll_list"),
    path("polls/<int:pk>/", poll_detail, name="poll_detail"),
    path("polls/<int:pk>/vote/", vote_poll, name="vote_poll"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("rating/", RatingView.as_view(), name="rating"),
    path(
        "results/add/",
        LearningResultCreateView.as_view(),
        name="learning_result_add",
    ),
    path(
        "results/<int:pk>/edit/",
        LearningResultUpdateView.as_view(),
        name="learning_result_edit",
    ),
    path(
        "results/<int:pk>/delete/",
        LearningResultDeleteView.as_view(),
        name="learning_result_delete",
    ),
    path("reports/", AdminReportsView.as_view(), name="admin_reports"),
    path(
        "management/polls/",
        StaffPollListView.as_view(),
        name="staff_poll_list",
    ),
    path(
        "management/polls/create/",
        staff_poll_create,
        name="staff_poll_create",
    ),
    path(
        "management/polls/<int:pk>/edit/",
        staff_poll_update,
        name="staff_poll_update",
    ),
    path(
        "management/polls/<int:pk>/delete/",
        StaffPollDeleteView.as_view(),
        name="staff_poll_delete",
    ),
]

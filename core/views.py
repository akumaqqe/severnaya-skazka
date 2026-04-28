from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, ListView, TemplateView, UpdateView

from .forms import ChoiceFormSet, LearningResultForm, PollForm, RegistrationForm, VoteForm
from .models import LearningResult, Poll, Profile, Vote


def annotate_rating_details(queryset):
    learning_points_subquery = (
        LearningResult.objects.filter(user=OuterRef("user_id"))
        .values("user")
        .annotate(total=Coalesce(Sum("points"), 0))
        .values("total")[:1]
    )
    vote_points_subquery = (
        Vote.objects.filter(user=OuterRef("user_id"))
        .values("user")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    return queryset.annotate(
        learning_points_value=Coalesce(
            Subquery(learning_points_subquery, output_field=IntegerField()),
            0,
        ),
        vote_points_value=Coalesce(
            Subquery(vote_points_subquery, output_field=IntegerField()),
            0,
        ),
    )


def student_profiles_queryset():
    return annotate_rating_details(
        Profile.objects.select_related("user").filter(user__is_staff=False)
    )


def build_poll_results(poll):
    choices = list(poll.choices.all())
    total_votes = sum(choice.votes_count for choice in choices)
    results = []
    for choice in choices:
        percentage = round((choice.votes_count / total_votes) * 100, 1) if total_votes else 0
        results.append(
            {
                "text": choice.text,
                "votes_count": choice.votes_count,
                "percentage": percentage,
            }
        )
    return total_votes, results


def get_user_rank(user):
    ordered_user_ids = list(
        student_profiles_queryset()
        .order_by("-total_rating", "user__username")
        .values_list("user_id", flat=True)
    )
    try:
        return ordered_user_ids.index(user.id) + 1
    except ValueError:
        return None


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Эта страница доступна только администраторам.")
        return redirect("home")


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_polls"] = Poll.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
        ).order_by("end_date")[:3]
        context["top_students"] = student_profiles_queryset().order_by(
            "-total_rating",
            "user__username",
        )[:5]
        context["students_count"] = student_profiles_queryset().count()
        context["active_polls_count"] = Poll.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
        ).count()
        context["votes_count"] = Vote.objects.count()
        context["successful_results_count"] = LearningResult.objects.filter(
            is_successful=True
        ).count()
        return context


class PollListView(ListView):
    model = Poll
    template_name = "core/poll_list.html"
    context_object_name = "polls"

    def get_queryset(self):
        return Poll.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
        ).order_by("end_date")


def poll_detail(request, pk):
    poll = get_object_or_404(Poll.objects.prefetch_related("choices"), pk=pk)
    user_vote = None
    if request.user.is_authenticated:
        user_vote = Vote.objects.filter(user=request.user, poll=poll).select_related(
            "choice"
        ).first()

    has_voted = user_vote is not None
    can_vote = request.user.is_authenticated and poll.is_open and not has_voted
    can_view_results = request.user.is_staff or not poll.is_open or has_voted
    form = VoteForm(poll=poll) if can_vote else None
    total_votes, results = build_poll_results(poll)

    return render(
        request,
        "core/poll_detail.html",
        {
            "poll": poll,
            "form": form,
            "user_vote": user_vote,
            "has_voted": has_voted,
            "can_vote": can_vote,
            "can_view_results": can_view_results,
            "total_votes": total_votes,
            "results": results,
        },
    )


@login_required
def vote_poll(request, pk):
    poll = get_object_or_404(Poll.objects.prefetch_related("choices"), pk=pk)

    if request.method != "POST":
        return redirect("poll_detail", pk=poll.pk)

    if not poll.is_open:
        messages.error(request, "Голосование уже закрыто.")
        return redirect("poll_detail", pk=poll.pk)

    if Vote.objects.filter(user=request.user, poll=poll).exists():
        messages.warning(request, "Вы уже участвовали в этом голосовании.")
        return redirect("poll_detail", pk=poll.pk)

    form = VoteForm(poll=poll, data=request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                Vote.objects.create(
                    user=request.user,
                    poll=poll,
                    choice=form.cleaned_data["choice"],
                )
        except IntegrityError:
            messages.warning(request, "Повторно голосовать в одном опросе нельзя.")
        else:
            messages.success(request, "Ваш голос учтен. Спасибо за участие!")
            return redirect("poll_detail", pk=poll.pk)

    total_votes, results = build_poll_results(poll)
    return render(
        request,
        "core/poll_detail.html",
        {
            "poll": poll,
            "form": form,
            "user_vote": None,
            "has_voted": False,
            "can_vote": True,
            "can_view_results": False,
            "total_votes": total_votes,
            "results": results,
        },
        status=400,
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        context["profile"] = profile
        context["learning_results"] = self.request.user.learning_results.all()
        context["vote_history"] = self.request.user.votes.select_related(
            "poll",
            "choice",
        )
        context["learning_points"] = profile.learning_points
        context["vote_points"] = profile.vote_points
        context["user_rank"] = get_user_rank(self.request.user)
        context["successful_results_count"] = self.request.user.learning_results.filter(
            is_successful=True
        ).count()
        return context


class RatingView(ListView):
    model = Profile
    template_name = "core/rating.html"
    context_object_name = "profiles"

    def get_queryset(self):
        return student_profiles_queryset().order_by(
            "-total_rating",
            "user__username",
        )


class LearningResultCreateView(LoginRequiredMixin, TemplateView):
    template_name = "core/learning_result_form.html"

    def get(self, request, *args, **kwargs):
        form = LearningResultForm()
        return render(
            request,
            self.template_name,
            {"form": form, "page_title": "Добавить результат", "submit_label": "Сохранить"},
        )

    def post(self, request, *args, **kwargs):
        form = LearningResultForm(request.POST)
        if form.is_valid():
            learning_result = form.save(commit=False)
            learning_result.user = request.user
            learning_result.save()
            messages.success(request, "Результат добавлен и сразу попал в общий рейтинг.")
            return redirect("dashboard")
        return render(
            request,
            self.template_name,
            {"form": form, "page_title": "Добавить результат", "submit_label": "Сохранить"},
            status=400,
        )


class OwnerLearningResultMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.get_object().user == self.request.user

    def handle_no_permission(self):
        messages.error(self.request, "Можно редактировать только свои результаты.")
        return redirect("dashboard")


class LearningResultUpdateView(OwnerLearningResultMixin, UpdateView):
    model = LearningResult
    form_class = LearningResultForm
    template_name = "core/learning_result_form.html"
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Изменить результат"
        context["submit_label"] = "Обновить"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Результат обновлен.")
        return super().form_valid(form)


class LearningResultDeleteView(OwnerLearningResultMixin, DeleteView):
    model = LearningResult
    template_name = "core/learning_result_confirm_delete.html"
    success_url = reverse_lazy("dashboard")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Результат удален.")
        return super().delete(request, *args, **kwargs)


class AdminReportsView(StaffRequiredMixin, TemplateView):
    template_name = "core/admin_reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        students = student_profiles_queryset().order_by(
            "-total_rating",
            "user__username",
        )
        polls = Poll.objects.prefetch_related("choices").annotate(
            votes_total=Count("votes")
        )
        poll_statistics = []
        for poll in polls:
            total_votes, results = build_poll_results(poll)
            poll_statistics.append(
                {
                    "poll": poll,
                    "total_votes": total_votes,
                    "results": results,
                }
            )

        context["students"] = students
        context["successful_students_count"] = student_profiles_queryset().filter(
            user__learning_results__is_successful=True
        ).distinct().count()
        context["successful_results_count"] = LearningResult.objects.filter(
            is_successful=True
        ).count()
        context["poll_statistics"] = poll_statistics
        return context


class StaffPollListView(StaffRequiredMixin, ListView):
    model = Poll
    template_name = "core/staff_poll_list.html"
    context_object_name = "polls"

    def get_queryset(self):
        return Poll.objects.annotate(votes_total=Count("votes")).order_by("-created_at")


def render_staff_poll_form(request, form, formset, page_title, submit_label):
    return render(
        request,
        "core/staff_poll_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": page_title,
            "submit_label": submit_label,
        },
    )


@login_required
def staff_poll_create(request):
    if not request.user.is_staff:
        messages.error(request, "Эта страница доступна только администраторам.")
        return redirect("home")

    poll = Poll()
    if request.method == "POST":
        form = PollForm(request.POST, instance=poll)
        formset = ChoiceFormSet(request.POST, instance=poll)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                poll = form.save()
                formset.instance = poll
                formset.save()
            messages.success(request, "Голосование создано.")
            return redirect("staff_poll_list")
    else:
        form = PollForm(instance=poll)
        formset = ChoiceFormSet(instance=poll)

    return render_staff_poll_form(
        request,
        form,
        formset,
        "Создать голосование",
        "Сохранить",
    )


@login_required
def staff_poll_update(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Эта страница доступна только администраторам.")
        return redirect("home")

    poll = get_object_or_404(Poll, pk=pk)
    if request.method == "POST":
        form = PollForm(request.POST, instance=poll)
        formset = ChoiceFormSet(request.POST, instance=poll)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, "Голосование обновлено.")
            return redirect("staff_poll_list")
    else:
        form = PollForm(instance=poll)
        formset = ChoiceFormSet(instance=poll)

    return render_staff_poll_form(
        request,
        form,
        formset,
        "Редактировать голосование",
        "Обновить",
    )


class StaffPollDeleteView(StaffRequiredMixin, DeleteView):
    model = Poll
    template_name = "core/staff_poll_confirm_delete.html"
    success_url = reverse_lazy("staff_poll_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Голосование удалено.")
        return super().delete(request, *args, **kwargs)

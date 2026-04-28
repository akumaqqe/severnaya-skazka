from django.contrib import admin

from .models import Choice, LearningResult, Poll, Profile, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    fields = ("text", "votes_count")
    readonly_fields = ("votes_count",)


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_at",
        "end_date",
        "is_active",
        "display_total_votes",
    )
    search_fields = ("title", "description")
    list_filter = ("is_active", "created_at", "end_date")
    inlines = [ChoiceInline]
    date_hierarchy = "created_at"

    @admin.display(description="Всего голосов")
    def display_total_votes(self, obj):
        return obj.total_votes


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "poll", "votes_count")
    search_fields = ("text", "poll__title")
    list_filter = ("poll",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "poll", "choice", "voted_at")
    search_fields = ("user__username", "poll__title", "choice__text")
    list_filter = ("poll", "voted_at")
    autocomplete_fields = ("user", "poll", "choice")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "age",
        "class_group",
        "display_learning_points",
        "display_vote_points",
        "total_rating",
        "registered_at",
    )
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_filter = ("age", "class_group", "registered_at")
    autocomplete_fields = ("user",)

    @admin.display(description="Баллы за задания")
    def display_learning_points(self, obj):
        return obj.learning_points

    @admin.display(description="Баллы за голосования")
    def display_vote_points(self, obj):
        return obj.vote_points


@admin.register(LearningResult)
class LearningResultAdmin(admin.ModelAdmin):
    list_display = ("user", "stage_title", "points", "is_successful", "created_at")
    search_fields = ("user__username", "stage_title")
    list_filter = ("is_successful", "created_at")
    autocomplete_fields = ("user",)


admin.site.site_header = "Северная сказка"
admin.site.site_title = "Панель администратора"
admin.site.index_title = "Управление сайтом программы"

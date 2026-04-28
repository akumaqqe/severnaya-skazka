from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    age = models.PositiveSmallIntegerField(
        "Возраст",
        default=6,
        validators=[MinValueValidator(6), MaxValueValidator(11)],
    )
    class_group = models.CharField(
        "Класс / группа",
        max_length=100,
        default="Не указано",
    )
    total_rating = models.PositiveIntegerField("Общий рейтинг", default=0)
    registered_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        ordering = ("-total_rating", "user__username")

    def __str__(self):
        return f"{self.user.username} ({self.total_rating} баллов)"

    @property
    def learning_points(self):
        annotated_value = getattr(self, "learning_points_value", None)
        if annotated_value is not None:
            return annotated_value
        return self.user.learning_results.aggregate(total=Sum("points"))["total"] or 0

    @property
    def vote_points(self):
        annotated_value = getattr(self, "vote_points_value", None)
        if annotated_value is not None:
            return annotated_value
        return self.user.votes.count()

    def update_total_rating(self):
        total_points = self.learning_points + self.vote_points
        if self.total_rating != total_points:
            self.total_rating = total_points
            self.save(update_fields=["total_rating"])


class Poll(models.Model):
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    end_date = models.DateTimeField("Дата окончания")
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "Голосование"
        verbose_name_plural = "Голосования"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.is_active and self.end_date >= timezone.now()

    @property
    def total_votes(self):
        return self.votes.count()


class Choice(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Голосование",
    )
    text = models.CharField("Вариант ответа", max_length=255)
    votes_count = models.PositiveIntegerField("Количество голосов", default=0)

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        ordering = ("poll", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("poll", "text"),
                name="unique_choice_text_per_poll",
            )
        ]

    def __str__(self):
        return self.text


class Vote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Пользователь",
    )
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Голосование",
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Выбранный вариант",
    )
    voted_at = models.DateTimeField("Дата голосования", auto_now_add=True)

    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"
        ordering = ("-voted_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "poll"),
                name="unique_vote_per_user_and_poll",
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.poll.title}"

    def clean(self):
        super().clean()
        if self.choice_id and self.poll_id and self.choice.poll_id != self.poll_id:
            raise ValidationError(
                {"choice": "Выбранный вариант не относится к этому голосованию."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class LearningResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_results",
        verbose_name="Пользователь",
    )
    stage_title = models.CharField("Название этапа / задания", max_length=200)
    points = models.PositiveIntegerField(
        "Баллы",
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
    )
    is_successful = models.BooleanField("Успешно пройдено", default=False)
    created_at = models.DateTimeField("Дата добавления результата", auto_now_add=True)

    class Meta:
        verbose_name = "Результат обучения"
        verbose_name_plural = "Результаты обучения"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username}: {self.stage_title} ({self.points})"

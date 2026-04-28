import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Choice, LearningResult, Poll, Profile, Vote


User = get_user_model()


class Command(BaseCommand):
    help = "Создает демонстрационные данные для готового сайта."

    def handle(self, *args, **options):
        with transaction.atomic():
            admin_user = self.ensure_user(
                username=os.environ.get("DEMO_ADMIN_USERNAME", "admin_demo"),
                password=os.environ.get("DEMO_ADMIN_PASSWORD", "SkazkaAdmin2026!"),
                email=os.environ.get("DEMO_ADMIN_EMAIL", "admin@severnaya-skazka.local"),
                age=11,
                class_group="Педагог",
                is_staff=True,
                is_superuser=True,
            )

            vera = self.ensure_user(
                username=os.environ.get("DEMO_STUDENT_USERNAME", "vera"),
                password=os.environ.get("DEMO_STUDENT_PASSWORD", "SkazkaStudent2026!"),
                email="vera@example.com",
                age=9,
                class_group="2А",
            )
            liza = self.ensure_user(
                username="liza",
                password="SkazkaStudent2026!",
                email="liza@example.com",
                age=10,
                class_group="3Б",
            )
            egor = self.ensure_user(
                username="egor",
                password="SkazkaStudent2026!",
                email="egor@example.com",
                age=8,
                class_group="1В",
            )

            active_symbol_poll = self.ensure_poll(
                title="Какой северный символ тебе нравится больше всего?",
                description="Выбери символ, который больше всего напоминает тебе о северной культуре.",
                end_date=timezone.now() + timedelta(days=14),
                is_active=True,
                choices=[
                    "Снежинка",
                    "Северный олень",
                    "Северный орнамент",
                ],
            )
            active_tale_poll = self.ensure_poll(
                title="Какую сказку ты бы прочитал(а) сегодня?",
                description="Выбери сказку, которую тебе было бы интересно прочитать на занятии.",
                end_date=timezone.now() + timedelta(days=10),
                is_active=True,
                choices=[
                    "Морозко",
                    "Снегурочка",
                    "Серебряное копытце",
                ],
            )
            closed_color_poll = self.ensure_poll(
                title="Какой цвет подойдёт для народного узора?",
                description="Пример завершенного голосования с уже готовыми результатами.",
                end_date=timezone.now() - timedelta(days=3),
                is_active=True,
                choices=[
                    "Синий",
                    "Красный",
                    "Золотой",
                ],
            )

            self.ensure_learning_result(vera, "Орнамент северного края", 18, True)
            self.ensure_learning_result(vera, "Народная сказка", 15, True)
            self.ensure_learning_result(liza, "Роспись деревянной игрушки", 20, True)
            self.ensure_learning_result(liza, "Северные традиции", 17, True)
            self.ensure_learning_result(egor, "Знакомство с символами Севера", 12, True)
            self.ensure_learning_result(egor, "Цвета народного узора", 10, False)

            self.ensure_vote(vera, active_symbol_poll, "Северный орнамент")
            self.ensure_vote(liza, active_symbol_poll, "Снежинка")
            self.ensure_vote(egor, active_symbol_poll, "Северный олень")
            self.ensure_vote(vera, active_tale_poll, "Морозко")
            self.ensure_vote(liza, active_tale_poll, "Снегурочка")
            self.ensure_vote(egor, closed_color_poll, "Синий")

            for user in (vera, liza, egor):
                user.profile.update_total_rating()

        self.stdout.write(self.style.SUCCESS("Демо-данные сайта готовы."))
        self.stdout.write(
            f"Администратор: {admin_user.username} / "
            f"{os.environ.get('DEMO_ADMIN_PASSWORD', 'SkazkaAdmin2026!')}"
        )
        self.stdout.write(
            f"Ученик: {vera.username} / "
            f"{os.environ.get('DEMO_STUDENT_PASSWORD', 'SkazkaStudent2026!')}"
        )

    def ensure_user(
        self,
        username,
        password,
        email,
        age,
        class_group,
        is_staff=False,
        is_superuser=False,
    ):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )

        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True
        user.set_password(password)
        changed = True
        if changed:
            user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile_changed = False
        if profile.age != age:
            profile.age = age
            profile_changed = True
        if profile.class_group != class_group:
            profile.class_group = class_group
            profile_changed = True
        if profile_changed:
            profile.save()
        return user

    def ensure_poll(self, title, description, end_date, is_active, choices):
        poll, _ = Poll.objects.get_or_create(
            title=title,
            defaults={
                "description": description,
                "end_date": end_date,
                "is_active": is_active,
            },
        )
        poll_changed = False
        if poll.description != description:
            poll.description = description
            poll_changed = True
        if poll.end_date != end_date:
            poll.end_date = end_date
            poll_changed = True
        if poll.is_active != is_active:
            poll.is_active = is_active
            poll_changed = True
        if poll_changed:
            poll.save()

        for choice_text in choices:
            Choice.objects.get_or_create(poll=poll, text=choice_text)
        return poll

    def ensure_learning_result(self, user, stage_title, points, is_successful):
        learning_result = user.learning_results.filter(stage_title=stage_title).first()
        if learning_result is None:
            LearningResult.objects.create(
                user=user,
                stage_title=stage_title,
                points=points,
                is_successful=is_successful,
            )
            return

        changed = False
        if learning_result.points != points:
            learning_result.points = points
            changed = True
        if learning_result.is_successful != is_successful:
            learning_result.is_successful = is_successful
            changed = True
        if changed:
            learning_result.save()

    def ensure_vote(self, user, poll, choice_text):
        choice = Choice.objects.get(poll=poll, text=choice_text)
        Vote.objects.get_or_create(
            user=user,
            poll=poll,
            defaults={"choice": choice},
        )

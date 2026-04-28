from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Choice, LearningResult, Poll, Vote


User = get_user_model()


class ProfileAndLearningResultTests(TestCase):
    def test_profile_created_and_total_rating_recalculated(self):
        user = User.objects.create_user(username="masha", password="secret123")

        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.total_rating, 0)

        first_result = LearningResult.objects.create(
            user=user,
            stage_title="Роспись игрушки",
            points=15,
            is_successful=True,
        )
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.total_rating, 15)

        LearningResult.objects.create(
            user=user,
            stage_title="Северный орнамент",
            points=10,
            is_successful=False,
        )
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.total_rating, 25)

        first_result.delete()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.total_rating, 10)

    def test_vote_adds_bonus_point_to_total_rating(self):
        user = User.objects.create_user(username="kolya", password="secret123")
        poll = Poll.objects.create(
            title="Любимый узор",
            description="Выберите любимый северный узор",
            end_date=timezone.now() + timedelta(days=3),
            is_active=True,
        )
        choice = Choice.objects.create(poll=poll, text="Снежинка")

        LearningResult.objects.create(
            user=user,
            stage_title="Рисунок узора",
            points=12,
            is_successful=True,
        )
        Vote.objects.create(user=user, poll=poll, choice=choice)

        user.profile.refresh_from_db()
        self.assertEqual(user.profile.learning_points, 12)
        self.assertEqual(user.profile.vote_points, 1)
        self.assertEqual(user.profile.total_rating, 13)


class VoteModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ivan", password="secret123")
        self.poll = Poll.objects.create(
            title="Любимая северная сказка",
            description="Выберите любимую сказку",
            end_date=timezone.now() + timedelta(days=3),
            is_active=True,
        )
        self.choice_one = Choice.objects.create(poll=self.poll, text="Морозко")
        self.choice_two = Choice.objects.create(poll=self.poll, text="Садко")

    def test_user_cannot_vote_twice_in_one_poll(self):
        Vote.objects.create(user=self.user, poll=self.poll, choice=self.choice_one)
        duplicate_vote = Vote(user=self.user, poll=self.poll, choice=self.choice_two)

        with self.assertRaises(ValidationError):
            duplicate_vote.full_clean()

    def test_choice_counter_is_updated_after_vote_create_and_delete(self):
        vote = Vote.objects.create(user=self.user, poll=self.poll, choice=self.choice_one)
        self.choice_one.refresh_from_db()
        self.assertEqual(self.choice_one.votes_count, 1)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.total_rating, 1)

        vote.delete()
        self.choice_one.refresh_from_db()
        self.assertEqual(self.choice_one.votes_count, 0)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.total_rating, 0)

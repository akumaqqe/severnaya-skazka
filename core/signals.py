from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Choice, LearningResult, Profile, Vote


User = get_user_model()


def refresh_choice_vote_count(choice_id):
    votes_count = Vote.objects.filter(choice_id=choice_id).count()
    Choice.objects.filter(pk=choice_id).update(votes_count=votes_count)


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=LearningResult)
@receiver(post_delete, sender=LearningResult)
def update_profile_rating(sender, instance, **kwargs):
    instance.user.profile.update_total_rating()


@receiver(pre_save, sender=Vote)
def remember_previous_choice(sender, instance, **kwargs):
    if instance.pk:
        previous_vote = sender.objects.filter(pk=instance.pk).only("choice_id").first()
        instance._previous_choice_id = previous_vote.choice_id if previous_vote else None
    else:
        instance._previous_choice_id = None


@receiver(post_save, sender=Vote)
def sync_choice_vote_count_after_save(sender, instance, **kwargs):
    refresh_choice_vote_count(instance.choice_id)
    instance.user.profile.update_total_rating()
    previous_choice_id = getattr(instance, "_previous_choice_id", None)
    if previous_choice_id and previous_choice_id != instance.choice_id:
        refresh_choice_vote_count(previous_choice_id)


@receiver(post_delete, sender=Vote)
def sync_choice_vote_count_after_delete(sender, instance, **kwargs):
    refresh_choice_vote_count(instance.choice_id)
    instance.user.profile.update_total_rating()

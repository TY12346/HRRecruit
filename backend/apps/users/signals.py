from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, create_profile_for_user


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        create_profile_for_user(instance)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile instance when a new User is created.
    This ensures Google Login users get a profile with free tokens.
    """
    if created:
        Profile.objects.create(
            user=instance,
            tokens=5,           # Default free tokens
            max_tokens=5,       # Default max tokens
            subscription='free',
            balance=0.00        # Default balance
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the Profile instance whenever the User object is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
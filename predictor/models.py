# predictor/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# import uuid  # Import for UUID generation
from django.core.exceptions import ValidationError
from django.db import transaction
from accounts.models import Profile

def generate_signal_id():
    return 'PRED-' + timezone.now().strftime("%Y%m%d%H%M%S")

class Prediction(models.Model):
    signal_id = models.CharField(max_length=30, unique=True, default=generate_signal_id, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.CharField(max_length=20)  # For symbol (e.g., BTC-USD)
    timeframe = models.CharField(max_length=10)  # e.g., 15m, 1h, D
    direction = models.CharField(max_length=50)  # e.g., UP, DOWN
    # impact_time = models.DateField(default=timezone.now)
    impact_time = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Added feedback field for Like/Dislike feature
    FEEDBACK_CHOICES = [
        ('LIKE', 'Like'),
        ('DISLIKE', 'Dislike'),
    ]
    feedback = models.CharField(max_length=10, choices=FEEDBACK_CHOICES, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:  # If updating an existing instance, just save without token check/deduction
            super().save(*args, **kwargs)
            return
        with transaction.atomic():  # Ensure atomicity for new predictions: check, save, deduct
            profile = self.user.profile
            if profile.tokens <= 0:
                raise ValidationError('Insufficient tokens. Please upgrade your subscription or refill tokens.')
            super().save(*args, **kwargs)
            profile.tokens -= 1
            profile.save()

    def __str__(self):
        return f"{self.signal_id} - {self.asset} - {self.direction} ({self.timeframe})" if self.signal_id else f"{self.asset} - {self.direction} ({self.timeframe})"

    class Meta:
        ordering = ['-created_at']

# --- Added Economic Calendar Model ---
class EconomicCalendar(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    data = models.JSONField(default=dict)  # Stores the full API response

    def __str__(self):
        return f"Calendar Data (Last Updated: {self.updated_at})"

    class Meta:
        verbose_name = "Economic Calendar"
        verbose_name_plural = "Economic Calendar"
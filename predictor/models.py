# predictor/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# import uuid  # Import for UUID generation

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

    def __str__(self):
        return f"{self.signal_id} - {self.asset} - {self.direction} ({self.timeframe})" if self.signal_id else f"{self.asset} - {self.direction} ({self.timeframe})"

    class Meta:
        ordering = ['-created_at']
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction

TIMEZONE_CHOICES = [
    ('UTC', 'UTC'),
    ('EST', 'Eastern Time (EST/EDT)'),
    ('CST', 'Central Time (CST/CDT)'),
    ('MST', 'Mountain Time (MST/MDT)'),
    ('PST', 'Pacific Time (PST/PDT)'),
    ('GMT', 'London (GMT/BST)'),
    ('CET', 'Central European Time (CET/CEST)'),
]

THEME_CHOICES = [
    ('system', 'System Default'),
    ('light', 'Light Mode'),
    ('dark', 'Dark Mode'),
]

class Profile(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="User's balance in USDT")
    subscription = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_start_date = models.DateTimeField(blank=True, null=True)
    subscription_end_date = models.DateTimeField(blank=True, null=True)
    tokens = models.IntegerField(default=0, help_text="User's available tokens")
    max_tokens = models.IntegerField(default=10, help_text="Maximum tokens allowed based on subscription")
    timezone = models.CharField(max_length=10, choices=TIMEZONE_CHOICES, default='EST')
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    auto_renew_subscription = models.BooleanField(default=False)
    auto_refill_tokens = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        # Ensure max_tokens is set based on subscription type
        if self.subscription == 'free':
            self.max_tokens = 10
        elif self.subscription == 'premium':
            self.max_tokens = 100

        # Auto-refill logic
        if self.auto_refill_tokens and self.tokens < 1 and self.subscription == 'premium':
            subscription_settings = SubscriptionSettings.objects.first()
            effective_price = subscription_settings.effective_price if subscription_settings else 5.00
            if self.balance >= effective_price:
                now = timezone.now()
                with transaction.atomic():
                    self.tokens = self.max_tokens
                    PaymentHistory.objects.create(
                        user=self.user,
                        payment_type='refill',
                        currency='USDT',
                        amount=effective_price,
                        payment_method='Auto-Refill',
                        transaction_id=f"AUTO_REFILL_{self.user.id}_{now.strftime('%Y%m%d%H%M%S')}",
                        status='successful',
                        payment_note='Auto-refilled tokens due to low balance',
                    )
            else:
                # Insufficient balance: disable auto_refill_tokens and record failed attempt
                with transaction.atomic():
                    self.auto_refill_tokens = False
                    PaymentHistory.objects.create(
                        user=self.user,
                        payment_type='refill',
                        currency='USDT',
                        amount=effective_price,
                        payment_method='Auto-Refill',
                        transaction_id=f"AUTO_REFILL_FAILED_{self.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        status='cancelled',
                        payment_note='Auto-refill failed: insufficient balance',
                        remark='Auto-refill disabled due to insufficient balance'
                    )

        super().save(*args, **kwargs)

class PaymentHistory(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('subscription', 'Subscription'),
        ('withdraw', 'Withdraw'),
        ('bonus', 'Bonus'),
        ('refill', 'Token Refill'),
    ]

    STATUS_CHOICES = [
        ('successful', 'Successful'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('partially_paid', 'Partially Paid'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_history')
    payment_id = models.AutoField(primary_key=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    currency = models.CharField(max_length=10, default='USDT')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    payment_method = models.CharField(max_length=50, default='Binance Pay')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_note = models.TextField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.username} - {self.payment_type}"

    def clean(self):
        """
        Validates that amount is set when status is 'successful'.
        """
        super().clean()
        if self.status == 'successful' and self.amount is None:
            raise ValidationError({
                'amount': 'Amount is required for successful payments.'
            })

    class Meta:
        verbose_name = 'Payment History'
        verbose_name_plural = 'Payment Histories'

@receiver(pre_save, sender=PaymentHistory)
def pre_save_payment(sender, instance, **kwargs):
    if instance.pk:  # If updating an existing instance
        old_instance = PaymentHistory.objects.get(pk=instance.pk)
        instance._old_status = old_instance.status
    else:
        instance._old_status = None  # For new instances

@receiver(post_save, sender=PaymentHistory)
def post_save_payment(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    if instance.status == 'successful' and old_status != 'successful':
        profile = instance.user.profile
        amount = instance.amount
        if amount is None:  # Skip if amount is None
            return
        if instance.payment_type in ['deposit', 'bonus']:
            profile.balance += amount
        elif instance.payment_type in ['subscription', 'withdraw', 'refill']:
            if profile.balance < amount:
                instance.status = 'cancelled'
                instance.remark = 'Insufficient balance'
                instance.save()
                return
            profile.balance -= amount
        profile.save()

# New model for subscription settings
class SubscriptionSettings(models.Model):
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        help_text="Regular price for subscription (in USDT)"
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Discounted price for subscription (in USDT; optional)"
    )
    is_discounted = models.BooleanField(
        default=False,
        help_text="If checked, the discounted price will be used as the effective price"
    )

    def clean(self):
        """
        Validates that the discounted_price is less than the regular price
        if discounted_price is provided.
        """
        super().clean()
        if self.discounted_price is not None:
            if self.discounted_price >= self.price:
                raise ValidationError({
                    'discounted_price': 'Discounted price must be less than the regular price.'
                })

    def __str__(self):
        return "Subscription Settings"

    @property
    def effective_price(self):
        """
        Returns the current effective price based on discount status.
        """
        if self.is_discounted and self.discounted_price is not None:
            return self.discounted_price
        return self.price

    class Meta:
        verbose_name = "Subscription Settings"
        verbose_name_plural = "Subscription Settings"
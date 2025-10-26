from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from django.db import transaction
from .models import Profile, PaymentHistory, SubscriptionSettings  # Import additional models

def check_expired_subscriptions():
    """
    Checks for expired premium subscriptions and attempts to auto-renew them if enabled and balance is sufficient.
    If renewal fails or is not enabled, downgrades to free and resets tokens to default allocation.
    Runs daily at the scheduled time.
    """
    now = timezone.now()
    expired_profiles = Profile.objects.filter(
        subscription='premium',
        subscription_end_date__lt=now
    )
    subscription_settings = SubscriptionSettings.objects.first()
    effective_price = subscription_settings.effective_price if subscription_settings else 5.00  # Fallback price

    for profile in expired_profiles:
        with transaction.atomic():  # Ensure atomic updates
            if profile.auto_renew_subscription and profile.balance >= effective_price:
                # Attempt auto-renewal
                PaymentHistory.objects.create(
                    user=profile.user,
                    payment_type='subscription',
                    currency='USDT',
                    amount=effective_price,
                    payment_method='Auto-Renewal',
                    transaction_id=f"AUTO_RENEW_{profile.user.id}_{now.strftime('%Y%m%d%H%M%S')}",
                    status='successful',
                    payment_note='Auto-renewed premium subscription',
                )
                profile.subscription_start_date = now
                profile.subscription_end_date = now + timezone.timedelta(days=30)
                profile.tokens = 3000  # Reset to premium tier tokens
                profile.max_tokens = 3000  # Set max tokens for premium tier
                profile.save()
            else:
                # Downgrade to free
                profile.subscription = 'free'
                profile.subscription_start_date = None  # Optional: Clear dates
                profile.subscription_end_date = None    # Optional: Clear dates
                profile.tokens = 5                      # Reset to default free tier tokens
                profile.max_tokens = 5                  # Set max tokens for free tier
                if profile.auto_renew_subscription:
                    profile.auto_renew_subscription = False  # Turn off auto-renewal if balance insufficient
                profile.save()
    print(f"Checked subscriptions at {now}. Downgraded {expired_profiles.count()} users.")  # For logging/debug

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Add the job with cron trigger: every day at 00:00 (midnight)
    # Adjust hour/minute as needed, e.g., CronTrigger(hour=23, minute=59) for 11:59 PM
    # Timezone defaults to system time; align with your 'Asia/Dhaka' if needed via timezone='Asia/Dhaka'

    scheduler.add_job(
        check_expired_subscriptions,
        trigger=CronTrigger(hour=22, minute=5),
        id='check_subscriptions',  # Unique ID for the job
        replace_existing=True      # Overwrite if already exists (handles restarts)
    )
    scheduler.start()
    print("Scheduler started for daily subscription checks.")

"""
Drawbacks/Notes: In dev, if you restart the server, 
the scheduler restarts (potential duplicate runs, 
but idempotent checks in your task prevent issues). 
For production, add persistence (e.g., via database job store), 
but that's future-proofing.
"""
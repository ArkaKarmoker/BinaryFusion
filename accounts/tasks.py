from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from .models import Profile  # Import your Profile model

def check_expired_subscriptions():
    """
    Checks for expired premium subscriptions and downgrades them to free.
    Runs daily at the scheduled time.
    """
    now = timezone.now()
    expired_profiles = Profile.objects.filter(
        subscription='premium',
        subscription_end_date__lt=now
    )
    for profile in expired_profiles:
        profile.subscription = 'free'
        profile.subscription_start_date = None  # Optional: Clear dates
        profile.subscription_end_date = None    # Optional: Clear dates
        profile.save()
    print(f"Checked subscriptions at {now}. Downgraded {expired_profiles.count()} users.")  # For logging/debug

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Add the job with cron trigger: every day at 00:00 (midnight)
    # Adjust hour/minute as needed, e.g., CronTrigger(hour=23, minute=59) for 11:59 PM
    # Timezone defaults to system time; align with your 'Asia/Dhaka' if needed via timezone='Asia/Dhaka'

    scheduler.add_job(
        check_expired_subscriptions,
        trigger=CronTrigger(hour=00, minute=00),
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
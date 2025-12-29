from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # 1. Register Signals (Crucial for Google Login to create Profiles)
        import accounts.signals

        # 2. Start the Scheduler (Crucial for Subscription management)
        import accounts.tasks
        accounts.tasks.start_scheduler()
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, PaymentHistory, SubscriptionSettings
from predictor.models import Prediction

# Define an inline admin descriptor for the Profile model
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# Define an inline admin descriptor for the PaymentHistory model
class PaymentHistoryInline(admin.StackedInline):
    model = PaymentHistory
    can_delete = False
    verbose_name_plural = 'PaymentHistory'
    fields = ('payment_type', 'currency', 'amount', 'payment_method', 'transaction_id', 'status', 'payment_note', 'remark', 'created_at', 'last_updated')
    readonly_fields = ('created_at', 'last_updated')
    extra = 0

# Define an inline admin descriptor for the Prediction model
class PredictionInline(admin.TabularInline):
    model = Prediction
    can_delete = True
    verbose_name_plural = 'Predictions'
    fields = ('asset', 'timeframe', 'direction', 'impact_time', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0
    show_change_link = True

# Define a custom UserAdmin that includes only the Profile inline
class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
    # Add custom fields to display in the user list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'subscription_status', 'total_predictions', 'total_predictions_all_users')
    
    # Add filtering by subscription type and other common fields
    list_filter = ('profile__subscription', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def subscription_status(self, obj):
        """Display the user's subscription status from Profile."""
        try:
            return obj.profile.subscription
        except Profile.DoesNotExist:
            return 'N/A'
    subscription_status.short_description = 'Subscription'
    
    def total_predictions(self, obj):
        return Prediction.objects.filter(user=obj).count()
    total_predictions.short_description = 'User Predictions'
    
    def total_predictions_all_users(self, obj):
        return Prediction.objects.count()
    total_predictions_all_users.short_description = 'Total Predictions (All Users)'

# Define a custom admin for PaymentHistory
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'payment_type', 'currency', 'amount', 'payment_method', 'transaction_id', 'status', 'payment_note', 'remark', 'created_at', 'last_updated')
    list_filter = ('payment_type', 'status', 'created_at')
    search_fields = ('user__username', 'transaction_id', 'payment_note')
    list_editable = ('amount', 'status', 'remark')
    readonly_fields = ('created_at', 'last_updated')
    list_per_page = 10

    def get_readonly_fields(self, request, obj=None):
        # Ensure fields like currency and payment_method remain non-editable
        return ('created_at', 'last_updated', 'currency', 'payment_method')

# Define a custom admin for Prediction
class PredictionAdmin(admin.ModelAdmin):
    # Added feedback_emoji to the list display
    list_display = ('user', 'asset', 'timeframe', 'direction', 'impact_time', 'feedback_emoji', 'created_at')
    # Added feedback to filters
    list_filter = ('user', 'asset', 'direction', 'feedback', 'created_at')
    search_fields = ('user__username', 'asset')
    readonly_fields = ('created_at', 'impact_time')
    list_per_page = 10
    ordering = ['-created_at']

    def feedback_emoji(self, obj):
        if obj.feedback == 'LIKE':
            return '👍'
        elif obj.feedback == 'DISLIKE':
            return '👎'
        return '-'
    
    feedback_emoji.short_description = 'Feedback'

# New admin for SubscriptionSettings
class SubscriptionSettingsAdmin(admin.ModelAdmin):
    list_display = ('price', 'discounted_price', 'is_discounted')
    fields = ('price', 'discounted_price', 'is_discounted')

    def has_add_permission(self, request):
        # Allow only one instance to be created
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

# Unregister the default UserAdmin
admin.site.unregister(User)

# Register the User model with the custom UserAdmin
admin.site.register(User, CustomUserAdmin)

# Register the Prediction model with the custom PredictionAdmin
admin.site.register(Prediction, PredictionAdmin)

# Register the PaymentHistory model with the custom PaymentHistoryAdmin
admin.site.register(PaymentHistory, PaymentHistoryAdmin)

# Register the new SubscriptionSettings model
admin.site.register(SubscriptionSettings, SubscriptionSettingsAdmin)
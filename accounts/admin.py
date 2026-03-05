from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, PaymentHistory, SubscriptionSettings, SiteContent # <--- ADDED: SiteContent
from predictor.models import Prediction, EconomicCalendar
from django.utils.safestring import mark_safe 
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
import accounts.tasks as tasks 

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

# --- ADDED: Admin for Site Content (Deposit Instructions) ---
class SiteContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Allow only one instance to be created
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

# --- Updated Admin for Economic Calendar ---
class EconomicCalendarAdmin(admin.ModelAdmin):
    # Added 'refresh_button' to list display so you can click it from the list view too
    list_display = ('__str__', 'updated_at', 'event_count', 'refresh_button')
    readonly_fields = ('updated_at', 'display_json_as_table')
    fields = ('updated_at', 'display_json_as_table')

    # --- Inject DataTables & jQuery ---
    class Media:
        css = {
            'all': ('https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css',)
        }
        js = (
            'https://code.jquery.com/jquery-3.7.0.min.js',
            'https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js',
        )

    # 1. Allow the "Add" button to appear (so we can hijack it)
    def has_add_permission(self, request):
        return True

    # 2. HIJACK the Add View. 
    # This turns the "Add Economic Calendar" button into a "Fetch API" action.
    def add_view(self, request, form_url='', extra_context=None):
        try:
            tasks.update_economic_calendar()
            self.message_user(request, "Economic Calendar successfully refreshed/created from API.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error updating calendar: {str(e)}", messages.ERROR)
        
        # Always redirect back to the list view
        return HttpResponseRedirect(reverse('admin:predictor_economiccalendar_changelist'))

    # 3. Add a button INSIDE the table row as well
    def refresh_button(self, obj):
        return mark_safe(
            '<a class="button" href="update-api/" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; text-decoration: none;">🔄 Reload Data</a>'
        )
    refresh_button.short_description = "Actions"
    refresh_button.allow_tags = True

    def event_count(self, obj):
        if obj.data and 'count' in obj.data:
            return obj.data['count']
        return 0
    event_count.short_description = 'Total Events'

    # 4. Render DataTable with ALL COLUMNS using mark_safe
    def display_json_as_table(self, obj):
        """
        Formats the JSON data into a valid HTML table and injects JS
        to initialize DataTables and rename the 'Add' button.
        """
        if not obj.data or 'events' not in obj.data:
            return mark_safe('<div style="padding:20px; color:red;"><b>⚠️ No data found.</b><br>Please click the <b>"Reload"</b> button above to fetch data from the API.</div>')
        
        events = obj.data['events']
        
        # Start HTML Table with ID for DataTables
        html = '<div style="margin-top: 15px;">'
        html += '<table id="economic-calendar-table" class="display" style="width:100%; border:1px solid #ddd;">'
        html += '<thead>'
        html += '<tr>'
        # Added ALL columns present in typical forex factory JSON
        html += '<th>Date</th>'
        html += '<th>Time</th>'
        html += '<th>Cur</th>'
        html += '<th>Country</th>'
        html += '<th>Event</th>'
        html += '<th>Impact</th>'
        html += '<th>Prev</th>'
        html += '<th>Fcst</th>'
        html += '<th>Actual</th>'
        html += '</tr>'
        html += '</thead>'
        html += '<tbody>'
        
        for event in events:
            # Color code impact
            impact = event.get("impact", "")
            impact_color = "inherit"
            if "High" in impact: impact_color = "#ef4444" # Red
            elif "Medium" in impact: impact_color = "#f59e0b" # Orange
            elif "Low" in impact: impact_color = "#10b981" # Green
            
            # Extract Date and Time from utc_datetime (Format: "YYYY-MM-DD HH:MM:SS")
            raw_datetime = event.get("utc_datetime", "")
            date_part = raw_datetime.split(" ")[0] if " " in raw_datetime else raw_datetime
            time_part = raw_datetime.split(" ")[1][:5] if " " in raw_datetime else "" # Get HH:MM

            html += '<tr>'
            html += f'<td>{date_part}</td>'
            html += f'<td>{time_part}</td>'
            html += f'<td>{event.get("currency", "")}</td>'
            html += f'<td>{event.get("country", "")}</td>'
            html += f'<td>{event.get("title", "")}</td>'
            html += f'<td style="color:{impact_color}; font-weight:bold;">{impact}</td>'
            html += f'<td>{event.get("previous", "")}</td>'
            html += f'<td>{event.get("forecast", "")}</td>'
            html += f'<td>{event.get("actual", "")}</td>'
            html += '</tr>'
        
        html += '</tbody></table></div>'

        # Inject JavaScript:
        # 1. Initialize DataTable
        # 2. Rename the top-right "Add" button to "Reload"
        # NOTE: We use mark_safe() at the end, so {} are preserved.
        html += """
        <script>
            (function($) {
                $(document).ready(function() {
                    // 1. Initialize DataTable
                    try {
                        if (!$.fn.DataTable.isDataTable('#economic-calendar-table')) {
                            $('#economic-calendar-table').DataTable({
                                "pageLength": 25,
                                "order": [[ 0, "asc" ], [ 1, "asc" ]], // Sort by Date then Time
                                "responsive": true,
                                "language": {
                                    "search": "Search Events:"
                                }
                            });
                        }
                    } catch (e) {
                        console.error("DataTables Error:", e);
                    }

                    // 2. Rename the default Django Admin "Add" button
                    var addBtn = $('.object-tools .addlink');
                    if (addBtn.length) {
                        addBtn.html('🔄 Reload / Fetch Data');
                        addBtn.css({
                            'background-color': '#28a745', 
                            'background-image': 'none',
                            'border-color': '#1e7e34',
                            'color': '#fff',
                            'text-transform': 'uppercase',
                            'font-weight': 'bold',
                            'box-shadow': 'none'
                        });
                        // The functionality is handled by the python add_view override
                    }
                });
            })(jQuery || django.jQuery);
        </script>
        """
        
        return mark_safe(html)
    
    display_json_as_table.short_description = "Calendar Data (DataTable)"

    # Helper URL for the row-button
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-api/', self.admin_site.admin_view(self.trigger_update_view), name='update-calendar-api'),
        ]
        return custom_urls + urls

    def trigger_update_view(self, request):
        try:
            tasks.update_economic_calendar()
            self.message_user(request, "Economic Calendar updated successfully from API.", messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Error triggering update: {e}", messages.ERROR)
        return HttpResponseRedirect("../")

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

# Register the Economic Calendar
admin.site.register(EconomicCalendar, EconomicCalendarAdmin)

# --- ADDED: Register the new SiteContent model ---
admin.site.register(SiteContent, SiteContentAdmin)
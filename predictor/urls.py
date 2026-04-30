from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("app/", views.app, name="app"),
    path("symbol-suggestions/", views.symbol_suggestions, name="symbol_suggestions"),
    path("submit-feedback/", views.submit_feedback, name="submit_feedback"),
    # --- New API Endpoint ---
    path('api/calendar-data/', views.get_calendar_data, name='calendar_data'),
]
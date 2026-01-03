from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", RedirectView.as_view(url="/app/", permanent=False), name="root_redirect"),
    path("app/", views.app, name="app"),
    path("symbol-suggestions/", views.symbol_suggestions, name="symbol_suggestions"),
    path("submit-feedback/", views.submit_feedback, name="submit_feedback"),
]
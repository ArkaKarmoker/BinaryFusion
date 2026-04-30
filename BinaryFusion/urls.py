"""
URL configuration for BinaryFusion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Added for media serving
from django.conf.urls.static import static # Added for media serving
from django.views.generic import RedirectView # রিডাইরেক্ট করার জন্য ইম্পোর্ট করা হয়েছে
from . import views

# --- ADDED: Custom Admin Panel Titles ---
admin.site.site_header = "BinaryFusion Administration"
admin.site.site_title = "BinaryFusion Admin Portal"
admin.site.index_title = "Welcome to BinaryFusion Admin Portal"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("home/", RedirectView.as_view(url='/', permanent=True)),
    path("", include("predictor.urls")),
    path("accounts/", include("accounts.urls")),  # Added accounts URLs
    path("accounts/", include("allauth.urls")),   # Added allauth URLs
    path("tinymce/", include("tinymce.urls")),    # <--- ADDED: TinyMCE URLs for the rich text editor
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
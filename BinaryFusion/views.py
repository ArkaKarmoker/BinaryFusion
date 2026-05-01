from django.shortcuts import render, redirect
from accounts.models import SubscriptionSettings

def home(request):
    # if request.user.is_authenticated:
    #     return redirect('app') # Optional: Auto-redirect logged in users to the dashboard
    
    # --- ADDED: Fetch Subscription Settings to pass to template ---
    sub_settings = SubscriptionSettings.objects.first()
    
    context = {
        'sub_settings': sub_settings,
    }
    return render(request, 'index.html', context)

def terms_of_service(request):
    return render(request, 'terms.html')

def privacy_policy(request):
    return render(request, 'privacy.html')
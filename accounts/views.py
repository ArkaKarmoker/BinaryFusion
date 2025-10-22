from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import RegistrationForm, EditProfileForm, ChangePasswordForm, DepositForm
from .models import Profile, PaymentHistory, SubscriptionSettings
from predictor.models import Prediction
from django.utils import timezone
from datetime import timedelta
import pytz
from django.db.models import Count

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                user.save()
                # Create a Profile instance for the new user
                Profile.objects.create(user=user, tokens=10, max_tokens=10)
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/registration.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('app')  # Redirect to predictor/app.html
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user, tokens=10, max_tokens=10)
    
    # Initialize forms to avoid UnboundLocalError
    form = EditProfileForm(instance=profile, user=request.user)
    change_password_form = ChangePasswordForm()
    deposit_form = DepositForm(user=request.user)  # Pass user to DepositForm

    # Fetch subscription price from SubscriptionSettings
    subscription_settings = SubscriptionSettings.objects.first()
    if subscription_settings:
        effective_price = subscription_settings.effective_price
        regular_price = subscription_settings.price
        is_discounted = subscription_settings.is_discounted
    else:
        effective_price = 5.00  # Default effective price
        regular_price = 5.00    # Default regular price
        is_discounted = False    # Default discount status

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = EditProfileForm(request.POST, instance=profile, user=request.user)
            if form.is_valid():
                form.save()
                # Update the user object
                user = request.user
                user.first_name = form.cleaned_data.get('first_name', user.first_name)
                user.last_name = form.cleaned_data.get('last_name', user.last_name)
                user.username = form.cleaned_data.get('username', user.username)
                user.email = form.cleaned_data.get('email', user.email)
                user.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Profile updated successfully.',
                        'user': {
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'username': user.username,
                            'email': user.email,
                            'date_joined': user.date_joined.strftime('%B %d, %Y'),
                            'last_login': user.last_login.strftime('%B %d, %Y') if user.last_login else 'N/A'
                        }
                    })
                messages.success(request, 'Profile updated successfully.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please correct the errors below.',
                        'errors': form.errors
                    })
                messages.error(request, 'Please correct the errors below.')
        elif 'change_password' in request.POST:
            change_password_form = ChangePasswordForm(request.POST)
            if change_password_form.is_valid():
                current_password = change_password_form.cleaned_data['current_password']
                new_password = change_password_form.cleaned_data['new_password']
                user = authenticate(username=request.user.username, password=current_password)
                if user is not None:
                    user.set_password(new_password)
                    user.save()
                    logout(request)  # Log out the user after password change
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Password changed successfully. You have been logged out.',
                            'logout': True  # Indicate logout for client-side handling
                        })
                    messages.success(request, 'Password changed successfully. Please log in again.')
                    return redirect('login')
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Current password is incorrect.'
                        })
                    messages.error(request, 'Current password is incorrect.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please correct the errors below.',
                        'errors': change_password_form.errors
                    })
                messages.error(request, 'Please correct the errors below.')
        elif 'deposit' in request.POST:
            deposit_form = DepositForm(request.POST, user=request.user)  # Pass user to DepositForm
            if deposit_form.is_valid():
                payment = PaymentHistory.objects.create(
                    user=request.user,
                    payment_type='deposit',
                    currency='USDT',
                    amount=None,  # Initially blank
                    payment_method='Binance Pay',
                    transaction_id=deposit_form.cleaned_data['transaction_id'],
                    payment_note=deposit_form.cleaned_data['payment_note'],
                    status='pending'
                )
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Deposit request submitted successfully. Awaiting admin approval.',
                        'payment': {
                            'payment_id': payment.payment_id,
                            'created_at': payment.created_at.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%B %d, %Y'),
                            'payment_type': payment.get_payment_type_display(),
                            'currency': payment.currency,
                            'amount': str(payment.amount) if payment.amount is not None else '',
                            'payment_method': payment.payment_method,
                            'transaction_id': payment.transaction_id or '-',
                            'status': payment.get_status_display()
                        }
                    })
                messages.success(request, 'Deposit request submitted successfully. Awaiting admin approval.', extra_tags='deposit')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Please correct the errors below.',
                        'errors': deposit_form.errors
                    })
                messages.error(request, 'Please correct the errors below.', extra_tags='deposit')
        elif 'subscribe' in request.POST:
            # Handle subscription request
            if profile.subscription == 'premium' and profile.subscription_end_date > timezone.now() and profile.tokens > 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'You are already subscribed to Premium with active tokens.'
                    })
                messages.error(request, 'You are already subscribed to Premium with active tokens.', extra_tags='subscription')
            else:
                # Get subscription price
                subscription_price = subscription_settings.effective_price if subscription_settings else 5.00
                # Check balance
                if profile.balance < subscription_price:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Insufficient balance. You need {subscription_price} USDT.'
                        })
                    messages.error(request, f'Insufficient balance. You need {subscription_price} USDT.', extra_tags='subscription')
                else:
                    # Create payment history entry
                    payment = PaymentHistory.objects.create(
                        user=request.user,
                        payment_type='subscription',
                        currency='USDT',
                        amount=subscription_price,
                        payment_method='Balance',
                        transaction_id=f'SUB-{request.user.id}-{int(timezone.now().timestamp())}',
                        status='successful',
                        payment_note='Premium subscription purchase - Assigned 3000 tokens'
                    )
                    # Update subscription status, dates, and tokens
                    profile.subscription = 'premium'
                    profile.subscription_start_date = timezone.now()
                    profile.subscription_end_date = timezone.now() + timedelta(days=30)
                    profile.tokens = 3000  # Assign or refill 3000 tokens
                    profile.max_tokens = 3000
                    profile.save()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Successfully subscribed to Premium!',
                            'balance': str(profile.balance),
                            'subscription': 'Premium',
                            'tokens': profile.tokens,
                            'max_tokens': profile.max_tokens,
                            'subscription_end_date': profile.subscription_end_date.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%B %d, %Y')
                        })
                    messages.success(request, 'Successfully subscribed to Premium!', extra_tags='subscription')
        elif 'renew' in request.POST:
            if profile.subscription != 'premium':
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Only premium users can renew. Please subscribe first.'
                    })
                messages.error(request, 'Only premium users can renew. Please subscribe first.', extra_tags='subscription')
            elif profile.tokens >= profile.max_tokens:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Your tokens are already full. No need to renew now.'
                    })
                messages.error(request, 'Your tokens are already full. No need to renew now.', extra_tags='subscription')
            else:
                # Get subscription price
                subscription_price = subscription_settings.effective_price if subscription_settings else 5.00
                # Check balance
                if profile.balance < subscription_price:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Insufficient balance. You need {subscription_price} USDT.'
                        })
                    messages.error(request, f'Insufficient balance. You need {subscription_price} USDT.', extra_tags='subscription')
                else:
                    # Create payment history entry
                    payment = PaymentHistory.objects.create(
                        user=request.user,
                        payment_type='subscription',
                        currency='USDT',
                        amount=subscription_price,
                        payment_method='Balance',
                        transaction_id=f'RENEW-{request.user.id}-{int(timezone.now().timestamp())}',
                        status='successful',
                        payment_note='Premium subscription renewal - Reset to 3000 tokens'
                    )
                    # Update subscription dates and reset tokens
                    profile.subscription_start_date = timezone.now()
                    profile.subscription_end_date = timezone.now() + timedelta(days=30)
                    profile.tokens = 3000  # Reset to 3000 tokens
                    profile.max_tokens = 3000
                    profile.save()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Successfully renewed Premium subscription!',
                            'balance': str(profile.balance),
                            'subscription': 'Premium',
                            'tokens': profile.tokens,
                            'max_tokens': profile.max_tokens,
                            'subscription_end_date': profile.subscription_end_date.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%B %d, %Y')
                        })
                    messages.success(request, 'Successfully renewed Premium subscription!', extra_tags='subscription')

    # Get current time in UTC+6
    utc6_tz = pytz.timezone('Asia/Dhaka')  # UTC+6
    current_time = timezone.now().astimezone(utc6_tz)

    # Fetch user's predictions
    predictions = Prediction.objects.filter(user=request.user)

    # Calculate total predictions
    total_predictions_all_users = Prediction.objects.count()
    total_predictions_user = predictions.count()

    # Calculate user ranking based on total predictions
    user_prediction_counts = Prediction.objects.values('user').annotate(
        total=Count('user')
    ).order_by('-total')

    user_ranking = 1
    user_found = False
    for index, user_count in enumerate(user_prediction_counts, start=1):
        if user_count['user'] == request.user.id:
            user_ranking = index
            user_found = True
            break

    if not user_found:
        user_ranking = user_prediction_counts.count() + 1 if total_predictions_user == 0 else 1

    # Calculate percentage for progress bars
    max_predictions = user_prediction_counts[0]['total'] if user_prediction_counts else total_predictions_user
    prediction_percentage = (total_predictions_user / max_predictions * 100) if max_predictions > 0 else 0

    total_users = user_prediction_counts.count()
    ranking_percentage = ((total_users - user_ranking + 1) / total_users * 100) if total_users > 0 else 0

    # Prepare prediction data with status
    prediction_data = []
    for prediction in predictions:
        # Use created_at for impact_datetime
        impact_datetime = prediction.created_at.astimezone(utc6_tz)

        # Calculate expiration time (5-minute timeframe)
        timeframe_delta = timedelta(minutes=5)  # Fixed to 5m as per trading_logic.py
        expiration_time = impact_datetime + timeframe_delta

        # Determine status
        status = 'Active' if current_time < expiration_time else 'Expired'

        prediction_data.append({
            'signal_id': str(prediction.signal_id),
            'date': prediction.impact_time,  # Use impact_time for date column
            'asset': prediction.asset,
            'timeframe': prediction.timeframe,  # Fixed to 5m
            'direction': prediction.direction,
            'impact_time': prediction.created_at.astimezone(utc6_tz),
            'status': status
        })

    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
        'form': form,
        'change_password_form': change_password_form,
        'deposit_form': deposit_form,
        'predictions': prediction_data,
        'total_predictions_all_users': total_predictions_all_users,
        'total_predictions_user': total_predictions_user,
        'user_ranking': user_ranking,
        'prediction_percentage': round(prediction_percentage, 1),
        'ranking_percentage': round(ranking_percentage, 1),
        'balance': profile.balance,
        'tokens': profile.tokens,
        'max_tokens': profile.max_tokens,
        'effective_price': effective_price,
        'regular_price': regular_price,
        'is_discounted': is_discounted
    })
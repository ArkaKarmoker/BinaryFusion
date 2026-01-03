from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .trading_logic import predict
from django.views.decorators.csrf import csrf_exempt
from yahooquery import search
import json
import logging
from .models import Prediction
from django.utils import timezone

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
@login_required(login_url='login')
def app(request):
    # if not request.user.is_authenticated:
    #     return redirect('login')
    
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        if symbol:
            try:
                result = predict(symbol)
                logger.info(f"Prediction successful for symbol: {symbol}")
                
                # Check for errors in the result
                if result.get('error'):
                    logger.error(f"Prediction error for {symbol}: {result['error']}")
                    return JsonResponse({'error': result['error']})
                
                # Save prediction to database
                prediction = Prediction(
                    user=request.user,
                    asset=result.get('symbol', symbol),
                    timeframe='5m',  # Hardcoded as trading_logic.py uses 5-minute timeframe
                    direction=result.get('direction', 'UNKNOWN'),
                    impact_time=timezone.now().date()  # Use current date
                )
                prediction.save()
                logger.info(f"Prediction saved for {symbol}, ID: {prediction.id}")
                
                result['current_tokens'] = request.user.profile.tokens
                
                # --- ADDED: Pass the prediction ID to the frontend for feedback ---
                result['prediction_id'] = prediction.id
                # ------------------------------------------------------------------
                
                return JsonResponse(result)
            except Exception as e:
                logger.error(f"Prediction error: {str(e)}")
                return JsonResponse({'error': str(e)})
        else:
            return JsonResponse({'error': 'No symbol provided'})
    return render(request, 'predictor/app.html', {'initial_tokens': request.user.profile.tokens, 'max_tokens': request.user.profile.max_tokens})

@csrf_exempt
@login_required(login_url='login')
def symbol_suggestions(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if query:
            try:
                suggestions = search(query)
                symbols = [item['symbol'] for item in suggestions.get('quotes', [])][:10]
                logger.info(f"Suggestions for '{query}': {symbols}")
                return JsonResponse({'suggestions': symbols})
            except Exception as e:
                logger.error(f"Error fetching suggestions: {str(e)}")
                return JsonResponse({'error': str(e)})
        return JsonResponse({'suggestions': []})
    return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
@login_required(login_url='login')
def submit_feedback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prediction_id = data.get('prediction_id')
            vote = data.get('vote')  # Expected 'LIKE' or 'DISLIKE'

            if not prediction_id or not vote:
                return JsonResponse({'error': 'Missing data'}, status=400)

            # Get the prediction and ensure it belongs to the logged-in user
            prediction = Prediction.objects.get(id=prediction_id, user=request.user)
            
            # Update feedback
            prediction.feedback = vote
            prediction.save()
            
            logger.info(f"Feedback '{vote}' received for prediction {prediction_id}")
            return JsonResponse({'status': 'success', 'vote': vote})
            
        except Prediction.DoesNotExist:
            logger.warning(f"Prediction not found or unauthorized access attempt. ID: {prediction_id}")
            return JsonResponse({'error': 'Prediction not found'}, status=404)
        except Exception as e:
            logger.error(f"Feedback error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
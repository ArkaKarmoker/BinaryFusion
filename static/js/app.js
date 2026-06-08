// =============================================================================
// BinaryFusion App (Predictor) JavaScript
// =============================================================================
// Django template variables are injected via window.APP_CONFIG in the
// template before this script loads. Access them like:
//   window.APP_CONFIG.calendarDataUrl
// =============================================================================

// Global variable to store the latest prediction data for sharing
let latestPrediction = null;

// Initialize Notyf (Same as dashboard.html)
const notyf = new Notyf({
    duration: 5000,
    position: { x: 'right', y: 'top' },
    dismissible: true,
    types: [
        {
            type: 'success',
            background: '#28a745',
            icon: { className: 'fa fa-check-circle', tagName: 'i', color: 'white' }
        },
        {
            type: 'error',
            background: '#dc3545',
            icon: { className: 'fa fa-times-circle', tagName: 'i', color: 'white' }
        },
        {
            type: 'warning',
            background: '#17a2b8',
            icon: { className: 'fa fa-info-circle', tagName: 'i', color: 'white' }
        },
        {
            type: 'info',
            background: '#ffc107',
            icon: { className: 'fas fa-exclamation-triangle', tagName: 'i', color: 'white' }
        }
    ]
});

// Theme Toggle Functionality
function toggleTheme() {
    const body = document.getElementById('body');
    const lightIcon = document.querySelector('.light-icon');
    const darkIcon = document.querySelector('.dark-icon');
    
    if (!body.classList.contains('dark-mode')) {
        body.classList.add('dark-mode');
        lightIcon.classList.add('hidden');
        darkIcon.classList.remove('hidden');
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.remove('dark-mode');
        lightIcon.classList.remove('hidden');
        darkIcon.classList.add('hidden');
        localStorage.setItem('theme', 'light');
    }
}

// Initialize Calendar Table
function initCalendarTable() {
    if ($('#calendarTable').length) {
        const calendarDataUrl = window.APP_CONFIG.calendarDataUrl;
        const table = $('#calendarTable').DataTable({
            ajax: {
                url: calendarDataUrl,
                dataSrc: function(json) {
                    if (!json.events) return [];
                    const now = new Date();
                    // Filter logic: Keep only future or current events
                    return json.events.filter(function(event) {
                        if (!event.utc_datetime) return false;
                        // Convert string "YYYY-MM-DD HH:MM:SS" to UTC Date Object
                        const eventDate = new Date(event.utc_datetime.replace(' ', 'T') + 'Z');
                        // Return true if event date is greater than or equal to now (current user system time)
                        return eventDate >= now;
                    });
                }
            },
            columns: [
                { 
                    data: 'utc_datetime',
                    render: function(data, type, row) {
                        if (!data) return '-';
                        // Create Date object from UTC string (assuming format "YYYY-MM-DD HH:MM:SS")
                        // Replacing space with T and appending Z forces JS to treat it as UTC
                        const dateObj = new Date(data.replace(' ', 'T') + 'Z');
                        
                        // Return formatted string for display
                        if (type === 'display' || type === 'filter') {
                            return dateObj.toLocaleDateString('en-GB', {
                                weekday: 'long', 
                                day: 'numeric', 
                                month: 'long'
                            }); // e.g., "Sunday, 18 January"
                        }
                        // Return original UTC string for sorting/ordering to keep chronological order
                        return data;
                    }
                },
                { 
                    data: 'utc_datetime',
                    render: function(data, type, row) {
                        if (!data) return '-';
                        const dateObj = new Date(data.replace(' ', 'T') + 'Z');
                        
                        if (type === 'display' || type === 'filter') {
                            return dateObj.toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit',
                                hour12: true
                            }); // e.g., "02:30 PM"
                        }
                        return data;
                    }
                },
                { data: 'currency' },
                { data: 'title' },
                { 
                    data: 'impact',
                    render: function(data) {
                        let badgeClass = 'badge-secondary';
                        if(data.includes('High')) { badgeClass = 'badge-destructive'; }
                        if(data.includes('Medium')) { badgeClass = 'badge-warning'; }
                        if(data.includes('Low')) { badgeClass = 'badge-success'; }
                        
                        return `<span class="badge ${badgeClass}">${data}</span>`;
                    }
                },
                { data: 'previous' },
                { data: 'actual' },
                { data: 'forecast' }
            ],
            order: [[0, 'asc'], [1, 'asc']],
            pageLength: 5,
            lengthMenu: [5, 10, 25],
            responsive: false, // Changed from true to false
            autoWidth: false, // Added to prevent fixed width issues
            language: {
                emptyTable: "No upcoming events found."
            }
        });
    }
}

// Load saved theme preference
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    const body = document.getElementById('body');
    const lightIcon = document.querySelector('.light-icon');
    const darkIcon = document.querySelector('.dark-icon');

    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        lightIcon.classList.add('hidden');
        darkIcon.classList.remove('hidden');
    }

    // Initialize trading animation
    initTradingAnimation();

    // Initialize Calendar
    initCalendarTable();
});

// Trading Background Animation
function initTradingAnimation() {
    const canvas = document.getElementById('tradingCanvas');
    const ctx = canvas.getContext('2d');

    // --- Updated Size Handling ---
    // Set internal resolution matches window size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const candles = [];
    const candleCount = Math.floor(window.innerWidth / 20); // Space candles 20px apart
    const maxHeight = window.innerHeight * 0.3; // Max candle height
    const minHeight = 20; // Min candle height

    // Initialize candles
    for (let i = 0; i < candleCount; i++) {
        candles.push({
            x: i * 20,
            height: minHeight + Math.random() * (maxHeight - minHeight),
            direction: Math.random() > 0.5 ? 1 : -1,
            speed: 0.5 + Math.random() * 0.5,
            wickHeight: 10 + Math.random() * 20
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        candles.forEach(candle => {
            // Update candle height
            candle.height += candle.direction * candle.speed;
            if (candle.height > maxHeight || candle.height < minHeight) {
                candle.direction *= -1; // Reverse direction
            }

            // Draw candle body
            ctx.fillStyle = document.body.classList.contains('dark-mode') ? 'rgba(250, 250, 250, 0.3)' : 'rgba(9, 9, 11, 0.3)';
            ctx.fillRect(candle.x, canvas.height - candle.height, 8, candle.height);

            // Draw wick
            ctx.fillStyle = document.body.classList.contains('dark-mode') ? 'rgba(250, 250, 250, 0.6)' : 'rgba(9, 9, 11, 0.6)';
            ctx.fillRect(candle.x + 3, canvas.height - candle.height - candle.wickHeight, 2, candle.wickHeight);
            ctx.fillRect(candle.x + 3, canvas.height, 2, candle.wickHeight);
        });

        requestAnimationFrame(animate);
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });

    animate();
}

// Modal Functionality
function openModal(src) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('enlargedImage');
    modal.style.display = 'flex';
    modalImg.src = src;
}

function closeModal() {
    const modal = document.getElementById('imageModal');
    modal.style.display = 'none';
}

// AJAX Prediction Submission with Countdown
function submitPrediction(event) {
    event.preventDefault();

    const form = document.getElementById('predict-form');
    const symbol = document.getElementById('symbol').value;
    const spinner = document.getElementById('loading-spinner');
    const countdownTimer = document.getElementById('countdown-timer');
    const resultsWrapper = document.getElementById('results-wrapper');
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    // Grab elements to hide/show
    const feedbackContainer = document.getElementById('feedback-container');
    const btnTelegram = document.getElementById('btn-telegram');
    const btnCopy = document.getElementById('btn-copy');
    const btnShare = document.getElementById('btn-share');

    // Show spinner, countdown, and disable button
    spinner.style.display = 'inline-block';
    countdownTimer.style.display = 'inline-block';
    form.querySelector('button').disabled = true;
    resultsWrapper.classList.add('hidden'); // Hide previous results

    // --- ADDED: RESET FEEDBACK BUTTON STYLES ON NEW SEARCH ---
    const likeBtn = document.querySelector('.feedback-btn.like');
    const dislikeBtn = document.querySelector('.feedback-btn.dislike');
    // Remove the new specific active classes
    likeBtn.classList.remove('active-like');
    dislikeBtn.classList.remove('active-dislike');
    // ---------------------------------------------------------

    // Start countdown from 5 seconds
    let timeLeft = 5;
    countdownTimer.textContent = `${timeLeft}s`;
    const countdownInterval = setInterval(() => {
        timeLeft--;
        if (timeLeft >= 0) {
            countdownTimer.textContent = `${timeLeft}s`;
        } else {
            clearInterval(countdownInterval);
            countdownTimer.style.display = 'none';
        }
    }, 1000);

    // Fetch prediction
    fetch('/app/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `symbol=${encodeURIComponent(symbol)}&csrfmiddlewaretoken=${encodeURIComponent(csrfToken)}`
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json(); // Expect JSON response from server
    })
    .then(data => {
        // Stop countdown and hide spinner/countdown
        clearInterval(countdownInterval);
        spinner.style.display = 'none';
        countdownTimer.style.display = 'none';
        form.querySelector('button').disabled = false;

        // Save data for Telegram sharing
        latestPrediction = data;

        // Logic to hide buttons if error exists in response
        if (data.error) {
            feedbackContainer.style.display = 'none';
            btnTelegram.style.display = 'none';
            btnCopy.style.display = 'none';
            btnShare.style.display = 'none';
        } else {
            // Reset display if success (remove inline style to revert to CSS classes)
            feedbackContainer.style.display = '';
            btnTelegram.style.display = '';
            btnCopy.style.display = '';
            btnShare.style.display = '';
        }

        // Update results section
        const resultsSection = document.getElementById('results-section');
        resultsSection.innerHTML = renderResults(data);
        resultsWrapper.classList.remove('hidden'); // Show results and buttons

        // Update token count in real-time
        if (data.current_tokens !== undefined) {
            document.getElementById('token-count').textContent = data.current_tokens;
        }

        // Add click event to the candlestick chart image
        const chartImage = document.querySelector('.graph-container img');
        if (chartImage) {
            chartImage.addEventListener('click', () => openModal(chartImage.src));
        }
    })
    .catch(error => {
        // Handle errors
        clearInterval(countdownInterval);
        spinner.style.display = 'none';
        countdownTimer.style.display = 'none';
        form.querySelector('button').disabled = false;
        latestPrediction = null; // Reset data on error
        
        // Logic to hide buttons on catch error
        feedbackContainer.style.display = 'none';
        btnTelegram.style.display = 'none';
        btnCopy.style.display = 'none';
        btnShare.style.display = 'none';

        const resultsSection = document.getElementById('results-section');
        resultsSection.innerHTML = `
            <div class="card p-6 error-message w-full">
                <h3 class="text-sm font-semibold mb-2">Error</h3>
                <p class="text-sm">Failed to fetch prediction: ${error.message}</p>
            </div>`;
        resultsWrapper.classList.remove('hidden'); // Show error and buttons
    });
}

// --- ADDED: FEEDBACK LOGIC FUNCTION ---
function sendFeedback(voteType) {
    // Check if we have a valid prediction ID from the global variable
    if (!latestPrediction || !latestPrediction.prediction_id) {
        notyf.error('No active prediction to vote on.');
        return;
    }

    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const likeBtn = document.querySelector('.feedback-btn.like');
    const dislikeBtn = document.querySelector('.feedback-btn.dislike');
    
    // Variable to hold the final vote to send (LIKE, DISLIKE, or CLEAR)
    let finalVote = voteType;

    // Visual Feedback (Immediate UI update) with Toggle Logic
    if (voteType === 'LIKE') {
        if (likeBtn.classList.contains('active-like')) {
            // If already selected, UNSELECT it (Toggle OFF)
            likeBtn.classList.remove('active-like');
            finalVote = 'CLEAR'; // Send a different signal to database to clear vote
        } else {
            // Select LIKE, deselect DISLIKE
            likeBtn.classList.add('active-like');
            dislikeBtn.classList.remove('active-dislike');
        }
    } else if (voteType === 'DISLIKE') {
        if (dislikeBtn.classList.contains('active-dislike')) {
            // If already selected, UNSELECT it (Toggle OFF)
            dislikeBtn.classList.remove('active-dislike');
            finalVote = 'CLEAR'; // Send a different signal to database to clear vote
        } else {
            // Select DISLIKE, deselect LIKE
            dislikeBtn.classList.add('active-dislike');
            likeBtn.classList.remove('active-like');
        }
    }

    // Send AJAX request
    fetch('/submit-feedback/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            prediction_id: latestPrediction.prediction_id,
            vote: finalVote // Sends 'LIKE', 'DISLIKE' or 'CLEAR'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Feedback saved:', data.vote);
            if (data.vote === 'LIKE') {
                notyf.success('Prediction Liked! 👍');
            } else if (data.vote === 'DISLIKE') {
                notyf.success('Prediction Disliked! 👎');
            } else {
                notyf.open({ 
                    type: 'info', 
                    message: 'Feedback Cleared.' 
                });
            }
        } else {
            console.error('Error saving feedback:', data.error);
            notyf.error('Error saving feedback.');
        }
    })
    .catch(error => {
        console.error('Network error:', error);
        notyf.error('Connection error.');
    });
}
// --------------------------------------

// Function to render results dynamically
function renderResults(result) {
    if (result.error) {
        return `
            <div class="card p-6 error-message w-full">
                <h3 class="text-sm font-semibold mb-2">Error</h3>
                <p class="text-sm">${result.error}</p>
            </div>`;
    }

    // Determine the signal direction and filter indicators
    let signalType = result.direction.includes("UP") ? "Bullish" : result.direction.includes("DOWN") ? "Bearish" : null;
    let indicatorContent = '';

    if (signalType && result.indicator_signals && result.indicator_values) {
        // Filter indicators that match the signal direction
        const contributingIndicators = Object.keys(result.indicator_signals).filter(indicator => 
            result.indicator_signals[indicator].includes(signalType)
        );

        // Generate content for contributing indicators only
        indicatorContent = '<ul class="list-disc pl-5 space-y-2.5 text-sm" style="color: var(--muted-foreground);">';
        contributingIndicators.forEach(indicator => {
            if (indicator === 'RSI') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">RSI:</span> ${result.indicator_values.RSI.toFixed(2)} (${result.indicator_signals.RSI})</li>`;
            } else if (indicator === 'MACD') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">MACD:</span> ${result.indicator_values.MACD.toFixed(4)} vs Signal: ${result.indicator_values.MACD_Signal.toFixed(4)} (${result.indicator_signals.MACD})</li>`;
            } else if (indicator === 'Bollinger Bands') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">Bollinger Bands:</span> Upper: ${result.indicator_values.BB_Upper.toFixed(4)}, Middle: ${result.indicator_values.BB_Middle.toFixed(4)}, Lower: ${result.indicator_values.BB_Lower.toFixed(4)} (${result.indicator_signals['Bollinger Bands']})</li>`;
            } else if (indicator === 'ADX') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">ADX:</span> ${result.indicator_values.ADX.toFixed(2)}, +DI: ${result.indicator_values.Plus_DI.toFixed(2)}, -DI: ${result.indicator_values.Minus_DI.toFixed(2)} (${result.indicator_signals.ADX})</li>`;
            } else if (indicator === 'Stochastic') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">Stochastic:</span> %K: ${result.indicator_values.Stochastic_K.toFixed(2)}, %D: ${result.indicator_values.Stochastic_D.toFixed(2)} (${result.indicator_signals.Stochastic})</li>`;
            } else if (indicator === 'EMA') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">EMA:</span> Fast: ${result.indicator_values.EMA_Fast.toFixed(4)}, Slow: ${result.indicator_values.EMA_Slow.toFixed(4)} (${result.indicator_signals.EMA})</li>`;
            } else if (indicator === 'ATR') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">ATR:</span> ${result.indicator_values.ATR.toFixed(4)} (${result.indicator_signals.ATR})</li>`;
            } else if (indicator === 'Ichimoku Cloud') {
                indicatorContent += `<li><span class="font-medium" style="color: var(--foreground);">Ichimoku Cloud:</span> Tenkan: ${result.indicator_values.Ichimoku_Tenkan.toFixed(4)}, Kijun: ${result.indicator_values.Ichimoku_Kijun.toFixed(4)}, Senkou A: ${result.indicator_values.Ichimoku_Senkou_A.toFixed(4)}, Senkou B: ${result.indicator_values.Ichimoku_Senkou_B.toFixed(4)}, Chikou: ${result.indicator_values.Ichimoku_Chikou ? result.indicator_values.Ichimoku_Chikou.toFixed(4) : 'N/A'} (${result.indicator_signals['Ichimoku Cloud']})</li>`;
            }
        });
        indicatorContent += '</ul>';

        // If no indicators contributed to the signal, show a message
        if (contributingIndicators.length === 0) {
            indicatorContent = '<p class="text-sm" style="color: var(--muted-foreground);">No indicators contributed to the signal.</p>';
        }
    } else {
        indicatorContent = '<p class="text-sm" style="color: var(--muted-foreground);">No clear signal direction available.</p>';
    }

    return `
        <div class="card p-6">
            <h2 class="text-base section-title mb-6"><i class="fa fa-bolt text-sm"></i> Generated Signal</h2>
            <div class="space-y-3.5 text-sm" style="color: var(--muted-foreground);">
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-coins w-4 text-yellow-500"></i> Asset:</span> ${result.symbol}</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-rocket w-4"></i> Signal:</span> <span class="font-bold text-primary">${result.direction}</span></p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-bullseye w-4"></i> Accuracy:</span> ${result.accuracy}%</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-map-pin w-4 text-blue-500"></i> Entry Price:</span> ${result.entry_price ? result.entry_price.toFixed(5) : 'N/A'}</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-stop-circle w-4 text-red-500"></i> Stop Loss:</span> ${result.stop_loss ? result.stop_loss.toFixed(5) : 'N/A'}</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-check-circle w-4 text-green-500"></i> Take Profit:</span> ${result.take_profit ? result.take_profit.toFixed(5) : 'N/A'}</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-clock w-4"></i> Timeframe:</span> M5</p>
                <p><span class="font-medium" style="color: var(--foreground);"><i class="fa fa-hourglass-half w-4"></i> Impact Time:</span> ${result.impact_time}</p>
                
                <div style="border-top: 1px solid var(--border); padding-top: 0.875rem; margin-top: 0.875rem;">
                    <p class="text-xs italic"><i class="fa fa-exclamation-triangle text-yellow-500 mr-1"></i> Use 1 Step Martingale if loss. 
                        <span class="tooltip ml-1 text-primary"><i class="fa fa-info-circle"></i><span class="tooltiptext">1-Step Martingale: Double your position size after a loss to recover the loss with the next trade, then revert to the original size. Use cautiously due to high risk.</span></span>
                    </p>
                </div>
            </div>
        </div>
        <div class="card p-6">
            <h3 class="text-base section-title mb-6"><i class="fa fa-chart-line text-sm"></i> Candlestick Chart (M5)</h3>
            <div class="graph-container">
                <img src="data:image/png;base64,${result.candlestick_plot}" alt="Candlestick Chart">
            </div>
        </div>
        <div class="card p-6">
            <h3 class="text-base section-title mb-6"><i class="fa fa-balance-scale text-sm"></i> Technical Indicators</h3>
            ${indicatorContent}
        </div>`;
}

// Send to Telegram Logic
function sendToTelegram() {
    if (!latestPrediction || latestPrediction.error) {
        notyf.error('No valid signal to share. Please generate a prediction first.');
        return;
    }

    // Construct the message
    const message = `📊 *BinaryFusion Signal* 📊\n\n` +
                    `💰 Asset: ${latestPrediction.symbol}\n` +
                    `🚀 Signal: ${latestPrediction.direction}\n` +
                    `🎯 Accuracy: ${latestPrediction.accuracy}%\n` +
                    `📍 Entry Price: ${latestPrediction.entry_price ? latestPrediction.entry_price.toFixed(5) : 'N/A'}\n` +
                    `🛑 Stop Loss: ${latestPrediction.stop_loss ? latestPrediction.stop_loss.toFixed(5) : 'N/A'}\n` +
                    `✅ Take Profit: ${latestPrediction.take_profit ? latestPrediction.take_profit.toFixed(5) : 'N/A'}\n` +
                    `⏳ Timeframe: M5\n` +
                    `⏰ Impact Time: ${latestPrediction.impact_time}\n\n` +
                    `⚠️ Note: Use 1 Step Martingale if loss.`;

    // Encode the message for URL
    const encodedMessage = encodeURIComponent(message);
    // URL to share text via Telegram app (opens chat picker)
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodedMessage}`;

    // Open in new tab/window (triggers app on mobile)
    window.open(telegramUrl, '_blank');
}

// Copy Signal Logic
function copySignal() {
    if (!latestPrediction || latestPrediction.error) {
        notyf.error('No valid signal to copy. Please generate a prediction first.');
        return;
    }

    // Construct the message (same format as Telegram)
    const message = `📊 *BinaryFusion Signal* 📊\n\n` +
                    `💰 Asset: ${latestPrediction.symbol}\n` +
                    `🚀 Signal: ${latestPrediction.direction}\n` +
                    `🎯 Accuracy: ${latestPrediction.accuracy}%\n` +
                    `📍 Entry Price: ${latestPrediction.entry_price ? latestPrediction.entry_price.toFixed(5) : 'N/A'}\n` +
                    `🛑 Stop Loss: ${latestPrediction.stop_loss ? latestPrediction.stop_loss.toFixed(5) : 'N/A'}\n` +
                    `✅ Take Profit: ${latestPrediction.take_profit ? latestPrediction.take_profit.toFixed(5) : 'N/A'}\n` +
                    `⏳ Timeframe: M5\n` +
                    `⏰ Impact Time: ${latestPrediction.impact_time}\n\n` +
                    `⚠️ Note: Use 1 Step Martingale if loss.`;

    // Use Clipboard API
    navigator.clipboard.writeText(message).then(() => {
        notyf.success('Signal copied! 📋');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        notyf.error('Failed to copy text.');
    });
}

// Share Signal Logic (Web Share API)
function shareSignal() {
    if (!latestPrediction || latestPrediction.error) {
        notyf.error('No valid signal to share. Please generate a prediction first.');
        return;
    }

    // Construct the message
    const message = `📊 *BinaryFusion Signal* 📊\n\n` +
                    `💰 Asset: ${latestPrediction.symbol}\n` +
                    `🚀 Signal: ${latestPrediction.direction}\n` +
                    `🎯 Accuracy: ${latestPrediction.accuracy}%\n` +
                    `📍 Entry Price: ${latestPrediction.entry_price ? latestPrediction.entry_price.toFixed(5) : 'N/A'}\n` +
                    `🛑 Stop Loss: ${latestPrediction.stop_loss ? latestPrediction.stop_loss.toFixed(5) : 'N/A'}\n` +
                    `✅ Take Profit: ${latestPrediction.take_profit ? latestPrediction.take_profit.toFixed(5) : 'N/A'}\n` +
                    `⏳ Timeframe: M5\n` +
                    `⏰ Impact Time: ${latestPrediction.impact_time}\n\n` +
                    `⚠️ Note: Use 1 Step Martingale if loss.`;

    if (navigator.share) {
        navigator.share({
            title: 'BinaryFusion Signal',
            // combine text and URL into the text field to prevent duplication in Messenger
            text: message + "\n\n" + window.location.href,
            // url: window.location.href // Removed URL param to fix double-posting bug
        })
        .then(() => console.log('Successful share'))
        .catch((error) => console.log('Error sharing', error));
    } else {
        // Fallback for browsers that don't support Web Share API
        notyf.open({ 
            type: 'warning', 
            message: 'Web Share API not supported. Please use Copy.' 
        });
    }
}

// Close Results and Refresh Page
function closeResults() {
    document.getElementById('results-wrapper').classList.add('hidden');
    document.getElementById('symbol').value = ''; // Clear the input field
    latestPrediction = null; // Clear saved data
}

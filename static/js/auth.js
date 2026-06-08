// =============================================================================
// BinaryFusion Authentication JavaScript
// =============================================================================

// --- FIX FOR FORM RESUBMISSION ON RELOAD ---
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

// Message Dismissal Logic
function dismissMessage(element) {
    const container = element.parentElement;
    element.style.opacity = '0';
    setTimeout(() => {
        element.remove();
        if (container.children.length === 0) {
            container.remove();
        }
    }, 500);
}

// Toggle Password Visibility
// Can be called with (fieldId, btnElement) [registration/password reset] 
// or without arguments [login.html] -> handled by element id directly.
function togglePassword(fieldId, btnElement) {
    let passwordInput, eyeIcon;

    if (fieldId && btnElement) {
        passwordInput = document.getElementById(fieldId);
        eyeIcon = btnElement.querySelector('i');
    } else {
        // Fallback for login.html format
        passwordInput = document.getElementById('password');
        eyeIcon = document.getElementById('eyeIcon');
    }
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
    }
}

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

// Load saved theme preference and init
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

    // Auto-dismiss Global Messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    if (messages.length > 0) {
        setTimeout(() => {
            messages.forEach(msg => dismissMessage(msg));
        }, 5000);
    }
    
    // Auto-dismiss Field-Specific Errors (from password_reset_confirm) after 5 seconds
    const fieldErrors = document.querySelectorAll('.field-error-message');
    if (fieldErrors.length > 0) {
        setTimeout(() => {
            fieldErrors.forEach(err => {
                err.style.opacity = '0';
                setTimeout(() => err.remove(), 500);
            });
        }, 5000);
    }
});

// Trading Background Animation
function initTradingAnimation() {
    const canvas = document.getElementById('tradingCanvas');
    if (!canvas) return; // Prevent error if canvas missing

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const candles = [];
    const candleCount = Math.floor(window.innerWidth / 20);
    const maxHeight = window.innerHeight * 0.3;
    const minHeight = 20;

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
            candle.height += candle.direction * candle.speed;
            if (candle.height > maxHeight || candle.height < minHeight) {
                candle.direction *= -1;
            }

            ctx.fillStyle = document.body.classList.contains('dark-mode') ? 'rgba(250, 250, 250, 0.3)' : 'rgba(9, 9, 11, 0.3)';
            ctx.fillRect(candle.x, canvas.height - candle.height, 8, candle.height);

            ctx.fillStyle = document.body.classList.contains('dark-mode') ? 'rgba(250, 250, 250, 0.6)' : 'rgba(9, 9, 11, 0.6)';
            ctx.fillRect(candle.x + 3, canvas.height - candle.height - candle.wickHeight, 2, candle.wickHeight);
            ctx.fillRect(candle.x + 3, canvas.height, 2, candle.wickHeight);
        });

        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });

    animate();
}

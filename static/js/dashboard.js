// =============================================================================
// BinaryFusion Dashboard JavaScript
// =============================================================================
// Django template variables are injected via window.DASHBOARD_CONFIG in the
// template before this script loads. Access them like:
//   window.DASHBOARD_CONFIG.dashboardUrl
//   window.DASHBOARD_CONFIG.loginUrl
//   window.DASHBOARD_CONFIG.nowpaymentsDepositUrl
//   window.DASHBOARD_CONFIG.effectivePrice
//   window.DASHBOARD_CONFIG.tokens
//   window.DASHBOARD_CONFIG.maxTokens
//   window.DASHBOARD_CONFIG.messages
// =============================================================================

// Global Chart Reference
let weeklySignalChart = null;

// Initialize Notyf
const notyf = new Notyf({
    duration: 5000,
    position: {
        x: 'right',
        y: 'top',
    },
    dismissible: true,
    types: [
        {
            type: 'success',
            background: '#28a745', // Green
            icon: {
                className: 'fas fa-check-circle',
                tagName: 'i',
                color: 'white'
            }
        },
        {
            type: 'error',
            background: '#dc3545', // Red
            icon: {
                className: 'fas fa-times-circle',
                tagName: 'i',
                color: 'white'
            }
        },
        {
            type: 'warning',
            background: '#ffc107', // Orange/Yellow
            icon: {
                className: 'fas fa-exclamation-triangle',
                tagName: 'i',
                color: 'white'
            }
        }
    ]
});

// Display Django messages via Notyf on page load
document.addEventListener('DOMContentLoaded', function() {
    const messages = window.DASHBOARD_CONFIG.messages || [];
    messages.forEach(function(msg) {
        if (msg.tags === 'error') {
            notyf.error(msg.text);
        } else if (msg.tags === 'success') {
            notyf.success(msg.text);
        } else if (msg.tags === 'warning') {
            notyf.open({ type: 'warning', message: msg.text });
        } else {
            notyf.open({ type: 'info', message: msg.text, background: '#17a2b8', icon: false });
        }
    });
});

let initialSettings = {};
let cropper = null;
let croppedImageBlob = null;

// Theme Toggle Functionality (consistent with app.html)
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
    // Re-initialize TinyMCE to match theme if it exists
    initTinyMCE();

    // Update Chart.js Theme Colors
    if (weeklySignalChart) {
        const isDark = body.classList.contains('dark-mode');
        const textColor = isDark ? '#a1a1aa' : '#71717a';
        const gridColor = isDark ? '#27272a' : '#e4e4e7';
        
        weeklySignalChart.options.scales.x.ticks.color = textColor;
        weeklySignalChart.options.scales.y.ticks.color = textColor;
        weeklySignalChart.options.scales.y.grid.color = gridColor;
        
        // Update specific Zinc Colors on toggle
        weeklySignalChart.data.datasets[0].borderColor = isDark ? '#fafafa' : '#18181b';
        weeklySignalChart.data.datasets[0].backgroundColor = isDark ? 'rgba(250, 250, 250, 0.08)' : 'rgba(24, 24, 27, 0.08)';
        weeklySignalChart.data.datasets[0].pointBackgroundColor = isDark ? '#fafafa' : '#18181b';
        weeklySignalChart.data.datasets[0].pointBorderColor = isDark ? '#18181b' : '#ffffff';
        
        weeklySignalChart.update();
    }
}

// --- ADDED: TinyMCE Initialization Function ---
function initTinyMCE() {
    if (tinymce.get('support_description_editor')) {
        tinymce.remove('#support_description_editor');
    }
    
    const isDark = document.body.classList.contains('dark-mode');
    const bgColor = isDark ? '#09090b' : '#ffffff';
    const textColor = isDark ? '#fafafa' : '#09090b';

    tinymce.init({
        selector: '#support_description_editor',
        height: 250,
        menubar: false,
        plugins: 'lists link code',
        toolbar: 'undo redo | formatselect | bold italic | alignleft aligncenter alignright | bullist numlist | link',
        skin: isDark ? 'oxide-dark' : 'oxide',
        content_css: isDark ? 'dark' : 'default',
        content_style: `
            body { 
                background-color: ${bgColor} !important; 
                color: ${textColor} !important; 
                font-family: 'Inter', sans-serif; 
                font-size: 0.875rem; 
                margin: 1rem;
            }
        `,
        setup: function (editor) {
            editor.on('change', function () {
                editor.save(); // Auto sync with textarea
            });
        }
    });
}

// Copy USDT address to clipboard
function copyAddress() {
    const addressInput = document.getElementById('usdt-address');
    addressInput.select();
    document.execCommand('copy');
    notyf.success('Address copied to clipboard!');
}
// Submit Deposit with Transaction ID
function submitDeposit() {
    const transactionId = document.getElementById('transaction-id').value.trim();
    const paymentNote = document.getElementById('payment-note').value.trim();
    if (!transactionId) {
        notyf.error('Please enter a valid Transaction ID.');
        return;
    }
    notyf.success('Deposit request submitted successfully! Transaction ID: ' + transactionId + '. Your deposit will be processed after confirmation.');
    document.getElementById('transaction-id').value = ''; // Clear the input field
    document.getElementById('payment-note').value = ''; // Clear the payment note field
}

// --- SweetAlert2 Replacement for Subscription Modal ---
function openSubscriptionModal() {
    const isDark = document.body.classList.contains('dark-mode');
    const currentBalance = document.getElementById('profile-balance').textContent;
    const effectivePrice = window.DASHBOARD_CONFIG.effectivePrice;
    
    Swal.fire({
        title: 'Confirm Subscription Upgrade',
        html: `
            <div class="text-left">
                <p class="mb-4">Are you sure you want to upgrade to the Premium plan? <strong>${effectivePrice} USDT</strong> will be deducted from your balance.</p>
                <p class="mb-4">Current Balance: <strong>${currentBalance}</strong></p>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Subscribe',
        cancelButtonText: 'Cancel',
        confirmButtonColor: isDark ? '#fafafa' : '#09090b',
        cancelButtonColor: '#6b7280', // gray-500
        background: isDark ? '#18181b' : '#fff',
        color: isDark ? '#fafafa' : '#09090b',
        customClass: {
            title: isDark ? 'text-white' : 'text-gray-800',
            confirmButton: isDark ? 'text-black' : 'text-white'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            subscribe();
        }
    });
}

function subscribe() {
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const dashboardUrl = window.DASHBOARD_CONFIG.dashboardUrl;
    $.ajax({
        url: dashboardUrl,
        type: 'POST',
        data: { subscribe: 'subscribe', csrfmiddlewaretoken: csrftoken },
        success: function(response) {
            if (response.status === 'success') {
                notyf.success(response.message);
                // Update balance
                document.getElementById('usdt-balance').textContent = response.balance + ' USDT';
                document.getElementById('profile-balance').textContent = response.balance + ' USDT';
                // Update subscription status
                document.getElementById('subscription-status').textContent = response.subscription;
                // Update start date to current date
                let today = new Date();
                let month = today.toLocaleString('default', { month: 'long' });
                let day = today.getDate();
                let year = today.getFullYear();
                let startDate = `${month} ${day}, ${year}`;
                document.getElementById('subscription-start-date').textContent = startDate;
                // Update expiry date
                document.getElementById('subscription-expiry-date').textContent = response.subscription_end_date;
                // Update premium plan button to "Current Plan"
                document.querySelector('#premium-plan-button').outerHTML = '<button class="mt-6 w-full btn-outline" id="premium-plan-button">Current Plan</button>';
                // Update free plan button to "Previous Plan"
                document.querySelector('#free-plan-button').textContent = 'Previous Plan';
                // Update subscription status card button text and function
                const statusBtn = document.getElementById('status-card-button');
                if (statusBtn) {
                    statusBtn.textContent = 'Renew Subscription';
                    statusBtn.setAttribute('onclick', 'openRenewModal()');
                }
                // Update subscription status in user profile tab
                document.getElementById('subscription-status-user').textContent = response.subscription;
                document.getElementById('subscription-expiry-user').textContent = 'Expires on: ' + response.subscription_end_date;
                // Update tokens
                document.getElementById('remaining-tokens-value').textContent = response.tokens + ' / ' + response.max_tokens;
                const percentage = (response.tokens / response.max_tokens) * 100;
                document.getElementById('token-bar').style.width = `${percentage}%`;
                let color;
                if (response.tokens / response.max_tokens > 0.66) {
                    color = '#22c55e'; // green for high
                } else if (response.tokens / response.max_tokens > 0.33) {
                    color = '#eab308'; // yellow for medium
                } else {
                    color = '#ef4444'; // red for low
                }
                document.getElementById('token-bar').style.backgroundColor = color;
            } else {
                notyf.error(response.message);
            }
        },
        error: function() {
            notyf.error('An error occurred. Please try again.');
        }
    });
}

// --- SweetAlert2 Replacement for Renewal Modal ---
function openRenewModal() {
    const isDark = document.body.classList.contains('dark-mode');
    const currentBalance = document.getElementById('profile-balance').textContent;
    const effectivePrice = window.DASHBOARD_CONFIG.effectivePrice;

    Swal.fire({
        title: 'Confirm Premium Renewal',
        html: `
            <div class="text-left">
                <p class="mb-4">Are you sure you want to renew your Premium plan? <strong>${effectivePrice} USDT</strong> will be deducted from your balance. This will reset your tokens to 3000/3000 and extend your subscription by 30 days from now.</p>
                <p class="mb-4">Current Balance: <strong>${currentBalance}</strong></p>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Renew',
        cancelButtonText: 'Cancel',
        confirmButtonColor: isDark ? '#fafafa' : '#09090b',
        cancelButtonColor: '#6b7280', // gray-500
        background: isDark ? '#18181b' : '#fff',
        color: isDark ? '#fafafa' : '#09090b',
        customClass: {
            title: isDark ? 'text-white' : 'text-gray-800',
            confirmButton: isDark ? 'text-black' : 'text-white'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            renew();
        }
    });
}

function renew() {
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const dashboardUrl = window.DASHBOARD_CONFIG.dashboardUrl;
    $.ajax({
        url: dashboardUrl,
        type: 'POST',
        data: { renew: 'renew', csrfmiddlewaretoken: csrftoken },
        success: function(response) {
            if (response.status === 'success') {
                notyf.success(response.message);
                // Update balance
                document.getElementById('usdt-balance').textContent = response.balance + ' USDT';
                document.getElementById('profile-balance').textContent = response.balance + ' USDT';
                // Update subscription status (though it remains 'Premium')
                document.getElementById('subscription-status').textContent = response.subscription;
                // Update start date to current date
                let today = new Date();
                let month = today.toLocaleString('default', { month: 'long' });
                let day = today.getDate();
                let year = today.getFullYear();
                let startDate = `${month} ${day}, ${year}`;
                document.getElementById('subscription-start-date').textContent = startDate;
                // Update expiry date
                document.getElementById('subscription-expiry-date').textContent = response.subscription_end_date;
                // Update subscription status in user profile tab
                document.getElementById('subscription-status-user').textContent = response.subscription;
                document.getElementById('subscription-expiry-user').textContent = 'Expires on: ' + response.subscription_end_date;
                // Update tokens
                document.getElementById('remaining-tokens-value').textContent = response.tokens + ' / ' + response.max_tokens;
                const percentage = (response.tokens / response.max_tokens) * 100;
                document.getElementById('token-bar').style.width = `${percentage}%`;
                let color;
                if (response.tokens / response.max_tokens > 0.66) {
                    color = '#22c55e'; // green for high
                } else if (response.tokens / response.max_tokens > 0.33) {
                    color = '#eab308'; // yellow for medium
                } else {
                    color = '#ef4444'; // red for low
                }
                document.getElementById('token-bar').style.backgroundColor = color;
            } else {
                notyf.error(response.message);
            }
        },
        error: function() {
            notyf.error('An error occurred. Please try again.');
        }
    });
}

// --- Photo Cropper Logic ---
function openCropperModal() {
    document.getElementById('cropperModal').style.display = 'flex';
}

function closeCropperModal() {
    document.getElementById('cropperModal').style.display = 'none';
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    $('#cropper-input').val(''); // Reset file input
}

$('#btn-upload-photo').on('click', function() {
    $('#cropper-input').click();
});

$('#cropper-input').on('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            $('#cropper-image').attr('src', event.target.result);
            openCropperModal();
            
            if (cropper) {
                cropper.destroy();
            }
            cropper = new Cropper(document.getElementById('cropper-image'), {
                aspectRatio: 1, // Enforce square cropping
                viewMode: 1,
                background: false
            });
        };
        reader.readAsDataURL(file);
    }
});

$('#btn-crop-confirm').on('click', function() {
    if (cropper) {
        cropper.getCroppedCanvas({
            width: 300,
            height: 300,
        }).toBlob(function(blob) {
            croppedImageBlob = blob;
            const url = URL.createObjectURL(blob);
            
            // Update preview in User Information
            $('#user-avatar-img').attr('src', url).removeClass('hidden');
            $('#user-avatar-initial').addClass('hidden');
            
            // Update buttons in Edit Profile
            $('#btn-upload-photo').html('<i class="fa fa-camera"></i> Update Photo');
            $('#btn-remove-photo').removeClass('hidden');
            $('#photo-update-warning').removeClass('hidden');
            
            // Uncheck clear image
            $('#id_clear_image').prop('checked', false);
            
            closeCropperModal();
        }, 'image/png');
    }
});

$('#btn-remove-photo').on('click', function() {
    croppedImageBlob = null;
    $('#id_clear_image').prop('checked', true);
    
    // Revert UI to initial avatar
    $('#user-avatar-img').addClass('hidden').attr('src', '');
    $('#user-avatar-initial').removeClass('hidden');
    
    // Update Buttons
    $('#btn-upload-photo').html('<i class="fa fa-plus"></i> Add Photo');
    $('#btn-remove-photo').addClass('hidden');
    $('#photo-update-warning').removeClass('hidden');
});

// Load saved theme preference and initialize credit progress
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
    
    // Initialize Chart.js for Weekly Signal Generation
    const ctxChart = document.getElementById('weeklySignalChart').getContext('2d');
    const isDark = document.body.classList.contains('dark-mode');
    const textColor = isDark ? '#a1a1aa' : '#71717a';
    const gridColor = isDark ? '#27272a' : '#e4e4e7';
    const chartPrimary = isDark ? '#fafafa' : '#18181b';
    const chartBg = isDark ? 'rgba(250, 250, 250, 0.08)' : 'rgba(24, 24, 27, 0.08)';

    weeklySignalChart = new Chart(ctxChart, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Signals Generated',
                data: [5, 12, 8, 15, 10, 22, 18], // Static dummy data
                borderColor: chartPrimary,
                backgroundColor: chartBg,
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: chartPrimary,
                pointBorderColor: isDark ? '#18181b' : '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: textColor, font: { size: 11 } },
                    grid: { color: gridColor, drawBorder: false }
                },
                x: {
                    ticks: { color: textColor, font: { size: 11 } },
                    grid: { display: false, drawBorder: false }
                }
            }
        }
    });

    // Initialize TinyMCE
    initTinyMCE();
    
    // Capture initial settings form values
    initialSettings = {
        timezone: $('#id_timezone').val(),
        theme_preference: $('#id_theme_preference').val(),
        auto_renew_subscription: $('#id_auto_renew_subscription').is(':checked'),
        auto_refill_tokens: $('#id_auto_refill_tokens').is(':checked'),
        email_notifications: $('#id_email_notifications').is(':checked'),
        push_notifications: $('#id_push_notifications').is(':checked')
    };
    // Initialize trading animation (consistent with app.html)
    initTradingAnimation();
     
    // Initialize DataTable for payment history with responsive settings
    const paymentTable = $('#paymentTable').DataTable({
        responsive: true,
        order: [[1, 'desc']], // Sort by Payment ID column in descending order
        columnDefs: [
            { className: 'dt-center', targets: '_all' }
        ]
    });
    
    // Initialize DataTable for Support History
    const supportTable = $('#supportTable').DataTable({
        responsive: true,
        order: [[0, 'desc']], // Sort by Date column descending
        columnDefs: [
            { className: 'dt-center', targets: '_all' }
        ]
    });

    // --- ADDED: Initialize DataTable for Offer History ---
    const offerTable = $('#offerTable').DataTable({
        responsive: true,
        order: [[0, 'desc']], // Sort by Date column descending
        columnDefs: [
            { className: 'dt-center', targets: '_all' }
        ]
    });
    
    // Handle profile form submission via AJAX with FormData Support
    $('#profile-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
 
        // Get current displayed values
        const currentFullName = $('#user-fullname').text().trim();
        const currentUsername = $('#user-username').text().trim();
        const currentEmail = $('#user-email').text().trim();
        const currentTelegram = $('#user-telegram').text().trim() === 'Not set' ? '' : $('#user-telegram').text().trim();
        const currentPhone = $('#user-phone').text().trim() === 'Not set' ? '' : $('#user-phone').text().trim();
 
        // Get form input values
        const formDataValues = form.serializeArray();
        let firstName = '';
        let lastName = '';
        let email = '';
        let username = '';
        let telegram = '';
        let phone = '';
        formDataValues.forEach(field => {
            if (field.name === 'first_name') firstName = field.value.trim();
            if (field.name === 'last_name') lastName = field.value.trim();
            if (field.name === 'email') email = field.value.trim();
            if (field.name === 'username') username = field.value.trim();
            if (field.name === 'telegram') telegram = field.value.trim();
            if (field.name === 'phone') phone = field.value.trim();
        });
 
        // Combine first and last name for comparison
        const formFullName = `${firstName} ${lastName}`.trim();
        const hasImageChanged = !$('#photo-update-warning').hasClass('hidden');
 
        // Check if any field has changed
        if (formFullName === currentFullName &&
            username === currentUsername &&
            email === currentEmail &&
            telegram === currentTelegram &&
            phone === currentPhone && 
            !hasImageChanged) {
            // No changes detected, show message and return
            notyf.open({ type: 'warning', message: 'No changes detected.' });
            return;
        }
        
        // Build FormData payload to support sending images
        const formData = new FormData(form[0]);
        formData.append('update_profile', 'Update Profile');
        
        if (croppedImageBlob) {
            formData.delete('image'); // Remove standard image input
            formData.append('image', croppedImageBlob, 'profile_photo.png');
        }

        // Proceed with AJAX request if changes detected
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: formData,
            processData: false, // Required for FormData
            contentType: false, // Required for FormData
            success: function(response) {
                if (response.status === 'success' || typeof response === 'object') {
                    notyf.success(response.message || 'Profile updated successfully.');
                    
                    // Reset image state
                    $('#photo-update-warning').addClass('hidden');
                    croppedImageBlob = null;
                    
                    // Update user information on the page
                    if(response.user) {
                        $('#user-fullname').text(`${response.user.first_name} ${response.user.last_name}`);
                        $('#user-email').text(response.user.email);
                        $('#user-username').text(response.user.username);
                        $('#welcome-username').text(`🎉 Welcome, ${response.user.username}`);
                        
                        // Sync Image Avatar with Backend URL Response
                        if(response.user.profile_image) {
                            $('#user-avatar-img').attr('src', response.user.profile_image).removeClass('hidden');
                            $('#user-avatar-initial').addClass('hidden');
                            $('#btn-upload-photo').html('<i class="fa fa-camera"></i> Update Photo');
                            $('#btn-remove-photo').removeClass('hidden');
                        } else {
                            $('#user-avatar-img').addClass('hidden').attr('src', '');
                            $('#user-avatar-initial').removeClass('hidden').text(response.user.initial);
                            $('#btn-upload-photo').html('<i class="fa fa-plus"></i> Add Photo');
                            $('#btn-remove-photo').addClass('hidden');
                        }
                    } else {
                        // Fallback mapping
                        $('#user-fullname').text(`${firstName} ${lastName}`);
                        $('#user-email').text(email);
                        $('#user-username').text(username);
                        $('#welcome-username').text(`🎉 Welcome, ${username}`);
                    }
                    $('#user-telegram').text(telegram || 'Not set');
                    $('#user-phone').text(phone || 'Not set');
                } else {
                     notyf.success('Profile updated successfully.');
                     $('#photo-update-warning').addClass('hidden');
                     croppedImageBlob = null;
                }
            },
            error: function(xhr) {
                notyf.error('An error occurred. Please try again.');
            }
        });
    });
    
    // Handle password form submission via AJAX
    $('#password-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
 
        // Include CSRF token in AJAX headers
        const csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
 
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize() + '&change_password=Save',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    notyf.success(response.message);
              
                    // Clear password fields
                    form.find('input[type="password"]').val('');
              
                    // Check if logout is required
                    if (response.logout) {
                        const loginUrl = window.DASHBOARD_CONFIG.loginUrl;
                        setTimeout(() => {
                            window.location.href = loginUrl;
                        }, 2000); // Redirect after 2 seconds to allow user to see the message
                    }
                } else {
                    // Display server-side errors
                    let errorMessageText = response.message || 'An error occurred. Please try again.';
                    if (response.errors) {
                        errorMessageText = Object.values(response.errors).flat().join('<br>');
                    }
                    notyf.error(errorMessageText);
                }
            },
            error: function(xhr) {
                notyf.error('An error occurred. Please try again.');
            }
        });
    });
    
    // Handle deposit form submission via AJAX
    $('#deposit-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        let paymentTable = $('#paymentTable').DataTable();
        // Get form input values
        const formData = form.serializeArray();
        let transactionId = '';
        let paymentNote = '';
        formData.forEach(field => {
            if (field.name === 'transaction_id') transactionId = field.value.trim();
            if (field.name === 'payment_note') paymentNote = field.value.trim();
        });
        // Validate transaction ID
        if (!transactionId) {
            notyf.error('Please enter a valid Transaction ID.');
            return;
        }
        // Include CSRF token in AJAX headers
        const csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
        // Proceed with AJAX request
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize() + '&deposit=Deposit',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    notyf.success(response.message);
                    
                    // Reload payment table data from server (Realtime fetch)
                    $.get(window.location.href, function(html) {
                        // Parse the new HTML
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        // Get new rows
                        var newRows = $(doc).find('#paymentTable tbody tr');
                        
                        // Get DataTable instance
                        var table = $('#paymentTable').DataTable();
                        
                        // Clear and add new rows
                        table.clear();
                        table.rows.add(newRows);
                        table.draw(); // Redraw table
                    });

                    // Clear form fields
                    form.find('input, textarea').val('');
                } else {
                    // Display server-side errors
                    let errorMessageText = response.message || 'An error occurred. Please try again.';
                    if (response.errors) {
                        errorMessageText = Object.values(response.errors).flat().join('<br>');
                    }
                    notyf.error(errorMessageText);
                }
            },
            error: function(xhr) {
                notyf.error('An error occurred. Please try again.');
            }
        });
    });
    
    // Handle settings form submission via AJAX
    $('#settings-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        // Get current form values
        const currentSettings = {
            timezone: $('#id_timezone').val(),
            theme_preference: $('#id_theme_preference').val(),
            auto_renew_subscription: $('#id_auto_renew_subscription').is(':checked'),
            auto_refill_tokens: $('#id_auto_refill_tokens').is(':checked'),
            email_notifications: $('#id_email_notifications').is(':checked'),
            push_notifications: $('#id_push_notifications').is(':checked')
        };
        // Check if any field has changed
        let hasChanges = false;
        for (let key in currentSettings) {
            if (currentSettings[key] !== initialSettings[key]) {
                hasChanges = true;
                break;
            }
        }
        if (!hasChanges) {
            notyf.open({ type: 'warning', message: 'No changes detected.' });
            return;
        }
        // Include CSRF token in AJAX headers
        const csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
        // Proceed with AJAX request
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize() + '&save_settings=Save+Settings',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    notyf.success(response.message);
                    // Update initialSettings to reflect saved changes
                    initialSettings = {...currentSettings};
                } else {
                    // Display server-side errors
                    let errorMessageText = response.message || 'An error occurred. Please try again.';
                    if (response.errors) {
                        errorMessageText = Object.values(response.errors).flat().join('<br>');
                    }
                    notyf.error(errorMessageText);
                }
            },
            error: function(xhr) {
                notyf.error('An error occurred. Please try again.');
            }
        });
    });
    
    // --- ADDED: Handle Support Ticket Form Submission via AJAX ---
    $('#support-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        
        // Sync TinyMCE data to textarea before serializing
        if (tinymce.get('support_description_editor')) {
            tinymce.get('support_description_editor').save();
        }
        
        const descValue = $('#support_description_editor').val().trim();
        if (!descValue) {
            notyf.error("Please provide a detailed description of your issue.");
            return;
        }

        const csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
        const btn = form.find('button[type="submit"]');
        const originalText = btn.html();
        
        // Set loading state
        btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Submitting...');

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: form.serialize() + '&submit_ticket=Submit',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    notyf.success(response.message);
                    
                    // Reload Support Table Data (Realtime fetch)
                    $.get(window.location.href, function(html) {
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        var newRows = $(doc).find('#supportTable tbody tr');
                        var table = $('#supportTable').DataTable();
                        table.clear();
                        table.rows.add(newRows);
                        table.draw(); 
                    });

                    // Clear form
                    form.find('select').prop('selectedIndex', 0);
                    if (tinymce.get('support_description_editor')) {
                        tinymce.get('support_description_editor').setContent('');
                    }
                } else {
                    let errorMessageText = response.message || 'An error occurred. Please try again.';
                    if (response.errors) {
                        errorMessageText = Object.values(response.errors).flat().join('<br>');
                    }
                    notyf.error(errorMessageText);
                }
                btn.prop('disabled', false).html(originalText);
            },
            error: function(xhr) {
                notyf.error('An error occurred while submitting your ticket. Please try again.');
                btn.prop('disabled', false).html(originalText);
            }
        });
    });
    
    // --- SweetAlert2 Replacement for Payment Details Modal ---
    $(document).on('click', '.view-details', function(e) {
        e.preventDefault();
        const data = this.dataset;
        const isDark = document.body.classList.contains('dark-mode');

        Swal.fire({
            title: 'Payment Details',
            html: `
                <div class="text-left space-y-2 text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}">
                    <p><strong>Payment ID:</strong> ${data.paymentId}</p>
                    <p><strong>User:</strong> ${data.user}</p>
                    <p><strong>Payment Type:</strong> ${data.paymentType}</p>
                    <p><strong>Currency:</strong> ${data.currency}</p>
                    <p><strong>Amount:</strong> ${data.amount}</p>
                    <p><strong>Payment Method:</strong> ${data.paymentMethod}</p>
                    <p><strong>Transaction ID:</strong> ${data.transactionId}</p>
                    <p><strong>Status:</strong> ${data.status}</p>
                    <p><strong>Payment Note:</strong> ${data.paymentNote}</p>
                    <p><strong>Remark:</strong> ${data.remark}</p>
                    <p><strong>Created At:</strong> ${data.createdAt}</p>
                    <p><strong>Last Updated:</strong> ${data.lastUpdated}</p>
                </div>
            `,
            background: isDark ? '#18181b' : '#fff',
            color: isDark ? '#fafafa' : '#09090b',
            confirmButtonColor: isDark ? '#fafafa' : '#09090b',
            confirmButtonText: 'Close',
            customClass: {
                title: isDark ? 'text-white' : 'text-gray-800',
                confirmButton: isDark ? 'text-black' : 'text-white'
            }
        });
    });

    // --- ADDED: SweetAlert2 Modal for Support Ticket Details ---
    $(document).on('click', '.view-ticket-details', function(e) {
        e.preventDefault();
        const data = this.dataset;
        const isDark = document.body.classList.contains('dark-mode');

        Swal.fire({
            title: 'Ticket Details',
            html: `
                <div class="text-left space-y-4 text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}">
                    <div class="grid grid-cols-2 gap-2 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'} pb-2">
                        <p><strong>Ticket No:</strong> <span class="font-mono">${data.ticket}</span></p>
                        <p><strong>Status:</strong> ${data.status}</p>
                        <p><strong>Issue Type:</strong> ${data.type}</p>
                        <p><strong>Date:</strong> ${data.date}</p>
                    </div>
                    <div>
                        <p class="font-bold mb-1">Description:</p>
                        <div class="p-3 rounded ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-gray-50 border-gray-200 text-gray-800'} border max-h-40 overflow-y-auto tinymce-content">
                            ${data.desc}
                        </div>
                    </div>
                    <div>
                        <p class="font-bold mb-1">Admin Response:</p>
                        <div class="p-3 rounded ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-gray-50 border-gray-200 text-gray-800'} border max-h-40 overflow-y-auto tinymce-content">
                            ${data.response}
                        </div>
                    </div>
                    <p class="text-xs text-right mt-2"><strong>Last Updated:</strong> ${data.updated}</p>
                </div>
            `,
            background: isDark ? '#18181b' : '#fff',
            color: isDark ? '#fafafa' : '#09090b',
            confirmButtonColor: isDark ? '#fafafa' : '#09090b',
            confirmButtonText: 'Close',
            customClass: {
                title: isDark ? 'text-white' : 'text-gray-800',
                popup: 'w-11/12 max-w-2xl', // Make modal wider for rich text
                confirmButton: isDark ? 'text-black' : 'text-white'
            }
        });
    });

    // --- NEW: SweetAlert2 Modal for Offer Details ---
    $(document).on('click', '.view-offer-details', function(e) {
        e.preventDefault();
        const data = this.dataset;
        const isDark = document.body.classList.contains('dark-mode');

        Swal.fire({
            title: 'Reward Request Details',
            html: `
                <div class="text-left space-y-4 text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}">
                    <div class="grid grid-cols-2 gap-2 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'} pb-2">
                        <p><strong>Reward ID:</strong> <span class="font-mono">${data.rewardId}</span></p>
                        <p><strong>Platform:</strong> ${data.platform}</p>
                        <p><strong>Platform UID:</strong> <span class="font-mono text-primary">${data.uid}</span></p>
                        <p><strong>Action Type:</strong> ${data.action}</p>
                        <p><strong>Date:</strong> ${data.date}</p>
                        <p><strong>Earned Credit:</strong> ${data.credit}</p>
                        <p><strong>Status:</strong> ${data.status}</p>
                    </div>
                    <div>
                        <p class="font-bold mb-1">Admin Remark:</p>
                        <div class="p-3 rounded ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-gray-50 border-gray-200 text-gray-800'} border">
                            ${data.remark}
                        </div>
                    </div>
                </div>
            `,
            background: isDark ? '#18181b' : '#fff',
            color: isDark ? '#fafafa' : '#09090b',
            confirmButtonColor: isDark ? '#fafafa' : '#09090b',
            confirmButtonText: 'Close',
            customClass: {
                title: isDark ? 'text-white' : 'text-gray-800',
                confirmButton: isDark ? 'text-black' : 'text-white'
            }
        });
    });

    // Restore active tab from localStorage
    const activeTab = sessionStorage.getItem('activeTab') || 'user-tab';
    const tabButton = document.querySelector(`.tab-button[onclick="openTab(event, '${activeTab}')"]`);
    if (tabButton) {
        tabButton.click();
    }
    // Restore default sub-tab for payment-tab if active
    if (activeTab === 'payment-tab') {
        const activeDepositTab = sessionStorage.getItem('activeDepositTab') || 'nowpayments-tab';
        const depositButton = document.querySelector(`#payment-tab .deposit-tab-button[onclick="openDepositTab(event, '${activeDepositTab}')"]`);
        if (depositButton) {
            depositButton.click();
        }
    }
    // Initialize token bar
    const remainingTokensElement = document.getElementById('remaining-tokens-value');
    if (remainingTokensElement) {
        const remainingTokens = window.DASHBOARD_CONFIG.tokens;
        const maxTokens = window.DASHBOARD_CONFIG.maxTokens;
        const percentage = (remainingTokens / maxTokens) * 100;
        const tokenBar = document.getElementById('token-bar');
        tokenBar.style.width = `${percentage}%`;
        let color;
        if (remainingTokens / maxTokens > 0.66) {
            color = '#22c55e'; // green for high
        } else if (remainingTokens / maxTokens > 0.33) {
            color = '#eab308'; // yellow for medium
        } else {
            color = '#ef4444'; // red for low
        }
        tokenBar.style.backgroundColor = color;
    }
});

// Handle NOWPayments Form Submission (New Feature)
$('#nowpayments-deposit-form').on('submit', function(e) {
    e.preventDefault();
    
    const form = $(this);
    const btn = form.find('button[type="submit"]');
    const originalText = btn.html();
    
    // 1. Basic Validation
    const amount = form.find('input[name="amount"]').val();
    if (!amount || amount < 5) {
        notyf.error('Minimum deposit is 5 USDT.');
        return;
    }

    // 2. UI Loading State
    btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Processing...');

    // 3. AJAX Request
    const nowpaymentsUrl = window.DASHBOARD_CONFIG.nowpaymentsDepositUrl;
    $.ajax({
        url: nowpaymentsUrl,
        type: 'POST',
        data: form.serialize(),
        success: function(response) {
            if (response.status === 'success') {
                // Show success message
                notyf.success('Redirecting to Payment Gateway...');
                
                // 4. Redirect User
                setTimeout(function() {
                    window.location.href = response.invoice_url;
                }, 1000);
            } else {
                // Show Error
                notyf.error(response.message);
                btn.prop('disabled', false).html(originalText);
            }
        },
        error: function(xhr) {
            let errorMsg = 'Connection error. Please try again.';
            if(xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }
            notyf.error(errorMsg);
            btn.prop('disabled', false).html(originalText);
        }
    });
});

// Check for payment callback params on load
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('tab') === 'payment-tab') {
    const status = urlParams.get('status');
    
    if (status === 'success') {
        notyf.success('Payment initiated! Please wait for network confirmation.');
    } else if (status === 'cancel') {
        notyf.error('Payment cancelled.');
    }
}

// Trading Background Animation (consistent with app.html)
function initTradingAnimation() {
    const canvas = document.getElementById('tradingCanvas');
    const ctx = canvas.getContext('2d');
    // Set canvas size initially
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const candles = [];
    const candleCount = Math.floor(window.innerWidth / 20);
    const maxHeight = window.innerHeight * 0.3;
    const minHeight = 20;
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
                candle.direction *= -1;
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
// Tab system functionality
function openTab(evt, tabName) {
    // Hide all tab content
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    // Show the current tab and add active class to the button
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
    // Save active tab to localStorage
    sessionStorage.setItem('activeTab', tabName);
    // Re-initialize DataTable for predictionTable when Signal History tab is opened
    if (tabName === 'signal-history-tab' && $('#predictionTable').length) {
        $('#predictionTable').DataTable().destroy();
        $('#predictionTable').DataTable({
            responsive: true,
            order: [[1, 'desc']],
            language: {
                emptyTable: "No predictions found."
            },
            columnDefs: [
                { className: 'dt-center', targets: '_all' }
            ]
        });
    }
}
// Deposit Tab system functionality (sub-tabs for deposit methods)
function openDepositTab(evt, tabName) {
    // Hide all deposit tab content
    const depositTabContents = document.querySelectorAll('#payment-tab .deposit-tab-content');
    for (let i = 0; i < depositTabContents.length; i++) {
        depositTabContents[i].classList.remove('active');
    }
    // Remove active class from all deposit tab buttons
    const depositTabButtons = document.querySelectorAll('#payment-tab .deposit-tab-button');
    for (let i = 0; i < depositTabButtons.length; i++) {
        depositTabButtons[i].classList.remove('active');
    }
    // Show the current deposit tab and add active class to the button
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
    sessionStorage.setItem('activeDepositTab', tabName);
}

// --- Updated Custom Modal Functionality from Code 1 ---
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

// Password Visibility Toggle
function togglePasswordVisibility(inputId, icon) {
    const input = document.getElementById(inputId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = "password";
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// --- NEW: Offer Tab Custom JS ---
function copyAffiliateLink(inputId) {
    const copyText = document.getElementById(inputId);
    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices
    document.execCommand("copy");
    notyf.success("Affiliate link copied to clipboard!");
}

function submitOfferReq(e, platform) {
    e.preventDefault();
    notyf.success(platform + " UID submitted successfully! Pending admin verification.");
    e.target.reset();
}

// --- NEW: Offer Carousel Logic ---
let currentOfferSlide = 0;
const totalOfferSlides = 3;
let offerCarouselInterval;

function updateCarouselUI() {
    const inner = document.getElementById('offer-carousel-inner');
    if(inner) {
        inner.style.transform = `translateX(-${currentOfferSlide * 100}%)`;
        
        // Update indicators
        const indicators = document.querySelectorAll('.carousel-indicator');
        indicators.forEach((ind, index) => {
            if (index === currentOfferSlide) {
                ind.classList.remove('opacity-50');
                ind.classList.add('opacity-100');
            } else {
                ind.classList.remove('opacity-100');
                ind.classList.add('opacity-50');
            }
        });
    }
}

function moveOfferCarousel(direction) {
    currentOfferSlide = (currentOfferSlide + direction + totalOfferSlides) % totalOfferSlides;
    updateCarouselUI();
    resetOfferCarouselInterval();
}

function setOfferCarousel(index) {
    currentOfferSlide = index;
    updateCarouselUI();
    resetOfferCarouselInterval();
}

function resetOfferCarouselInterval() {
    clearInterval(offerCarouselInterval);
    offerCarouselInterval = setInterval(() => {
        moveOfferCarousel(1);
    }, 5000);
}

// Initialize carousel interval
document.addEventListener('DOMContentLoaded', () => {
    offerCarouselInterval = setInterval(() => {
        moveOfferCarousel(1);
    }, 5000);
});

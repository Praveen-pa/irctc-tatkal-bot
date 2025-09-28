/**
 * IRCTC Tatkal Automation Bot - Main JavaScript
 */

// Global variables
let isFormSubmitting = false;
let passengerCount = 0;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

function initializeApplication() {
    console.log('🚀 Initializing IRCTC Tatkal Bot');
    
    // Initialize UI components
    initUI();
    
    // Load user preferences
    loadUserPreferences();
    
    // Setup global event listeners
    setupGlobalEventListeners();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    // Check browser compatibility
    checkBrowserCompatibility();
}

function initUI() {
    console.log('🎨 Initializing UI components');
    
    // Initialize date inputs
    initializeDateInputs();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize dynamic elements
    initializeDynamicElements();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
}

function initializeDateInputs() {
    const journeyDateInput = document.getElementById('journey-date');
    if (journeyDateInput) {
        // Set minimum date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        journeyDateInput.min = tomorrow.toISOString().split('T')[0];
        
        // Set default to tomorrow
        journeyDateInput.value = tomorrow.toISOString().split('T')[0];
        
        // Update Tatkal time when date/class changes
        journeyDateInput.addEventListener('change', updateTatkalTime);
    }
    
    const travelClassSelect = document.getElementById('travel-class');
    if (travelClassSelect) {
        travelClassSelect.addEventListener('change', updateTatkalTime);
    }
}

function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

function initializeDynamicElements() {
    // Add passenger button
    const addPassengerBtn = document.getElementById('add-passenger');
    if (addPassengerBtn) {
        addPassengerBtn.addEventListener('click', addPassenger);
    }
    
    // Password toggle button
    const togglePasswordBtn = document.getElementById('toggle-password');
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', togglePasswordVisibility);
    }
    
    // Station input autocomplete
    initializeStationAutocomplete();
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl+Enter to submit form
        if (event.ctrlKey && event.key === 'Enter') {
            const activeForm = document.querySelector('form:focus-within');
            if (activeForm) {
                activeForm.requestSubmit();
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                bootstrap.Modal.getInstance(openModal).hide();
            }
        }
    });
}

function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function addPassenger() {
    const container = document.getElementById('passengers-container');
    const template = document.getElementById('passenger-template');
    
    if (!container || !template) {
        console.error('Passenger container or template not found');
        return;
    }
    
    passengerCount++;
    
    // Clone template
    const passengerForm = template.content.cloneNode(true);
    
    // Update passenger number
    const passengerNumber = passengerForm.querySelector('.passenger-number');
    if (passengerNumber) {
        passengerNumber.textContent = passengerCount;
    }
    
    // Update form field names and IDs
    const inputs = passengerForm.querySelectorAll('input, select');
    inputs.forEach(input => {
        const baseName = input.name.replace('passenger_', '');
        input.name = `passenger_${passengerCount}_${baseName}`;
        input.id = `passenger_${passengerCount}_${baseName}`;
        
        // Add validation
        if (input.hasAttribute('required')) {
            input.addEventListener('invalid', function() {
                input.classList.add('is-invalid');
            });
            
            input.addEventListener('input', function() {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                }
            });
        }
    });
    
    // Add remove button functionality
    const removeBtn = passengerForm.querySelector('.btn-close');
    if (removeBtn) {
        removeBtn.addEventListener('click', function() {
            removePassenger(this.closest('.passenger-form'));
        });
    }
    
    // Add form to container
    container.appendChild(passengerForm);
    
    // Focus on first input
    const firstInput = container.querySelector(`.passenger-form:last-child input`);
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
    
    // Update passenger count display
    updatePassengerCountDisplay();
    
    console.log(`Added passenger ${passengerCount}`);
}

function removePassenger(passengerForm) {
    if (document.querySelectorAll('.passenger-form').length <= 1) {
        showNotification('At least one passenger is required', 'warning');
        return;
    }
    
    passengerForm.style.animation = 'slideOutUp 0.3s ease-out';
    setTimeout(() => {
        passengerForm.remove();
        updatePassengerCountDisplay();
    }, 300);
}

function updatePassengerCountDisplay() {
    const count = document.querySelectorAll('.passenger-form').length;
    const display = document.getElementById('passenger-count');
    if (display) {
        display.textContent = count;
    }
}

function updateTatkalTime() {
    const journeyDate = document.getElementById('journey-date')?.value;
    const travelClass = document.getElementById('travel-class')?.value;
    const tatkalTimeDisplay = document.getElementById('tatkal-time');
    
    if (!journeyDate || !travelClass || !tatkalTimeDisplay) {
        return;
    }
    
    try {
        const journey = new Date(journeyDate);
        const bookingDate = new Date(journey);
        bookingDate.setDate(bookingDate.getDate() - 1);
        
        // AC classes: 10:00 AM, Non-AC classes: 11:00 AM
        const acClasses = ['1A', '2A', '3A', 'CC', 'EC'];
        const isACClass = acClasses.includes(travelClass);
        const hour = isACClass ? 10 : 11;
        
        bookingDate.setHours(hour, 0, 0, 0);
        
        const options = {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        tatkalTimeDisplay.innerHTML = `
            <i class="fas fa-clock"></i> ${bookingDate.toLocaleDateString('en-IN', options)} IST
        `;
        
        tatkalTimeDisplay.className = `badge bg-${isACClass ? 'primary' : 'info'} fs-6`;
        
        // Check if Tatkal time has passed
        const now = new Date();
        if (now > bookingDate) {
            tatkalTimeDisplay.classList.add('bg-secondary');
            tatkalTimeDisplay.innerHTML += ' <small>(Passed)</small>';
        }
        
    } catch (error) {
        console.error('Error updating Tatkal time:', error);
        tatkalTimeDisplay.textContent = 'Invalid date/class';
    }
}

function togglePasswordVisibility() {
    const passwordInput = document.getElementById('password');
    const toggleBtn = document.getElementById('toggle-password');
    const icon = toggleBtn.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

function initializeStationAutocomplete() {
    const stationInputs = document.querySelectorAll('#from-station, #to-station');
    
    stationInputs.forEach(input => {
        input.addEventListener('input', handleStationInput);
        input.addEventListener('focus', () => {
            input.select();
        });
    });
}

function handleStationInput(event) {
    const input = event.target;
    const query = input.value.toLowerCase();
    
    if (query.length < 2) {
        return;
    }
    
    // This would typically fetch from a stations API
    // For now, using the predefined list
    const datalist = document.getElementById('stations-list');
    if (datalist) {
        const options = datalist.querySelectorAll('option');
        let hasMatch = false;
        
        options.forEach(option => {
            if (option.value.toLowerCase().includes(query)) {
                hasMatch = true;
            }
        });
        
        // Add visual feedback
        if (hasMatch) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else if (query.length > 3) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
        }
    }
}

function loadUserPreferences() {
    console.log('📋 Loading user preferences');
    
    try {
        const preferences = JSON.parse(localStorage.getItem('irctc_bot_preferences')) || {};
        
        // Apply theme preference
        if (preferences.theme && preferences.theme !== 'auto') {
            document.documentElement.setAttribute('data-bs-theme', preferences.theme);
        }
        
        // Apply other preferences
        if (preferences.autoSaveForm) {
            loadSavedFormData();
        }
        
        if (preferences.soundEnabled !== false) {
            enableSoundNotifications();
        }
        
    } catch (error) {
        console.error('Error loading user preferences:', error);
    }
}

function saveUserPreferences() {
    const preferences = {
        theme: document.documentElement.getAttribute('data-bs-theme') || 'auto',
        autoSaveForm: true,
        soundEnabled: true,
        lastUpdated: new Date().toISOString()
    };
    
    localStorage.setItem('irctc_bot_preferences', JSON.stringify(preferences));
}

function loadSavedFormData() {
    try {
        const savedData = JSON.parse(localStorage.getItem('irctc_bot_form_data')) || {};
        
        Object.keys(savedData).forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && field.type !== 'password') {
                if (field.type === 'checkbox') {
                    field.checked = savedData[fieldId];
                } else {
                    field.value = savedData[fieldId];
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading saved form data:', error);
    }
}

function saveFormData() {
    const formData = {};
    const formInputs = document.querySelectorAll('input, select, textarea');
    
    formInputs.forEach(input => {
        if (input.id && input.type !== 'password' && !input.name.includes('passenger')) {
            if (input.type === 'checkbox') {
                formData[input.id] = input.checked;
            } else {
                formData[input.id] = input.value;
            }
        }
    });
    
    localStorage.setItem('irctc_bot_form_data', JSON.stringify(formData));
}

function setupGlobalEventListeners() {
    // Auto-save form data
    document.addEventListener('change', debounce(saveFormData, 1000));
    
    // Handle form submissions
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleFormSubmission);
    }
    
    // Handle button clicks
    document.addEventListener('click', handleButtonClicks);
    
    // Handle window beforeunload
    window.addEventListener('beforeunload', function(event) {
        if (isFormSubmitting) {
            event.preventDefault();
            event.returnValue = 'Booking is in progress. Are you sure you want to leave?';
            return event.returnValue;
        }
    });
    
    // Handle online/offline status
    window.addEventListener('online', () => {
        showNotification('Connection restored', 'success');
        updateConnectionStatus('online');
    });
    
    window.addEventListener('offline', () => {
        showNotification('Connection lost', 'warning');
        updateConnectionStatus('offline');
    });
}

function handleFormSubmission(event) {
    event.preventDefault();
    
    if (isFormSubmitting) {
        showNotification('Please wait, booking is in progress...', 'warning');
        return;
    }
    
    const formData = new FormData(event.target);
    const bookingData = formDataToObject(formData);
    
    // Validate form
    if (!validateBookingData(bookingData)) {
        return;
    }
    
    // Show loading state
    showLoadingState(true);
    isFormSubmitting = true;
    
    // Submit booking
    submitBooking(bookingData);
}

function handleButtonClicks(event) {
    const target = event.target.closest('button');
    if (!target) return;
    
    switch (target.id) {
        case 'start-booking':
            startImmediateBooking();
            break;
        case 'schedule-booking':
            scheduleBooking();
            break;
        case 'save-config':
            saveConfiguration();
            break;
        case 'load-config':
            loadConfiguration();
            break;
    }
}

function startImmediateBooking() {
    const formData = collectFormData();
    
    if (!validateBookingData(formData)) {
        return;
    }
    
    if (!confirm('Start booking immediately? Make sure you have your mobile ready for OTP and payment.')) {
        return;
    }
    
    showLoadingState(true);
    
    fetch('/api/start_booking', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'booking_started') {
            showNotification('Booking started! Monitor the status page for updates.', 'success');
            // Redirect to status page
            setTimeout(() => {
                window.location.href = '/status';
            }, 2000);
        } else {
            throw new Error(data.error || 'Failed to start booking');
        }
    })
    .catch(error => {
        console.error('Error starting booking:', error);
        showNotification(`Failed to start booking: ${error.message}`, 'error');
    })
    .finally(() => {
        showLoadingState(false);
    });
}

function scheduleBooking() {
    const formData = collectFormData();
    
    if (!validateBookingData(formData)) {
        return;
    }
    
    showLoadingState(true);
    
    fetch('/api/schedule_booking', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'scheduled') {
            showNotification(`Booking scheduled successfully for ${data.booking_time}`, 'success');
        } else {
            throw new Error(data.error || 'Failed to schedule booking');
        }
    })
    .catch(error => {
        console.error('Error scheduling booking:', error);
        showNotification(`Failed to schedule booking: ${error.message}`, 'error');
    })
    .finally(() => {
        showLoadingState(false);
    });
}

function collectFormData() {
    const formData = {};
    
    // Basic journey details
    formData.from_station = document.getElementById('from-station')?.value;
    formData.to_station = document.getElementById('to-station')?.value;
    formData.journey_date = document.getElementById('journey-date')?.value;
    formData.travel_class = document.getElementById('travel-class')?.value;
    formData.train_number = document.getElementById('train-number')?.value;
    
    // Credentials
    formData.username = document.getElementById('username')?.value;
    formData.password = document.getElementById('password')?.value;

    console.log("Username:", formData.username);
    console.log("Password:", formData.password);

    
    // Payment details
    formData.upi_id = document.getElementById('upi-id')?.value;
    formData.upi_gateway = document.getElementById('upi-gateway')?.value;
    
    // Options
    formData.auto_upgrade = document.getElementById('auto-upgrade')?.checked;
    formData.travel_insurance = document.getElementById('travel-insurance')?.checked;
    
    // Collect passengers
    formData.passengers = collectPassengerData();
    
    return formData;
}

function collectPassengerData() {
    const passengers = [];
    const passengerForms = document.querySelectorAll('.passenger-form');
    
    passengerForms.forEach(form => {
        const passenger = {
            name: form.querySelector('.passenger-name')?.value,
            age: parseInt(form.querySelector('.passenger-age')?.value),
            gender: form.querySelector('.passenger-gender')?.value,
            berth_preference: form.querySelector('.passenger-berth')?.value
        };
        
        if (passenger.name && passenger.age && passenger.gender) {
            passengers.push(passenger);
        }
    });
    
    return passengers;
}

function validateBookingData(data) {
    const errors = [];
    
    // Validate basic fields
    if (!data.from_station) errors.push('From station is required');
    if (!data.to_station) errors.push('To station is required');
    if (!data.journey_date) errors.push('Journey date is required');
    if (!data.travel_class) errors.push('Travel class is required');
    if (!data.username) errors.push('IRCTC username is required');
    if (!data.password) errors.push('IRCTC password is required');
    
    // Validate passengers
    if (!data.passengers || data.passengers.length === 0) {
        errors.push('At least one passenger is required');
    }
    
    // Check if journey date is in the future
    if (data.journey_date) {
        const journeyDate = new Date(data.journey_date);
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(0, 0, 0, 0);
        
        if (journeyDate < tomorrow) {
            errors.push('Journey date must be from tomorrow onwards');
        }
    }
    
    if (errors.length > 0) {
        showNotification(`Please fix the following errors:\n• ${errors.join('\n• ')}`, 'error');
        return false;
    }
    
    return true;
}

function showLoadingState(show) {
    const overlay = document.getElementById('loading-overlay');
    const buttons = document.querySelectorAll('#start-booking, #schedule-booking');
    
    if (show) {
        overlay?.classList.remove('d-none');
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        });
    } else {
        overlay?.classList.add('d-none');
        buttons.forEach(btn => {
            btn.disabled = false;
        });
        
        const startBtn = document.getElementById('start-booking');
        const scheduleBtn = document.getElementById('schedule-booking');
        
        if (startBtn) {
            startBtn.innerHTML = '<i class="fas fa-rocket"></i> Start Booking Now';
        }
        if (scheduleBtn) {
            scheduleBtn.innerHTML = '<i class="fas fa-calendar-alt"></i> Schedule for Tatkal Time';
        }
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 350px;
        max-width: 500px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    // Add icon based on type
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    else if (type === 'warning') icon = 'fa-exclamation-triangle';
    else if (type === 'error') icon = 'fa-times-circle';
    
    notification.innerHTML = `
        <i class="fas ${icon} me-2"></i>
        ${message.replace(/\n/g, '<br>')}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    // Play sound if enabled
    playNotificationSound(type);
}

function playNotificationSound(type) {
    try {
        const preferences = JSON.parse(localStorage.getItem('irctc_bot_preferences')) || {};
        if (preferences.soundEnabled === false) return;
        
        // Create audio context for notification sounds
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Simple beep sound for notifications
        const frequency = type === 'error' ? 400 : type === 'success' ? 800 : 600;
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
        
    } catch (error) {
        console.log('Audio notification not available');
    }
}

function updateConnectionStatus(status) {
    const connectionBadge = document.getElementById('connection-status');
    if (!connectionBadge) return;
    
    connectionBadge.className = 'badge';
    
    switch (status) {
        case 'online':
            connectionBadge.classList.add('bg-success');
            connectionBadge.innerHTML = '<i class="fas fa-wifi"></i> Online';
            break;
        case 'offline':
            connectionBadge.classList.add('bg-danger');
            connectionBadge.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
            break;
        default:
            connectionBadge.classList.add('bg-secondary');
            connectionBadge.innerHTML = '<i class="fas fa-question"></i> Unknown';
    }
}

function checkBrowserCompatibility() {
    const issues = [];
    
    // Check for required APIs
    if (!window.WebSocket) issues.push('WebSocket support');
    if (!window.localStorage) issues.push('Local storage');
    if (!window.fetch) issues.push('Fetch API');
    if (!window.Promise) issues.push('Promise support');
    
    // Check browser version (basic check)
    const userAgent = navigator.userAgent;
    const isOldIE = userAgent.indexOf('MSIE') !== -1;
    const isOldChrome = /Chrome\/([0-9]+)/.test(userAgent) && parseInt(RegExp.$1) < 60;
    const isOldFirefox = /Firefox\/([0-9]+)/.test(userAgent) && parseInt(RegExp.$1) < 55;
    
    if (isOldIE || isOldChrome || isOldFirefox) {
        issues.push('Modern browser version');
    }
    
    if (issues.length > 0) {
        showNotification(
            `Your browser may not be fully compatible. Missing: ${issues.join(', ')}. Please update your browser for the best experience.`,
            'warning',
            0
        );
    }
}

function formDataToObject(formData) {
    const object = {};
    formData.forEach((value, key) => {
        object[key] = value;
    });
    return object;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function enableSoundNotifications() {
    // Request permission for audio if needed
    if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
        document.addEventListener('click', function enableAudio() {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            const audioContext = new AudioContextClass();
            
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            
            document.removeEventListener('click', enableAudio);
        }, { once: true });
    }
}

// Utility functions
function formatTime(date) {
    return new Intl.DateTimeFormat('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(date);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-IN', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// Export functions for use in other scripts
window.IRCTCBot = {
    showNotification,
    updateConnectionStatus,
    collectFormData,
    validateBookingData,
    showLoadingState,
    addPassenger,
    updateTatkalTime
};

console.log('✅ IRCTC Tatkal Bot main script loaded successfully');

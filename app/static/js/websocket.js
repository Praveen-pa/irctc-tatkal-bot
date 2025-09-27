/**
 * IRCTC Tatkal Automation Bot - WebSocket Communication
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        
        this.init();
    }
    
    init() {
        console.log('Initializing WebSocket connection...');
        
        // Initialize Socket.IO connection
        this.socket = io({
            transports: ['websocket', 'polling'],
            timeout: 20000,
            reconnection: true,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: this.reconnectDelay
        });
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('error');
        });
        
        // Booking status updates
        this.socket.on('booking_status', (data) => {
            this.handleBookingStatus(data);
        });
        
        // Captcha request
        this.socket.on('captcha_required', (data) => {
            this.handleCaptchaRequest(data);
        });
        
        // OTP request
        this.socket.on('otp_required', (data) => {
            this.handleOTPRequest(data);
        });
        
        // Real-time updates
        this.socket.on('live_update', (data) => {
            this.addLiveUpdate(data);
        });
        
        // System status
        this.socket.on('system_status', (data) => {
            this.updateSystemStatus(data);
        });
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        statusElement.className = 'badge';
        
        switch(status) {
            case 'connected':
                statusElement.classList.add('bg-success');
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
                break;
            case 'disconnected':
                statusElement.classList.add('bg-danger');
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
                break;
            case 'error':
                statusElement.classList.add('bg-warning');
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                break;
            default:
                statusElement.classList.add('bg-secondary');
                statusElement.innerHTML = '<i class="fas fa-circle"></i> Connecting...';
        }
    }
    
    handleBookingStatus(data) {
        console.log('Booking status update:', data);
        
        // Update current status section
        this.updateCurrentStatus(data);
        
        // Add to live updates
        this.addLiveUpdate(data);
        
        // Show toast notification
        this.showToast(data);
        
        // Update bot status indicator
        this.updateBotStatus(data);
    }
    
    updateCurrentStatus(data) {
        const statusElement = document.getElementById('current-status');
        if (!statusElement) return;
        
        const statusHtml = `
            <div class="text-center">
                <div class="status-icon mb-2">
                    ${this.getStatusIcon(data.type)}
                </div>
                <h6 class="status-step">${data.step || 'Unknown Step'}</h6>
                <p class="status-message mb-2">${data.message}</p>
                <small class="text-muted">
                    <i class="fas fa-clock"></i> ${this.formatTime(data.timestamp)}
                </small>
            </div>
        `;
        
        statusElement.innerHTML = statusHtml;
    }
    
    getStatusIcon(type) {
        const iconClass = type === 'error' ? 'text-danger' : 
                         type === 'warning' ? 'text-warning' :
                         type === 'success' ? 'text-success' : 'text-info';
        
        const iconName = type === 'error' ? 'fa-exclamation-triangle' :
                        type === 'warning' ? 'fa-exclamation-circle' :
                        type === 'success' ? 'fa-check-circle' : 'fa-info-circle';
        
        return `<i class="fas ${iconName} fa-2x ${iconClass}"></i>`;
    }
    
    addLiveUpdate(data) {
        const updatesContainer = document.getElementById('live-updates');
        if (!updatesContainer) return;
        
        // Remove "no updates" message if present
        const noUpdatesMsg = updatesContainer.querySelector('.text-muted');
        if (noUpdatesMsg) {
            noUpdatesMsg.remove();
        }
        
        // Create update element
        const updateElement = document.createElement('div');
        updateElement.className = `alert alert-${this.getAlertClass(data.type)} alert-dismissible fade show`;
        updateElement.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-shrink-0 me-2">
                    ${this.getStatusIcon(data.type)}
                </div>
                <div class="flex-grow-1">
                    <strong>${data.step || 'Update'}</strong><br>
                    <small>${data.message}</small><br>
                    <small class="text-muted">
                        <i class="fas fa-clock"></i> ${this.formatTime(data.timestamp)}
                    </small>
                </div>
                <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Add to top of updates
        updatesContainer.insertBefore(updateElement, updatesContainer.firstChild);
        
        // Limit to last 10 updates
        const updates = updatesContainer.querySelectorAll('.alert');
        if (updates.length > 10) {
            updates[updates.length - 1].remove();
        }
        
        // Auto-scroll to latest update
        updatesContainer.scrollTop = 0;
    }
    
    getAlertClass(type) {
        switch(type) {
            case 'error': return 'danger';
            case 'warning': return 'warning';
            case 'success': return 'success';
            default: return 'info';
        }
    }
    
    handleCaptchaRequest(data) {
        console.log('Captcha request:', data);
        
        // Show captcha modal
        const captchaModal = new bootstrap.Modal(document.getElementById('captchaModal'));
        const captchaImage = document.getElementById('captcha-image');
        const captchaInput = document.getElementById('captcha-input');
        
        // Set image source (convert relative path to full URL)
        captchaImage.src = `/${data.image_path}`;
        captchaInput.value = '';
        captchaInput.focus();
        
        captchaModal.show();
        
        // Add submit handler
        const submitBtn = document.getElementById('submit-captcha');
        const submitHandler = () => {
            const captchaText = captchaInput.value.trim();
            if (captchaText) {
                this.submitCaptcha(captchaText);
                captchaModal.hide();
            }
            submitBtn.removeEventListener('click', submitHandler);
        };
        
        submitBtn.addEventListener('click', submitHandler);
        
        // Handle Enter key
        const enterHandler = (e) => {
            if (e.key === 'Enter') {
                submitHandler();
                captchaInput.removeEventListener('keypress', enterHandler);
            }
        };
        
        captchaInput.addEventListener('keypress', enterHandler);
    }
    
    handleOTPRequest(data) {
        console.log('OTP request:', data);
        
        // Show OTP modal
        const otpModal = new bootstrap.Modal(document.getElementById('otpModal'));
        const otpInput = document.getElementById('otp-input');
        
        otpInput.value = '';
        otpInput.focus();
        
        otpModal.show();
        
        // Add submit handler
        const submitBtn = document.getElementById('submit-otp');
        const submitHandler = () => {
            const otp = otpInput.value.trim();
            if (otp && otp.length === 6) {
                this.submitOTP(otp);
                otpModal.hide();
            }
        };
        
        submitBtn.addEventListener('click', submitHandler);
        
        // Handle Enter key
        const enterHandler = (e) => {
            if (e.key === 'Enter') {
                submitHandler();
                otpInput.removeEventListener('keypress', enterHandler);
            }
        };
        
        otpInput.addEventListener('keypress', enterHandler);
        
        // Auto-submit when 6 digits are entered
        const inputHandler = () => {
            if (otpInput.value.length === 6) {
                setTimeout(submitHandler, 500); // Small delay for user confirmation
                otpInput.removeEventListener('input', inputHandler);
            }
        };
        
        otpInput.addEventListener('input', inputHandler);
    }
    
    submitCaptcha(captchaText) {
        console.log('Submitting captcha response');
        this.socket.emit('captcha_response', { captcha_text: captchaText });
    }
    
    submitOTP(otp) {
        console.log('Submitting OTP response');
        this.socket.emit('otp_response', { otp: otp });
    }
    
    updateSystemStatus(data) {
        // Update individual status indicators
        Object.keys(data).forEach(service => {
            const statusElement = document.getElementById(`${service}-status`);
            if (statusElement) {
                statusElement.className = `status-dot bg-${data[service] === 'healthy' ? 'success' : 'danger'}`;
            }
        });
    }
    
    updateBotStatus(data) {
        const botStatusElement = document.getElementById('bot-status');
        if (!botStatusElement) return;
        
        let statusClass = 'bg-secondary';
        
        if (data.step === 'booking_complete') {
            statusClass = data.type === 'success' ? 'bg-success' : 'bg-danger';
        } else if (data.step && data.step !== 'idle') {
            statusClass = 'bg-primary';
        }
        
        botStatusElement.className = `status-dot ${statusClass}`;
    }
    
    showToast(data) {
        const toast = document.getElementById('status-toast');
        const toastIcon = document.getElementById('toast-icon');
        const toastTitle = document.getElementById('toast-title');
        const toastMessage = document.getElementById('toast-message');
        const toastTime = document.getElementById('toast-time');
        
        if (!toast) return;
        
        // Set content
        toastIcon.innerHTML = this.getStatusIcon(data.type);
        toastTitle.textContent = data.step || 'Status Update';
        toastMessage.textContent = data.message;
        toastTime.textContent = this.formatTime(data.timestamp);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    formatTime(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
    
    // Public methods for external use
    sendMessage(event, data) {
        if (this.isConnected) {
            this.socket.emit(event, data);
        } else {
            console.error('WebSocket not connected');
        }
    }
    
    isConnectedToServer() {
        return this.isConnected;
    }
}

// Global WebSocket instance
let webSocketClient;

// Initialize WebSocket connection
function initWebSocket() {
    webSocketClient = new WebSocketClient();
    return webSocketClient;
}

// Export for use in other scripts
window.WebSocketClient = WebSocketClient;
window.webSocketClient = webSocketClient;
window.initWebSocket = initWebSocket;
# IRCTC Tatkal Automation Bot

<div align="center">

![IRCTC Tatkal Bot](https://img.shields.io/badge/IRCTC-Tatkal%20Bot-blue?style=for-the-badge&logo=train&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3+-red?style=for-the-badge&logo=flask&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Latest-green?style=for-the-badge&logo=playwright&logoColor=white)

**Fast, Reliable, and Secure Tatkal Ticket Booking Automation**

</div>

## 🚀 Features

### Core Functionality
- **⚡ Lightning Fast**: Optimized for speed with headless browser automation
- **🎯 Tatkal Precision**: Atomic-level timing with NTP synchronization
- **📱 Mobile Friendly**: Responsive web interface accessible on all devices
- **🔐 Secure**: Encrypted credential storage and secure data handling
- **🤖 Smart Automation**: Handles all repetitive tasks while keeping manual inputs for compliance

### User Experience
- **🌐 Web-Based Interface**: No software installation required
- **📋 Pre-filled Forms**: Save passenger details and booking preferences
- **⏰ Scheduled Booking**: Automatic execution at Tatkal opening time
- **📊 Real-time Updates**: Live status monitoring with WebSocket communication
- **📸 Smart Captcha Handling**: Screenshot display for quick manual entry
- **💳 Payment Integration**: UPI gateway selection and payment monitoring

### Technical Excellence
- **☁️ Cloud Optimized**: Designed for AWS Mumbai region deployment
- **🔄 Auto Retry**: Intelligent fallback and retry mechanisms
- **📈 Performance Monitoring**: Built-in metrics and health checks
- **🛡️ Error Handling**: Comprehensive error detection and recovery
- **📝 Detailed Logging**: Complete audit trail of all operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask Server  │    │ Headless Chrome │
│                 │◄──►│                 │◄──►│                 │
│   React UI      │    │   WebSocket     │    │   Playwright    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   Scheduler     │    │   IRCTC.co.in   │
│ Captcha/OTP/Pay │    │   NTP Sync      │    │   Booking       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚦 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/irctc-tatkal-bot.git
cd irctc-tatkal-bot

# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:5000
```

### Option 2: Manual Installation

```bash
# Clone and setup
git clone https://github.com/yourusername/irctc-tatkal-bot.git
cd irctc-tatkal-bot

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env file

# Run the application
python run.py
```

### Option 3: AWS Cloud Deployment

```bash
# Deploy to AWS Mumbai region
chmod +x deploy/aws_setup.sh
./deploy/aws_setup.sh
```

## 📋 Usage Guide

### 1. Initial Setup
1. **Access Interface**: Open `http://localhost:5000` in your browser
2. **Configure Settings**: Go to Settings page and set your preferences
3. **Test Connection**: Verify all systems are working

### 2. Booking Configuration
1. **Journey Details**: Enter from/to stations, date, and class
2. **Passenger Information**: Add all passenger details
3. **Login Credentials**: Provide IRCTC username and password
4. **Payment Setup**: Configure UPI preferences

### 3. Booking Execution
#### Scheduled Booking (Recommended)
1. Click **"Schedule for Tatkal Time"**
2. Bot automatically starts at Tatkal opening time
3. Monitor progress in real-time
4. Handle captcha/OTP prompts when they appear

#### Immediate Booking
1. Click **"Start Booking Now"** for immediate execution
2. Follow real-time updates
3. Complete manual steps (captcha, OTP, payment approval)

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Basic Configuration
SECRET_KEY=your-super-secret-key
DEBUG=False
HOST=0.0.0.0
PORT=5000

# Security
ENCRYPTION_KEY=your-32-character-encryption-key
SESSION_TIMEOUT=3600

# Performance
PLAYWRIGHT_HEADLESS=True
MAX_CONCURRENT_BOOKINGS=1
BROWSER_TIMEOUT=300

# Timing
NTP_SERVER=pool.ntp.org
TATKAL_AC_TIME=10:00
TATKAL_NON_AC_TIME=11:00
```

### Passenger Configuration

Save frequent travelers in `config/passengers.json`:

```json
{
  "passengers": [
    {
      "name": "John Doe",
      "age": 30,
      "gender": "M",
      "berth_preference": "LB"
    }
  ],
  "default_preferences": {
    "auto_upgrade": true,
    "travel_insurance": false
  }
}
```

## 🔒 Security & Compliance

### Data Protection
- **🔐 Encryption**: All sensitive data encrypted at rest
- **🛡️ No Data Storage**: Credentials never stored in plain text
- **🚫 No Automation of Security**: Captcha, OTP, and payments remain manual
- **📊 Audit Logs**: Complete tracking of all operations

### IRCTC Compliance
- **✅ Manual Captcha**: Never bypassed automatically
- **✅ Manual OTP**: User enters OTP from SMS
- **✅ Manual Payment**: User approves UPI transaction
- **✅ Rate Limiting**: Respects IRCTC's request limits
- **✅ Personal Use**: Designed for individual booking only

## 🚀 Deployment Options

### Local Development
```bash
python run.py
```

### Docker Production
```bash
docker-compose -f docker-compose.yml up -d
```

### AWS EC2 (Mumbai Region)
```bash
./deploy/aws_setup.sh
```

### Cloud Providers
- **AWS**: Mumbai region for lowest latency
- **Google Cloud**: Asia-South1 region
- **Azure**: Central India region

## 📊 Monitoring & Logging

### Health Checks
- **Application**: `GET /api/health`
- **Database**: Connection and query testing
- **Browser**: Playwright engine status
- **IRCTC**: Website accessibility check

### Performance Metrics
- **Booking Speed**: End-to-end timing
- **Success Rate**: Booking completion percentage
- **Error Tracking**: Failure analysis and patterns
- **System Resources**: CPU, memory, network usage

### Logs Location
- **Application Logs**: `logs/app.log`
- **Booking Logs**: `logs/booking.log`
- **Error Logs**: `logs/errors.log`
- **Performance Logs**: `logs/performance.log`

## 🔧 API Documentation

### REST Endpoints

```http
POST /api/schedule_booking
POST /api/start_booking
GET  /api/booking_status
POST /api/stop_booking
GET  /api/health
```

### WebSocket Events

```javascript
// Client to Server
socket.emit('captcha_response', { captcha_text: 'ABC123' });
socket.emit('otp_response', { otp: '123456' });

// Server to Client
socket.on('booking_status', (data) => { /* handle status */ });
socket.on('captcha_required', (data) => { /* show captcha */ });
socket.on('otp_required', (data) => { /* request OTP */ });
```

## 🐛 Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check if IRCTC is accessible
curl -I https://www.irctc.co.in

# Verify NTP synchronization
ntpdate -q pool.ntp.org
```

#### Browser Issues
```bash
# Reinstall Playwright browsers
playwright install --force chromium

# Check browser dependencies
playwright install-deps
```

#### Performance Issues
```bash
# Monitor resource usage
htop

# Check network latency to IRCTC
ping www.irctc.co.in
```

### Log Analysis
```bash
# View recent application logs
tail -f logs/app.log

# Check error patterns
grep "ERROR" logs/app.log | tail -20

# Monitor booking attempts
grep "booking" logs/booking.log
```

## 🛠️ Development

### Project Structure
```
irctc-tatkal-bot/
├── app/                 # Application source code
│   ├── bot/            # Automation logic
│   ├── web/            # Web interface
│   ├── utils/          # Utilities
│   └── templates/      # HTML templates
├── config/             # Configuration files
├── deploy/             # Deployment scripts
├── logs/               # Log files
└── tests/              # Test suite
```

### Running Tests
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run test suite
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This bot is designed for **personal use only** to automate repetitive tasks in train ticket booking. It maintains compliance with IRCTC's terms of service by:

- Requiring manual captcha solving
- Requiring manual OTP entry
- Requiring manual payment approval
- Not bypassing any security measures
- Operating at human-like speeds

Users are responsible for ensuring compliance with IRCTC's terms of service and applicable laws.

## 🤝 Support

### Community
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Community support and questions
- **Wiki**: Detailed documentation and guides

### Professional Support
For enterprise deployments or custom modifications, contact:
- **Email**: support@ircbotpro.com
- **Telegram**: @irctc_bot_support

## 🙏 Acknowledgments

- **IRCTC**: For providing the platform for train bookings
- **Playwright**: For the excellent browser automation framework
- **Flask**: For the lightweight and powerful web framework
- **Contributors**: All developers who have contributed to this project

---

<div align="center">

**Made with ❤️ for hassle-free train booking**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/irctc-tatkal-bot?style=social)](https://github.com/yourusername/irctc-tatkal-bot)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/irctc-tatkal-bot?style=social)](https://github.com/yourusername/irctc-tatkal-bot)

</div>
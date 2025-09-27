# IRCTC Tatkal Automation Bot - Complete Project Structure

```
irctc-tatkal-bot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Flask application entry point
│   ├── config.py                  # Application configuration
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── irctc_automation.py    # Core Playwright automation
│   │   ├── scheduler.py           # Timing and scheduling logic
│   │   ├── captcha_handler.py     # Screenshot and UI integration
│   │   └── payment_handler.py     # Payment processing logic
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py              # Web API endpoints
│   │   ├── websocket_handler.py   # Real-time communication
│   │   └── forms.py               # Form validation and handling
│   ├── templates/
│   │   ├── base.html              # Base template
│   │   ├── index.html             # Main booking interface
│   │   ├── status.html            # Real-time status page
│   │   ├── config.html            # Settings and preferences
│   │   └── components/
│   │       ├── navbar.html        # Navigation component
│   │       ├── booking_form.html  # Booking form component
│   │       └── status_monitor.html # Status monitoring component
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css           # Main stylesheet
│   │   │   ├── mobile.css         # Mobile responsive styles
│   │   │   └── components.css     # Component-specific styles
│   │   ├── js/
│   │   │   ├── main.js            # Main JavaScript logic
│   │   │   ├── booking.js         # Booking form handling
│   │   │   ├── status.js          # Real-time status updates
│   │   │   └── websocket.js       # WebSocket communication
│   │   ├── images/
│   │   │   ├── logo.png           # Application logo
│   │   │   ├── favicon.ico        # Favicon
│   │   │   └── icons/             # Various icons
│   │   └── fonts/                 # Custom fonts if needed
│   └── utils/
│       ├── __init__.py
│       ├── encryption.py          # Secure credential storage
│       ├── validation.py          # Input validation and sanitization
│       ├── logging.py             # Comprehensive logging system
│       ├── database.py            # Database operations
│       └── helpers.py             # Utility functions
├── config/
│   ├── app_config.json            # Application settings
│   ├── passengers_template.json   # Passenger data template
│   ├── routes_template.json       # Frequently used routes template
│   └── deployment_config.json     # Deployment configuration
├── logs/
│   ├── .gitkeep                   # Keep logs directory in git
│   └── README.md                  # Log files information
├── temp/
│   ├── .gitkeep                   # Keep temp directory in git
│   └── README.md                  # Temporary files information
├── tests/
│   ├── __init__.py
│   ├── test_automation.py         # Bot automation tests
│   ├── test_web_interface.py      # Web interface tests
│   └── test_utils.py              # Utility function tests
├── deploy/
│   ├── Dockerfile                 # Container configuration
│   ├── docker-compose.yml         # Local development setup
│   ├── docker-compose.prod.yml    # Production setup
│   ├── nginx.conf                 # Reverse proxy configuration
│   ├── aws_setup.sh               # AWS deployment script
│   ├── install_dependencies.sh    # System dependencies installer
│   └── systemd/
│       ├── irctc-bot.service      # Systemd service configuration
│       └── nginx.service          # Nginx service configuration
├── docs/
│   ├── README.md                  # Main documentation
│   ├── SETUP.md                   # Setup instructions
│   ├── API.md                     # API documentation
│   ├── DEPLOYMENT.md              # Deployment guide
│   └── TROUBLESHOOTING.md         # Common issues and solutions
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── .dockerignore                  # Docker ignore rules
├── README.md                      # Project overview
├── LICENSE                        # License file
└── run.py                         # Application runner script
```

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python run.py`
5. Access web interface at `http://localhost:5000`

## Deployment

- **Local Development**: Use `docker-compose up`
- **Production**: Use AWS deployment script in `deploy/` folder
- **Manual**: Follow instructions in `docs/DEPLOYMENT.md`
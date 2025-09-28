# Use Playwright's official image with dependencies preinstalled
FROM mcr.microsoft.com/playwright/python:latest

# Create and set workdir
WORKDIR /app

# Copy only Python requirements first
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Create a basic .env file with default values
RUN echo "SECRET_KEY=your-super-secret-key-change-in-production" > .env && \
    echo "DEBUG=False" >> .env && \
    echo "HOST=0.0.0.0" >> .env && \
    echo "PORT=5000" >> .env && \
    echo "ENVIRONMENT=production" >> .env && \
    echo "PLAYWRIGHT_HEADLESS=True" >> .env && \
    echo "LOG_LEVEL=INFO" >> .env && \
    echo "ENCRYPTION_KEY=your-32-character-encryption-key!" >> .env

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "run.py"]

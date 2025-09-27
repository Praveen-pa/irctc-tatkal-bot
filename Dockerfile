# Use Playwright’s official image with dependencies preinstalled
FROM mcr.microsoft.com/playwright/python:latest

# Create and set workdir
WORKDIR /app

# Copy only Python requirements first
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Expose port
EXPOSE 5000

# Create environment file from example
RUN cp .env.example .env

# Start the app
CMD ["python", "run.py"]

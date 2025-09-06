# Base image with Playwright and Python
FROM mcr.microsoft.com/playwright/python:v1.43.0-focal

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set default browser channel to Firefox
ENV PLAYWRIGHT_BROWSERS_PATH=0
RUN playwright install firefox

# Launch scraper in headful mode
CMD ["python", "scraper/main.py", "--headless=false"]

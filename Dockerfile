FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app
VOLUME ["/data"]
ENV CSV_PATH=/data/scraped_apps.csv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install firefox

COPY scraper ./scraper

ENV PYTHONUNBUFFERED=1

CMD ["python", "scraper/main.py"]

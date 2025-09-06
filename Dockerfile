FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install firefox

COPY scraper ./scraper

ENV PYTHONUNBUFFERED=1

CMD ["python", "scraper/main.py"]

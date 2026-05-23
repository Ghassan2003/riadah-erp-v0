# Backend Dockerfile - Django Application
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies + Arabic fonts for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles

RUN addgroup --system app && adduser --system --ingroup app app
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Start Daphne ASGI server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]

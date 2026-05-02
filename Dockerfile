# ── Build stage ───────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY templates/ templates/
COPY static/   static/

# Create directories for ERD files and user uploads
RUN mkdir -p erd uploads

# ── Runtime config ────────────────────────────────────────────
ENV FLASK_DEBUG=false
ENV FLASK_SECRET_KEY=change-me-in-production

EXPOSE 5000

# Use gunicorn for production; fall back to flask dev server if not installed
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]

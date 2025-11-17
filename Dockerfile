FROM python:3.11-slim

# Run Python in unbuffered mode and avoid writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal OS-level dependencies. `curl` is used by the HEALTHCHECK.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version for reproducible installs
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first so Docker can cache installed dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a dedicated non-root user
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

# Default SQLite DB location inside container; exposed as a volume
ENV FOODID_DB=/data/foodid.db
VOLUME ["/data"]

# Expose Flask port
EXPOSE 5000

# Switch to non-root user
USER app

# Healthcheck hitting Flask /health endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD curl -f http://127.0.0.1:5000/health || exit 1

# Default command: run Flask dev server
ENV FLASK_APP=app.py
CMD ["python", "app.py"]

# Production example (uncomment and ensure gunicorn is in requirements):
# ENTRYPOINT ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

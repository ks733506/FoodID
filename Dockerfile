FROM python:3.11-slim

# Run Python in unbuffered mode and avoid writing .pyc files to reduce
# surprises when running in containers and to make logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal OS-level dependencies. `curl` is used by the HEALTHCHECK
# below. `build-essential` is useful if any dependency needs to be compiled.
# Keep the layer small and clean up apt caches afterwards.
RUN apt-get update \
		&& apt-get install -y --no-install-recommends \
			 curl \
			 build-essential \
		&& rm -rf /var/lib/apt/lists/*

# Copy requirements first so Docker can cache installed dependencies when only
# application code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a dedicated (non-root) user to run the app for better security.
RUN addgroup --system app \
		&& adduser --system --ingroup app app \
		&& chown -R app:app /app

# Default location of the SQLite DB inside the container; exposed as a
# volume so data persists across container restarts when the volume is mounted.
ENV FOODID_DB=/data/foodid.db
VOLUME ["/data"]

# Expose the port the Flask app listens on. The app prints the precise URL
# when it starts; this is the commonly used default.
EXPOSE 5000

# Switch to the non-root user
USER app

# A lightweight healthcheck used by container orchestrators to verify the
# service is up. It hits the Flask `/health` endpoint. The check uses curl
# which we installed earlier.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
	CMD curl -f http://127.0.0.1:5000/health || exit 1

# Default command: run the Flask development server. For production, prefer
# running behind a WSGI server such as gunicorn (example below). Keep this
# as the default so `docker run` works for local development and demos.
CMD ["python", "app.py"]

# Production example (uncomment and ensure `gunicorn` is in requirements):
# ENTRYPOINT ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

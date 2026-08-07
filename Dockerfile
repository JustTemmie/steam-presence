FROM python:3.14-slim

# Create a non-root user
RUN groupadd -r app -g 1000 && \
    useradd -r -u 1000 -g app app

WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership
COPY --chown=app:app . .

# Make /app writable by appuser (for runtime file creation)
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Run the application
CMD ["python", "-u", "main.py"]

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash imgserv

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create directories
RUN mkdir -p /var/lib/imgserv/images /var/lib/imgserv/sequences /var/log/imgserv

# Set ownership
RUN chown -R imgserv:imgserv /app /var/lib/imgserv /var/log/imgserv

# Switch to non-root user
USER imgserv

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["python", "main.py"]

# Build stage
FROM alpine:3.23.0 AS builder

# Upgrade system packages
RUN apk upgrade

# Install Python and build dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    python3-dev \
    && python3 -m venv /opt/venv

# Make sure we use venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Production stage
FROM alpine:3.23.0

# Upgrade system packages
RUN apk upgrade

# Install Python runtime only
RUN apk add --no-cache \
    python3 \
    && addgroup -g 1001 -S appuser \
    && adduser -u 1001 -S appuser -G appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Upgrade pip
RUN /opt/venv/bin/pip install -U pip

# Make sure we use venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY main.py validation.py .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for health checks
EXPOSE 8080

# Command to run
CMD ["python3", "main.py"]

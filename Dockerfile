# Multi-stage build for smaller image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies in builder stage
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy source code
COPY src/ ./src/

# Make sure scripts are executable
ENV PATH=/root/.local/bin:$PATH

# Set environment for production
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Health check (optional - Railway doesn't require it but good practice)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import redis; r = redis.from_url('${REDIS_URL}'); r.ping()" || exit 1

# Run the bot
CMD ["python", "-u", "-m", "src.bot"]

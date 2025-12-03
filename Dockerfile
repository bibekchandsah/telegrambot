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

# Run the bot
CMD ["python", "-u", "-m", "src.bot"]

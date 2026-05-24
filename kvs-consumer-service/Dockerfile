FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m -u 1000 gympt

# Copy Python dependencies from builder and change ownership
COPY --from=builder --chown=gympt:gympt /root/.local /home/gympt/.local

# Copy application code
COPY --chown=gympt:gympt src/ ./src/

# Switch to non-root user
USER gympt

# Make sure scripts in .local are usable
ENV PATH=/home/gympt/.local/bin:$PATH

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8003/health', timeout=5)"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]

# ============================================
# Multi-Stage Build for Posture Analysis Service
# ============================================

# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim

# Install runtime dependencies
# Note: Using python-opencv which includes all necessary OpenCV libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r gympt && useradd -r -g gympt gympt

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/gympt/.local

# Copy application code
COPY app ./app

# Change ownership
RUN chown -R gympt:gympt /app

# Switch to non-root user
USER gympt

# Add local Python packages to PATH
ENV PATH=/home/gympt/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

# ==========================================
# Stage 1: Build dependencies
# ==========================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install GCC and libopus-dev for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libopus-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ==========================================
# Stage 2: Final minimal runtime environment
# ==========================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime libopus library
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY . .

# Expose keep-alive web server port (should match the PORT env variable)
EXPOSE 8080

# Execute bot
CMD ["python", "bot.py"]

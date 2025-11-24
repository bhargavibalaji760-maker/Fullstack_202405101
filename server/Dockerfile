FROM python:3.10-slim

WORKDIR /app

# Install system libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../app/requirements.txt /app/requirements.txt

# Install Python deps
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy app
COPY ../app /app/app

# Expose port
EXPOSE 8000

# ✅ Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

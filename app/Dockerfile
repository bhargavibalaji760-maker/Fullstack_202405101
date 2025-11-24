FROM python:3.10-slim

WORKDIR /app

# Copy requirements first (better cache)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the whole FastAPI app
COPY . /app

EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

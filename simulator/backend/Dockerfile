# EV-CyberRange Backend
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create data directories
RUN mkdir -p /app/data /app/logs

# Environment
ENV PYTHONUNBUFFERED=1
ENV MQTT_HOST=mqtt
ENV MQTT_PORT=1883

# Expose API port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# EV-CyberRange CSMS
# Lightweight OCPP 1.6J Central System
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY csms_server.py .

# Expose OCPP WebSocket port and HTTP API port
EXPOSE 9000 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost',9000)); s.close()" || exit 1

CMD ["python", "-u", "csms_server.py"]

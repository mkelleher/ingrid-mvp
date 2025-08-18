# Ultra-minimal Dockerfile - Should work on all platforms
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies only
COPY backend/requirements-no-ocr.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 8001

# Start the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
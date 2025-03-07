FROM python:3.9-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && \
    git config --global user.name "Wenote App" && \
    git config --global user.email "app@wenote.example.com"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV FLASK_APP=app
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"] 
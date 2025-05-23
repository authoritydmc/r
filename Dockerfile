# Dockerfile for Flask URL Shortener/Redirector
FROM python:3.11-slim

WORKDIR /app

# Install git for version info support
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["python", "app.py"]
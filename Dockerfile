# Dockerfile for Flask URL Shortener/Redirector
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

# Use Gunicorn with gevent as the worker class
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]

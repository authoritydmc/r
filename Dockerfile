# Dockerfile for Flask URL Shortener/Redirector
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

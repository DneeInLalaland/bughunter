FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install flask flask-cors requests beautifulsoup4 || true

EXPOSE 5001

CMD ["python", "app.py"]

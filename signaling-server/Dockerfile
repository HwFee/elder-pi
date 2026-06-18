FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p uploads/avatars

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

# Install Chromium for kiosk mode; X11/display setup is host-dependent.
RUN apt-get update && \
    apt-get install -y --no-install-recommends chromium && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 3000

CMD ["python3", "launcher.py", "--host", "0.0.0.0", "--backend", "http://signaling-server:8000"]

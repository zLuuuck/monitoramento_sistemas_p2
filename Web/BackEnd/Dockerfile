FROM python:3.12-slim

WORKDIR /app

# só o netcat pro entrypoint esperar o postgres — sem gcc, sem postgresql-dev, sem LLVM
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

EXPOSE 5000
ENTRYPOINT ["./entrypoint.sh"]
FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev postgresql-dev netcat-openbsd

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
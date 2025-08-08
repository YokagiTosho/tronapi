FROM python:3.13.6-slim

WORKDIR /app

COPY ./src .

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r "requirements.txt"

EXPOSE 8000

CMD ["/bin/sh", "-c", "exec fastapi dev tronapi/main.py --host 0.0.0.0"]

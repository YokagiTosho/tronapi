FROM python:3.13.6-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r "requirements.txt"

EXPOSE 8000

CMD ["uvicorn", "tronapi.main:app", "--host", "0.0.0.0", "--port", "8000"]

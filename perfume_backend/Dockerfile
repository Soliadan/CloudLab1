
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
       "psycopg[binary]==3.2.10" \
       "python-dotenv==1.0.1" \
       "gunicorn>=22,<24"

COPY . .

EXPOSE 8088

CMD ["gunicorn", "--bind", "0.0.0.0:8088", "main_pg:app"]


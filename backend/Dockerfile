FROM python:3.11-slim

WORKDIR /app

# Install dependencies for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
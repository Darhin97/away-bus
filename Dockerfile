FROM python:3.13
LABEL authors="derrickankrah"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


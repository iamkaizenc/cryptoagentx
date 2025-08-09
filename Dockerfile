FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY app /srv/app

RUN pip install --no-cache-dir -r /srv/app/requirements.txt

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

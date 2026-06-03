FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/controlcash

COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--preload", "-w", "2", "--threads", "4", "-b", "0.0.0.0:5000", "api.app:app", "--access-logfile", "-", "--error-logfile", "-"]
FROM python:3.11-slim@sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin api

# Runtime dependencies are cached separately from the application code.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=10001:10001 . .
RUN chmod 0755 docker-entrypoint.sh

USER 10001
EXPOSE 8088

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8088", "--workers", "2", "--timeout", "30", "--graceful-timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "main_pg:app"]

FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        build-essential \
        python3-gdal \
        libspatialindex-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash acceslibre
USER acceslibre

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings_dev
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv venv && \
    uv sync --dev

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

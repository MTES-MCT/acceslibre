FROM python:3.14.8-slim
# Pinned uv version: the eSign root CA removal requires uv >= 0.13.4
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /uvx /bin/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        gdal-bin \
        libgdal-dev \
        build-essential \
        python3-gdal \
        libspatialindex-dev \
        gettext \
        libpango-1.0-0 libpangoft2-1.0-0 libgobject-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Fetch the latest system CA certificates (eMudhra / eSign root CA removal)
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# pip bundles its own CA bundle: it must be >= 26.2.2 (eSign root CA removal)
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.2.2"

RUN useradd -ms /bin/bash acceslibre
USER acceslibre

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings_dev
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv venv && \
    uv sync --dev

COPY . .

EXPOSE 7000

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:7000"]

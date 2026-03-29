FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim-bookworm

ARG CAMOUFOX_VERSION=135.0.1
ARG CAMOUFOX_RELEASE=beta.24

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    APP_CONDA_ENV=docker \
    DATABASE_URL=sqlite:////app/data/account_manager.db \
    APP_ENABLE_SOLVER=1 \
    SOLVER_PORT=8889 \
    SOLVER_BIND_HOST=0.0.0.0 \
    LOCAL_SOLVER_URL=http://127.0.0.1:8889

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        tini \
        libgtk-3-0 \
        libgdk-pixbuf-2.0-0 \
        libcairo-gobject2 \
        libpangocairo-1.0-0 \
        libxcursor1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY scripts/install_camoufox.py /tmp/install_camoufox.py
RUN pip install -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && CAMOUFOX_VERSION="$CAMOUFOX_VERSION" CAMOUFOX_RELEASE="$CAMOUFOX_RELEASE" python /tmp/install_camoufox.py

COPY . ./
COPY --from=frontend-builder /build/static ./static

RUN mkdir -p /app/data /app/_ext_targets

EXPOSE 8000
VOLUME ["/app/data", "/app/_ext_targets"]

ENTRYPOINT ["tini", "--"]
CMD ["python", "-u", "main.py"]

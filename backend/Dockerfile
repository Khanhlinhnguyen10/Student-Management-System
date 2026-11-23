
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Linux dependencies for pyodbc and ODBC Driver 18.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        g++ \
        unixodbc-dev \
        libgssapi-krb5-2 \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y \
        --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Install existing backend dependencies.
COPY requirements.txt /app/requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    -r /app/requirements.txt

# Copy the backend source code.
COPY . /app

# Runtime command will be configured after
# verifying the existing Flask entry point.

FROM python:3.12.3-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV POETRY_VERSION=1.8.2

WORKDIR /code

# In case where run as non root is true
RUN set -x && \
    addgroup --system --gid 101 app && \
    adduser \
        --system \
        --disabled-login \
        --ingroup app \
        --no-create-home \
        --home /nonexistent \
        --gecos "app user" \
        --shell /bin/false \
        --uid 101 app

# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "poetry==$POETRY_VERSION"

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl=7.88.1-* && \
    rm -rf /var/lib/apt/lists/*

COPY alembic.ini run.py ./
COPY alembic alembic

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

COPY app app

CMD ["python", "run.py"]

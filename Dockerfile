FROM python:3.11.13-slim-bullseye AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.5

COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev


FROM python:3.11.13-slim-bullseye AS prod

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/celery /usr/local/bin/celery

COPY src src

RUN useradd -m admin
USER admin

CMD ["celery", "-A", "src.core.celery_app", "worker", "--loglevel=INFO", "-Q", "sherlock"]

FROM builder AS dev

RUN poetry install

COPY . .

CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "celery", "-A", "src.core.celery_app", "worker", "--loglevel=INFO", "-Q", "sherlock"]
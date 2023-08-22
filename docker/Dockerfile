FROM python:3.11-alpine
WORKDIR /code

COPY ../poetry.lock ../pyproject.toml /code/
RUN    apk add --no-cache curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && POETRY_VIRTUALENVS_CREATE=false /root/.local/bin/poetry install --no-root $(test "$MODE" == production && echo "--no-dev")

COPY ../app /code/app
COPY ../tests /code/tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
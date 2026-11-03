FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --editable .

COPY alembic.ini ./
COPY migrations ./migrations

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown --recursive app:app /app

USER app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "customer_management.main:app", "--host", "0.0.0.0", "--port", "8000"]


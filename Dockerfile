FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY apps ./apps
COPY core ./core
COPY db ./db
RUN pip install --no-cache-dir -e .

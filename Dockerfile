FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY harness/ ./harness/
COPY config.yaml ./
RUN pip install --no-cache-dir .

ENTRYPOINT ["harness"]

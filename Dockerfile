# Dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Stage 2: Runner
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Kích hoạt môi trường ảo
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Lệnh chạy mặc định bằng python, không dùng uv hay make
CMD ["python", "CLI.py", "run", "--env", "production"]

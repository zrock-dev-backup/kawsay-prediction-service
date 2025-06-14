FROM python:3.11-slim AS deps
WORKDIR /app
RUN pip install poetry
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only=main

FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
COPY src/kawsay/ ./src/kawsay/
RUN poetry build --format=wheel

FROM python:3.11-slim AS final
WORKDIR /app
RUN addgroup --system app && adduser --system --group app

COPY --from=deps /app/.venv ./.venv
COPY --from=builder /app/dist/*.whl .
COPY student_pass_predictor.onnx ./
RUN ./.venv/bin/pip install *.whl
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.11/site-packages"

RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "kawsay.main:app", "--host", "0.0.0.0", "--port", "8000"]

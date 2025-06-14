# Dockerfile

# --- Stage 1: Builder ---
# This stage installs dependencies and our application into a virtual environment.
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Configure poetry to create the virtual environment in the project's root
RUN poetry config virtualenvs.in-project true

# Copy dependency definition files
COPY pyproject.toml poetry.lock ./

RUN poetry install --only=main

# Copy the application source code and the model artifact
COPY src/ ./src/
COPY student_pass_predictor.onnx ./


# --- Stage 2: Final Image ---
# This stage creates the lean, production-ready image.
FROM python:3.11-slim as final

WORKDIR /app

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Copy the pre-built virtual environment from the builder stage.
# This now contains all dependencies AND our installed `kawsay` package.
COPY --from=builder /app/.venv ./.venv

# --- FIX 2: Remove redundant source code copy ---
# The source code is already installed in the .venv's site-packages.
# We only need to copy the ONNX model artifact.
COPY --from=builder /app/student_pass_predictor.onnx ./

# Add the virtual environment's bin directory to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Change ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

EXPOSE 8000

# The command now works because `kawsay` is an installed package.
# We still refer to the entrypoint via its file path for uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

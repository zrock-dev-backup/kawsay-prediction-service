# Dockerfile

# --- Stage 1: Builder ---
# This stage installs dependencies into a virtual environment.
FROM python:3.11-slim as builder

# Set the working directory
WORKDIR /app

# Install poetry
# We use pip to install poetry itself into the builder image.
RUN pip install poetry

# Configure poetry to create the virtual environment in the project's root
# This makes it easy to copy the .venv to the next stage.
RUN poetry config virtualenvs.in-project true

# Copy only the files needed to install dependencies
# This leverages Docker's layer caching. The expensive `poetry install`
# step will only re-run if these files change.
COPY pyproject.toml poetry.lock ./

# Install dependencies, excluding development ones.
# --no-root prevents installing the project itself, we only need its dependencies.
RUN poetry install --no-root --only=main

# Copy the application source code and the model artifact
# This layer will be invalidated more often, but the layers above are cached.
COPY src/ ./src/
COPY student_pass_predictor.onnx ./


# --- Stage 2: Final Image ---
# This stage creates the lean, production-ready image.
FROM python:3.11-slim as final

# Set the working directory
WORKDIR /app

# Create a non-root user and group for security
RUN addgroup --system app && adduser --system --group app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application source code and model from the builder stage
COPY --from=builder /app/src ./src
COPY --from=builder /app/student_pass_predictor.onnx ./

# Add the virtual environment's bin directory to the PATH
# This allows us to run `uvicorn` directly without specifying the full path.
ENV PATH="/app/.venv/bin:$PATH"

# Change ownership of the app directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the application runs on
EXPOSE 8000

# Define the command to run the application
# Use 0.0.0.0 to make it accessible outside the container.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

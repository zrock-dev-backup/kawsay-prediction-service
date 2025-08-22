# Default goal for new users.
default: setup

# Zero-config onboarding recipe. Installs the project in editable mode.
setup: install
	@echo "\n✅ Project setup complete."
	@echo "--> Run 'poetry shell' to activate the virtual environment."
	@echo "--> Then you can use other make targets like 'make run-server' or 'make benchmark'."

# Installs dependencies via Poetry and the project itself in editable mode.
install:
	@echo "--- 📦 Installing Python dependencies... ---"
	@poetry install

# Runs the server
run:
	poetry run uvicorn kawsay.main:app --host 0.0.0.0 --port 8000

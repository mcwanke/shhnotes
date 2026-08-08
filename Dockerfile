FROM python:3.14-slim

WORKDIR /app

# Install system dependencies for audio and runtime
RUN apt-get update && apt-get install -y \
    pipewire-alsa \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY shhnotes/ ./shhnotes/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 5444

# Run the API server
CMD ["python", "-m", "uvicorn", "shhnotes.api:app", "--host", "0.0.0.0", "--port", "5444"]

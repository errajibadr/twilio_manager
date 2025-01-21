FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv pip install --system .

# Add the app directory to PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose the port Streamlit runs on
EXPOSE 8484

# Command to run the Streamlit app
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.address", "0.0.0.0", "--server.baseUrlPath", "/twilio-manager", "--server.port", "8484"]
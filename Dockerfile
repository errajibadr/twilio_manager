FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

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

# Healthcheck to ensure the application is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8484/_stcore/health || exit 1

# Command to run the Streamlit app
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.address", "0.0.0.0", "--server.baseUrlPath", "/twilio-manager/", "--server.port", "8484"] 
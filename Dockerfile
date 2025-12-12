FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && \
    apt-get install -y cron && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY config/ ./config/
COPY gmail/ ./gmail/
COPY processor/ ./processor/
COPY utils/ ./utils/
COPY scripts/ ./scripts/

# Install dependencies with uv
RUN uv sync

# Create log directory
RUN mkdir -p /var/log/emailagent

# Copy cron job file
COPY scripts/crontab /etc/cron.d/emailagent-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/emailagent-cron

# Apply cron job
RUN crontab /etc/cron.d/emailagent-cron

# Create entrypoint script
RUN echo '#!/bin/bash\n\
touch /var/log/emailagent/cron.log\n\
cron && tail -F /var/log/emailagent/cron.log' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run the command on container startup
CMD ["/entrypoint.sh"]

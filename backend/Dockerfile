FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies, uv, and tzdata
RUN apt-get update && \
    apt-get install -y cron tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

# Set timezone properly (ENV alone doesn't work for cron daemon)
ENV TZ=America/Los_Angeles
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY config/ ./config/
COPY db/ ./db/
COPY gmail/ ./gmail/
COPY processor/ ./processor/
COPY sources/ ./sources/
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

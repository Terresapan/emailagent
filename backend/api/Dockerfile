FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies including docker SDK
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    sqlalchemy==2.0.35 \
    psycopg2-binary==2.9.9 \
    pydantic==2.9.2 \
    docker==7.1.0

# Copy API code
COPY . .

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

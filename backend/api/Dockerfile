FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies including docker SDK and requests for Google Trends API
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn==0.30.6 \
    sqlalchemy==2.0.35 \
    psycopg2-binary==2.9.9 \
    pydantic==2.9.2 \
    docker==7.1.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    google-api-python-client==2.111.0 \
    google-auth-oauthlib==1.2.0 \
    google-auth-httplib2==0.2.0 \
    pytrends==4.9.2 \
    tenacity==8.2.3 \
    markdown==3.5.2 \
    justhtml

# Copy API code
COPY . .

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

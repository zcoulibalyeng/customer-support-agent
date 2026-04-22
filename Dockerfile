FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .


# Copy and prepare the entrypoint script
COPY entrypoint.sh /usr/local/bin/

# Initialise database and knowledge base at build time
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

# Use the entrypoint to handle initialization
ENTRYPOINT ["entrypoint.sh"]

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile

# Use an official Python image as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set the working directory
WORKDIR /app

# Install system dependencies and PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment and install dependencies
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project into the container
COPY . /app/

# Copy and use entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose the port Django will run on
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:$PORT agilemetrics.wsgi:application"]
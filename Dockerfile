# Dockerfile

# Use an official Python image as the base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies and PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project into the container
COPY . /app/

# Expose the port Django will run on
EXPOSE 8000

# Add this line after copying your code
#COPY entrypoint.sh /app/

# Run migrations and start the server
#ENTRYPOINT ["/app/entrypoint.sh"]
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "agilemetrics.wsgi:application"]
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
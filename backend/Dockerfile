# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Prevent Python from writing .pyc files to disc and force stdio unbuffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
# libsndfile1 is needed for the 'soundfile' Python package for audio processing
# Update package lists and install libsndfile1, then clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your backend application code into the container
# Ensure that your schemas, services, core, api, and main.py are within the backend/app structure
COPY ./backend /app/backend

# The port your app will run on inside the container.
# Gunicorn will bind to this, and Render will map its internal port to this.
ENV PORT 8000
EXPOSE 8000

# Command to run your application using Gunicorn with Uvicorn workers
# This will be the default command if not overridden by the PaaS start command.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend.app.main:app", "--bind", "0.0.0.0:$PORT"]
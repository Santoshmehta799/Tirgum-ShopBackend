# Use the official Python image from Docker Hub
FROM python:3.11.4-slim-bookworm

# Set the working directory to /app
WORKDIR /app

# Install system dependencies required for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libcairo2 \
    libpangocairo-1.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements.txt file to leverage Docker caching
COPY requirements.txt /app/

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose the port that your application is running on
EXPOSE 8000

# Specify the command to run your application with the --reload option
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--reload", "--workers", "4", "--capture-output"]

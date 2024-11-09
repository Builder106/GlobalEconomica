# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update && apt-get install -y yarn

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install the dependencies and capture detailed logs
RUN pip install --no-cache-dir -r requirements.txt || \
    { echo "pip install failed"; cat /root/.pip/pip.log; exit 1; }

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8050

# Run the application
CMD ["python", "app.py"]
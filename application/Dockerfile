# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install PostgreSQL client tools (including pg_isready)
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /application

# Copy the current directory contents into the container at /application
COPY . /application

# Make sure the wait-for-db.sh script is executable
RUN chmod +x /application/wait-for-db.sh

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/application

# Run the wait-for-db.sh script and then the application
ENTRYPOINT ["/application/wait-for-db.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
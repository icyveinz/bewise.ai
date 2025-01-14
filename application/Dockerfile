# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /application

# Copy the current directory contents into the container at /app
COPY . /application

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/application

# Run the myapi application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
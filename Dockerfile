# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Command to run the application
CMD ["gunicorn", "run:app", "-w", "4", "-b", ":8080"]

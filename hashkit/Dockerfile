# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a dedicated directory for writable data and set it as the working directory
RUN mkdir /app/data && chmod 777 /app/data
WORKDIR /app/data

# Copy the application code into the new working directory
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Set the command to run the Flask application
CMD ["python", "app.py"]

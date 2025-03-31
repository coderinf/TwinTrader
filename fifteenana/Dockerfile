# Use an official Python image as a base
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY . .

# Make the script executable
RUN chmod +x scr.py

# Run the script when the container starts
CMD ["python", "scr.py"]
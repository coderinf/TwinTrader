# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the command to start the application when the container launches
CMD ["python", "pricetracker.py"]
# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the script and other necessary files to the container
COPY update/app.py /app/

# Install the required Python packages
RUN pip install requests pytest-playwright
RUN playwright install

# Expose the port on which the Flask app will run
EXPOSE 80

CMD ["python", "app.py"]

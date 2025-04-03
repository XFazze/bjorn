# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /app

# Install required packages for the web app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# If requirements.txt doesn't exist, uncomment these lines
# RUN pip3 install flask pandas plotly

# Copy web app files
COPY . .

# Make sure static directory exists
RUN mkdir -p static/css

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Command to run the application
CMD ["flask", "run"]

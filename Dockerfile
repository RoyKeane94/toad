# 1. Use an official, slim Python image
# Using a specific version is better for reproducibility
FROM python:3.11-slim-bullseye

# 2. Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory
WORKDIR /app

# 4. Install dependencies
# This is done in a separate step to take advantage of Docker's caching.
# The requirements are only re-installed if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# The port the container will listen on.
# Gunicorn will bind to the $PORT environment variable provided by Railway automatically.
EXPOSE 8000

# The Procfile will override this, but it's good practice to have it.
# This command is not strictly necessary if you have a Procfile.
CMD ["gunicorn", "toad.wsgi"]
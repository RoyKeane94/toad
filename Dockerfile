# 1. Use an official, slim Python image
# Using a specific version is better for reproducibility
FROM python:3.11-slim-bullseye

# 2. Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Install Node.js and npm for Tailwind CSS build
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Install dependencies
# This is done in a separate step to take advantage of Docker's caching.
# The requirements are only re-installed if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your application code
COPY . .

# 7. Build Tailwind CSS
# This generates the final CSS file (e.g., master.css) from your sources.
RUN python manage.py tailwind build

# 8. Collect static files
# This runs the collectstatic command to gather all static files into STATIC_ROOT.
# The --noinput flag prevents any interactive prompts.
RUN python3 manage.py collectstatic --noinput

# The port the container will listen on.
# Gunicorn will bind to the $PORT environment variable provided by Railway automatically.
EXPOSE 8000

# The Procfile will override this, but it's good practice to have it.
# This command is not strictly necessary if you have a Procfile.
CMD ["gunicorn", "toad.wsgi"]
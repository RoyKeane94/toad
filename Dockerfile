# 1. Use an official, slim Python image
# Using a specific version is better for reproducibility
FROM python:3.11-slim-bullseye

# 2. Set environment variables
# Prevents Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Install Node.js and npm from NodeSource
RUN apt-get update \
    && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Install dependencies
# This is done in a separate step to take advantage of Docker's caching.
# The requirements are only re-installed if requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy package.json and postcss.config.js for better caching
COPY package.json .
COPY postcss.config.js .

# 7. Install Node.js dependencies
RUN npm install

# 8. Copy the rest of your application code
COPY . .

# 9. Build CSS and JS assets
RUN npm run build:all

# The port the container will listen on.
# Gunicorn will bind to the $PORT environment variable provided by Railway automatically.
EXPOSE 8000

# The Procfile will override this, but it's good practice to have it.
# This command is not strictly necessary if you have a Procfile.
CMD ["gunicorn", "toad.wsgi"]
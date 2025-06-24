# 1. Use an official, slim Python image
FROM python:3.11-slim-bullseye

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install Node.js and npm
RUN apt-get update \
    && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory
WORKDIR /app

# 5. Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 6. Set Node.js memory limit to prevent OOM errors
ENV NODE_OPTIONS=--max-old-space-size=2048

# 7. Install Node.js dependencies
COPY package*.json ./
COPY postcss.config.js ./
RUN npm ci

# 8. Copy the rest of your application code
COPY . .

# 9. Build static assets (CSS and JS)
RUN npm run build:all

# 10. Set the environment variable to ensure collectstatic runs in production mode
ENV DJANGO_DEBUG_ENVIRONMENT=1

# 11. Collect static files, ignoring ALL source CSS files.
RUN python3 manage.py collectstatic --no-input --clear --ignore input.css --ignore master-dev.css --ignore master.css

# 12. Expose the port. Gunicorn will bind to the $PORT environment variable.
EXPOSE 8000

# 13. The command to run the application.
CMD ["gunicorn", "toad.wsgi"]
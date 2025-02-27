FROM python:3.10-slim

# Set the timezone if needed
ENV TZ=Asia/Kolkata

# Install necessary packages: ffmpeg, git, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create the working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Command to run the bot
CMD ["python", "magic.py"]

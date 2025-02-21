# cookiebot - tg-ytdlp-bot

Support me on [BuyMeACoffee](https://buymeacoffee.com/upekshaip)

Download private YouTube/videos using a cookie file.

## Full documentation available on  
[https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU](https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU)

## Deploy on VM

- First, you need to add your bot to the **logging channel** and **subscription channel**. Both are required.
- Give me a star and fork this repository. Then change the **_config.py** file to **config.py**.
- Add your configuration for the **config.py** file.

#### Setup debian/any for docker

- ```sh
  sudo apt-get update
  ```
- ```sh
  sudo apt -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common
  ```
- ```sh
  curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  ```
- ```sh
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
  ```
- ```sh
  sudo apt update
  ```
- ```sh
  sudo apt install -y docker-ce docker-ce-cli containerd.io
  ```
- ```sh
  docker -v
  ```

#### Installing ffmpeg in the System

It is essential to have **ffmpeg** installed on your system because **yt-dlp** relies on it for merging streams (and in some cases, for transcoding or extracting thumbnails). To install ffmpeg on a Debian-based system, run:

- ```sh
  sudo apt-get update
  ```
- ```sh
  sudo apt-get install -y ffmpeg
  ```
- Verify installation:
- ```sh
  ffmpeg -version
  ```

#### Making ffmpeg Available in Docker

If you are deploying via Docker, ensure that ffmpeg is included in your Docker image. One simple way is to modify the Dockerfile to install ffmpeg during the build process. For example, add the following lines in your Dockerfile before copying the bot’s files:

```dockerfile
FROM python:3.9-slim

# Install dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the bot
CMD ["python", "your_bot_file.py"]
```

This way, the built Docker image will include ffmpeg and your bot will be able to use it.

#### Setting the config.py file

- ```sh
  git clone https://github.com/upekshaip/tg-ytdlp-bot.git
  ```
- ```sh
  cd tg-ytdlp-bot
  ```
- ```sh
  sudo mv _config.py config.py
  ```
- ```sh
  nano config.py
  ```
- Now you can edit your config before the deployment.
- After your edit process, please follow the steps below.

#### Install Dockerfile

- ```sh
  sudo docker build . -t tg-public-bot
  ```
- ```sh
  sudo docker ps -a
  ```
- ```sh
  sudo docker run tg-public-bot
  ```

### Additions

- Added a Config object for configurations.
- Can add a custom name for a playlist. The 1st video will start as "bla bla - Part 1" and so on.  
  You can specify a range if you need a custom name like -> (https://blabla.blaa*1*3*name)
- No need to specify a range if there is only one video. Simply provide the URL (https://blabla.blaa).
- If you provide only a playlist URL, the bot will download the first video of that playlist.
- If you want to download a range of videos, specify a range like -> (https://blabla.blaa*1*3)

### User Commands

- `/check_cookie` - Check cookie file
- `/help` - Help message
- `/start` - Start the bot
- `/clean` - Clean your working directory
- `/usage` - See your usage

### Admin Commands

- `start` - Start the bot
- `help` - Send help text
- `run_time` - Show bot runtime
- `log` - Get user logs (e.g., `/log 10101010`)
- `broadcast` - Send a message to all users (reply to any message with this command to broadcast it)
- `clean` - Clean your working directory
- `usage` - Get all logs
- `check_cookie` - Check cookie file
- `save_as_cookie` - Save text as cookie (save text as cookie)
- `download_cookie` - Download the cookie file
- `format` - Choose media format options
- `block_user` - Block a user (e.g., `/block_user 10101010`)
- `unblock_user` - Unblock a user (e.g., `/unblock_user 10101010`)
- `all_users` - Get all users
- `all_blocked` - Get all blocked users
- `all_unblocked` - Get all unblocked users

#### Link Command Pattern Spec (Just send the link)

https://blabla.blaa

- Download video with the real name.
- Download only the 1st video of the playlist.

https://blabla.blaa*1*3

- Download the given range of the playlist with the real name.

https://blabla.blaa*1*3*name

- Download the given range of the playlist with a custom name.  
  Video names will be like:
  - "name - Part 1"
  - "name - Part 2"

## Added New Features

- Added cookie download feature for each user.
- Added per-user database.

## TODO:

- Need to add a custom formatter selector for download.
- Need to add mp3 support.
- Need to add Google Drive support to store files.

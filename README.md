# cookiebot - tg-ytdlp-bot

Support me on [BuyMeACoffee](https://buymeacoffee.com/upekshaip)

Download private YouTube/videos using a cookie file.

## Full documentation available
[https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU](https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU)

---

## Deploy on a VM

- First, you need to add your bot to the **logging channel** and **subscription channel**. Both are required.
- Give this repository a star and fork it. Then rename the file **_config.py** to **config.py**.
- Add your configuration to the **config.py** file.

### Setup Debian/Any for Docker

1. ```sh
   sudo apt-get update
   ```
2. ```sh
   sudo apt -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common
   ```
3. ```sh
   curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```
4. ```sh
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
   https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
   | sudo tee /etc/apt/sources.list.d/docker.list
   ```
5. ```sh
   sudo apt update
   ```
6. ```sh
   sudo apt install -y docker-ce docker-ce-cli containerd.io
   ```
7. ```sh
   docker -v
   ```

---

### Installing ffmpeg in the System

It is essential to have **ffmpeg** installed on your system because **yt-dlp** relies on it for merging streams (and in some cases, for transcoding or extracting thumbnails). To install ffmpeg on a Debian-based system, run:

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Verify installation:
```sh
ffmpeg -version
```

---

#### Setting up `config.py`

```sh
git clone https://github.com/upekshaip/tg-ytdlp-bot.git
cd tg-ytdlp-bot
sudo mv _config.py config.py
nano config.py
```
Edit your config before deployment. After your edits, proceed with Docker build steps below.

---

### Preparing `yt-dlp` for `/cookies_from_browser`

To use the `/cookies_from_browser` command (which extracts cookies from installed browsers on your server), you need to have the `yt-dlp` binary properly set up. Follow these steps:

1. **Download `yt-dlp`**  
   Go to the [official `yt-dlp` releases page](https://github.com/yt-dlp/yt-dlp/releases) and download the binary for your CPU architecture (e.g., `yt-dlp_x86_64`, `yt-dlp_arm`, etc.).
   Place this binary executable to `tg-ytdlp-bot` project folder.
 
2. **Rename and make it executable**  
   ```bash
   mv yt-dlp_linux yt-dlp
   chmod +x yt-dlp
   ```

3. **Create a symbolic link**  
   So that `yt-dlp` can be run from any directory without specifying the full path, create a symlink (for example, in `/usr/local/bin`):
   ```bash
   sudo ln -s /full/path/to/tg-ytdlp-bot/yt-dlp /usr/local/bin/yt-dlp
   ```
   Make sure `/usr/local/bin` is in your `PATH`. Now you can invoke `yt-dlp` directly.

---

#### Building and Running with Docker

```sh
sudo docker build . -t tg-public-bot
sudo docker ps -a
sudo docker run tg-public-bot
```

---

### Additions

- Added a `Config` object for configurations.
- Added the ability to set a custom name for a playlist. The 1st video will start as "bla bla - Part 1" and so on.  
- You can specify a range if you need a custom name like `https://blabla.blaa*1*3*name`.
- No need to specify a range if there is only one video. Just provide the URL, e.g. `https://blabla.blaa`.
- If you provide only a playlist URL, the bot will download the first video of that playlist.
- If you want to download a range of videos, specify a range like `https://blabla.blaa*1*3`.

---

## User Commands

- `/check_cookie` - Check cookie file
- `/cookies_from_browser` - **Get cookies from browser**  
- `/help` - Help message
- `/start` - Start the bot
- `/clean` - Clean your working directory
- `/usage` - See your usage

## Admin Commands

- `start` - Start the bot
- `help` - Send help text
- `run_time` - Show bot runtime
- `log` - Get user logs (e.g., `/log 10101010`)
- `broadcast` - Send a message to all users (reply to any message with this command to broadcast it)
- `clean` - Clean your working directory
- `usage` - Get all logs
- `check_cookie` - Check cookie file
- `save_as_cookie` - Save text as cookie
- `download_cookie` - Download the cookie file
- `cookies_from_browser` - Get cookies from browser
- `format` - Choose media format options
- `block_user` - Block a user (e.g., `/block_user 10101010`)
- `unblock_user` - Unblock a user (e.g., `/unblock_user 10101010`)
- `all_users` - Get all users
- `all_blocked` - Get all blocked users
- `all_unblocked` - Get all unblocked users

### Link Command Pattern Spec (Just send the link)

- **`https://blabla.blaa`**  
  Download the video with the real name.  
  Download only the 1st video of the playlist (if it's a playlist).

- **`https://blabla.blaa*1*3`**  
  Download the specified range of the playlist with the real name.

- **`https://blabla.blaa*1*3*name`**  
  Download the specified range of the playlist with a custom name.  
  Video names will be like:
  - `name - Part 1`
  - `name - Part 2`

---

## Added New Features

- Added cookie download feature for each user.
- Added a per-user database.

## TODO

- Add a custom formatter selector for download.
- Add MP3 support.
- Add Google Drive support to store files.


# cookiebot - tg-ytdlp-bot

Support me on [BuyMeACoffee](https://buymeacoffee.com/upekshaip)

Download private YouTube/videos using a cookie file.

## Full Documentation
[https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU](https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU)

---

## Deploy on a VM

- First, add your bot to the **logging channel** and **subscription channel**. Both are required.
- Star and fork this repository. Then rename the file **_config.py** to **config.py**.
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

### Installing ffmpeg

**ffmpeg** is essential since **yt-dlp** relies on it for merging streams (and in some cases for transcoding or extracting thumbnails). To install ffmpeg on a Debian-based system, run:

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg
```

Verify the installation:
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

Edit your configuration before deployment. After your edits, proceed with the Docker build steps below.

---

### Preparing `yt-dlp` for `/cookies_from_browser`

To use the `/cookies_from_browser` command (which extracts cookies from installed browsers on your server), ensure that the **yt-dlp** binary is set up properly:

1. **Download `yt-dlp`**  
   Visit the [official `yt-dlp` releases page](https://github.com/yt-dlp/yt-dlp/releases) and download the binary for your CPU architecture (e.g., `yt-dlp_x86_64`, `yt-dlp_arm`, etc.).  
   Place the binary executable in the `tg-ytdlp-bot` project folder.
 
2. **Rename and make it executable**  
   ```bash
   mv yt-dlp_linux yt-dlp
   chmod +x yt-dlp
   ```

3. **Create a symbolic link**  
   Create a symlink so that `yt-dlp` can be run from any directory (for example, in `/usr/local/bin`):
   ```bash
   sudo ln -s /full/path/to/tg-ytdlp-bot/yt-dlp /usr/local/bin/yt-dlp
   ```
   Ensure `/usr/local/bin` is in your `PATH`. Now you can run `yt-dlp` directly.

---

#### Building and Running with Docker

```sh
sudo docker build . -t tg-public-bot
sudo docker ps -a
sudo docker run tg-public-bot
```

---

## New Commands and Features

### /audio Command

The **/audio** command downloads audio from a given video URL. It extracts the best available audio track, converts it to MP3, and sends the audio file to the user. After sending, the downloaded file is removed to prevent disk clutter.

Usage example:
```
/audio https://youtu.be/dQw4w9WgXcQ?si=Vqh0HJVNn_99bhj4
```

---

### /format Command

The **/format** command allows users to set a custom download format for their videos. Users can either supply a custom format string or choose from a preset menu.

**Main Menu Options:**
- 💻<=4k (best for desktop TG app)
- 📱<=FullHD (best for mobile TG app)
- 📈bestvideo+bestaudio (MAX quality)
- 📉best (no ffmpeg)
- **Others** – opens a full resolution menu (see below)
- 🎚 custom – for entering a custom format string
- 🔙 Cancel – cancels the selection

**Full Resolution Menu (triggered by "Others"):**
- 144p (256×144)
- 240p (426×240)
- 360p (640×360)
- 480p (854×480)
- 720p (1280×720)
- 1080p (1920×1080)
- 1440p (2560×1440)
- 2160p (3840×2160)
- 4320p (7680×4320)
- A **Back** button returns to the main menu.

Usage example:
```
/format
```
Then select the desired option from the menu.

---

## User Commands

- **/check_cookie** - Check the cookie file.
- **/cookies_from_browser** - Get cookies from your browser.
- **/help** - Display help message.
- **/start** - Start the bot.
- **/clean** - Clean your working directory.
- **/usage** - Show your usage statistics.
- **/audio** - Download audio from a video URL.
- **/format** - Choose media format options.

## Admin Commands

- **start** - Start the bot.
- **help** - Send help text.
- **run_time** - Show bot runtime.
- **log** - Get user logs (e.g., `/log 10101010`).
- **broadcast** - Broadcast a message to all users (reply to any message with this command).
- **clean** - Clean the working directory.
- **usage** - Get all logs.
- **check_cookie** - Check the cookie file.
- **save_as_cookie** - Save text as cookie.
- **download_cookie** - Download the cookie file.
- **cookies_from_browser** - Get cookies from your browser.
- **format** - Choose media format options.
- **block_user** - Block a user (e.g., `/block_user 10101010`).
- **unblock_user** - Unblock a user (e.g., `/unblock_user 10101010`).
- **all_users** - Get all users.
- **all_blocked** - Get all blocked users.
- **all_unblocked** - Get all unblocked users.

---

## Link Command Pattern Spec

- **`https://blabla.blaa`**  
  Download the video with its original name.  
  If it is a playlist, only the first video is downloaded.

- **`https://blabla.blaa*1*3`**  
  Download a specified range of videos from the playlist with their original names.

- **`https://blabla.blaa*1*3*name`**  
  Download a specified range of videos from the playlist with a custom name.  
  Videos will be named as:
  - `name - Part 1`
  - `name - Part 2`

---

## Added New Features

- Per-user cookie download.
- Per-user database.
- Custom playlist naming.
- MP3 audio download support (/audio command).

---

## Auto-Cleaning User Directories with Crontab

To prevent your server from filling up with downloaded files, you can set up a crontab task that runs every 24 hours and deletes all files in user directories (except for `cookie.txt` and `logs.txt`).

For example, add the following line to your crontab:

```bash
0 0 * * * /usr/bin/find /root/Telegram/tg-ytdlp-bot/users -type f ! -name "cookie.txt" ! -name "logs.txt" -delete
```

**Explanation:**
- `0 0 * * *` – Executes the command every day at midnight.
- `/usr/bin/find /CHANGE/ME/TO/REAL/PATH/TO/tg-ytdlp-bot/users -type f` – Searches for all files under the users directory.
- `! -name "cookie.txt" ! -name "logs.txt"` – Excludes `cookie.txt` and `logs.txt` files from deletion.
- `-delete` – Deletes the files found.

---

## TODO

- Add a custom formatter selector for downloads.
- Enhance MP3 support.
- Add Google Drive support to store files.
```


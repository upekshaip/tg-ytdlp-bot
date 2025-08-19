# cookiebot - tg-ytdlp-bot

Support me on [BuyMeACoffee](https://buymeacoffee.com/upekshaip) \
Thanks to Contributor - [@IIlIlIlIIIlllIIlIIlIllIIllIlIIIl](https://t.me/IIlIlIlIIIlllIIlIIlIllIIllIlIIIl) - [chelaxian](https://github.com/chelaxian/tg-ytdlp-bot)

Download private YouTube/videos using a cookie file.

Test free bot - https://t.me/tgytdlp_bot

## Full Documentation
[https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU](https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU)

---

## Deploy on a VM in a Docker container

- First, add your bot to the **logging channel** and **subscription channel**. Both are required.
- Star and fork this repository. Then rename the file **_config.py** to **config.py**.
- Add your configuration to the **config.py** file.

### Setup Debian for Docker

[Install Docker Engine
](https://docs.docker.com/engine/install/)
---

#### Setting up `config.py` (example for Ubuntu/Debian)

```sh
sudo apt update
sudo apt install git
```

```sh
git clone https://github.com/upekshaip/tg-ytdlp-bot.git
cd tg-ytdlp-bot
sudo mv _config.py config.py
nano config.py
```

Edit your configuration before deployment. After your edits, proceed with the Docker build steps below.

---

#### Get YouTube cookies

YouTube rotates account cookies frequently on open YouTube browser tabs as a security measure. To export cookies that will remain working with yt-dlp, you will need to export cookies in such a way that they are never rotated.

One way to do this is through a private browsing/incognito window:

- Open a new private browsing/incognito window and log into YouTube
- Open a new tab and close the YouTube tab
- Export youtube.com cookies from the browser then close the private browsing/incognito window so the session is never opened in the browser again.

For export you can use browser extension [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)

create in project folder subfolder `cookies` and place `cookie.txt` extracted from YouTube here

```sh
cd tg-ytdlp-bot
mkdir cookies
nano cookie.txt
```
---

#### Building and Running with Docker

```sh
sudo docker build . -t tg-public-bot
sudo docker ps -a
sudo docker run tg-public-bot
```

(optional) If you want to use `/cookies_from_browser` command, after docker deployment you need to enter your docker CMD and install desktop environment (GUI) and Browser into your docker container.
Also you will need download `yt-dlp` binary into your Docker container. See [(Optional) Preparing `yt-dlp` for `/cookies_from_browser`](#optional-preparing-yt-dlp-for-cookies_from_browser)

---

## Alternative local deployment on a VM (without Docker container)

If you prefer local deployment rather than docker container, you should use this commands:

#### Install `git` and `python3` (example for Ubuntu/Debian)
```sh
sudo apt update
sudo apt install git python3.10 python3-pip python3.10-venv
```
#### Setting up `config.py`
```sh
git clone https://github.com/upekshaip/tg-ytdlp-bot.git
cd tg-ytdlp-bot
sudo mv _config.py config.py
nano config.py
```
Edit your configuration before deployment.

#### Install `python` modules

```sh
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
pip uninstall urllib3 -y
pip install --no-cache-dir --force-reinstall "urllib3==1.26.20"
pip install --no-deps moviepy==1.0.3
python3 magic.py
```
---
### (Optional) Installing ffmpeg (example for Ubuntu/Debian)
<details>
  <summary>spoiler</summary> 
      
   If you prefer local deployment rather that docker container you also need to install `ffmpeg`
   **ffmpeg** is essential since **yt-dlp** relies on it for merging streams (and in some cases for transcoding or extracting thumbnails). To install ffmpeg on a Debian-based system, run:

   ```sh
   sudo apt-get update
   sudo apt-get install -y ffmpeg
   ```

   Verify the installation:
   ```sh
   ffmpeg -version
   ```

   If you need to support extra languages such as arabic, chinese, japanese, korean - you also need to install this language packs:
   ```sh
   sudo apt update
   sudo add-apt-repository universe
   sudo apt update

   sudo apt install fonts-noto-core             # – Noto Sans, Noto Serif, … base fonts Google Noto
   sudo apt install fonts-noto-extra            # – extra fonts (including arabic)
   sudo apt install fonts-kacst fonts-kacst-one # – KACST arabic fonts
   sudo apt install fonts-noto-cjk              # – Chinese-Japanese-Korean characters
   ```

   For Amiri arabic:
   ```sh
   git clone https://github.com/aliftype/amiri.git
   sudo mkdir -p /usr/share/fonts/truetype/amiri
   sudo cp amiri/fonts/*.ttf /usr/share/fonts/truetype/amiri/
   ```
   
   Update font cache
   ```sh
   sudo fc-cache -fv
   fc-list | grep -i amiri
   ```
</details> 

---
### (Optional) Preparing `yt-dlp` for `/cookies_from_browser`
<details>
   <summary>spoiler</summary> 

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

   (Also in that case you must install desktop environment (GUI) and any supported by `yt-dlp` browser by yourself)

</details>

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
- ❓ Always Ask (menu + buttons)
- **🎛 Others (144p - 4320p)** – opens a full resolution menu (see below)
- 💻4k (best for PC/Mac Telegram)
- 📱FullHD (best for mobile Telegram)
- 📈bestvideo+bestaudio (MAX quality)
- **🎚 Custom (enter your own)** – for entering a custom format string
- 🔙 Close – cancels the selection

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

- **/start** - Start the bot.
- **/help** - Display help message.
- **/settings** - Open settings menu with categories and quick actions.
- **/clean** - Clean your working directory or specific files (see /help).
- **/usage** - Show your usage statistics and logs.
- **/tags** - Get all your #tags.
- **/audio** - Download audio from a video URL.
- **/format** - Choose media format options.
- **/split** - Change splitted video part size (0.25-2GB).
- **/mediainfo** - Turn ON/OFF sending mediainfo.
- **/check_cookie** - Check the cookie file.
- **/download_cookie** - Download the cookie file.
- **/save_as_cookie** - Save text as cookie (or upload TXT-doc).
- **/cookies_from_browser** - Get cookies from browser (if supported).
- **/subs** - Enable/disable subtitle embedding for videos.


## Admin Commands

- **/start** - Start the bot.
- **/help** - Send help text.
- **/run_time** - Show bot runtime.
- **/log** - Get user logs (e.g., `/log 10101010`).
- **/broadcast** - Broadcast a message to all users (reply to any message with this command).
- **/clean** - Clean the working directory.
- **/usage** - Get all logs.
- **/check_cookie** - Check the cookie file.
- **/save_as_cookie** - Save text as cookie.
- **/download_cookie** - Download the cookie file.
- **/cookies_from_browser** - Get cookies from your browser.
- **/format** - Choose media format options.
- **/block_user** - Block a user (e.g., `/block_user 10101010`).
- **/unblock_user** - Unblock a user (e.g., `/unblock_user 10101010`).
- **/all_users** - Get all users.
- **/all_blocked** - Get all blocked users.
- **/all_unblocked** - Get all unblocked users.
- **/uncache** - Clear cached subtitle language data.
- **/reload_cache** - Reload cache from firebase to local json file
- **/auto_cache** - Toggle turn ON/OFF mode of auto reloading of cache every N hours. 
---

## Settings Menu (`/settings`)

The `/settings` command opens an interactive menu with three categories:

- **🍪 COOKIES**
- **🎞 MEDIA**
- **📖 LOGS**

Each category contains quick action buttons for the most important commands. Example (COOKIES section):

```
🧹 /clean             - Delete cookies & broken media files
📥 /download_cookie   - Download my YouTube cookie
🌐 /cookies_from_browser - Get cookies from browser
🔎 /check_cookie      - Check cookie file in your folder
🔖 /save_as_cookie    - Send text to save as cookie
```

- Pressing a button instantly runs the corresponding command (not just sends text).
- Some buttons (like /audio, /save_as_cookie) show usage hints.
- The menu is fully localized and does not conflict with other inline menus.

---

## Link Command Pattern Spec

- **`https://blabla.blaa`** \
  Download the video with its original name. \
  If it is a playlist, only the first video is downloaded. 

- **`https://blabla.blaa*1*3`**  \
  Download a specified range of videos from the playlist with their original names. 

- **`https://blabla.blaa*1*3*name`**  \
  Download a specified range of videos from the playlist with a custom name. \
  Videos will be named as: 
  - `name - Part 1` 
  - `name - Part 2` 

---

## Tags System (Navigation Tags)

You can add tags to any link (video, playlist, audio) directly in your message:

- Format: `https://site.com/link#tag1#tag2#my_tag`
- Tags must start with `#` and contain only letters, digits, and underscore (`_`).
- Tags are automatically added to the caption of the video/audio, separated by spaces.
- All unique tags you send are saved in the `tags.txt` file in your user folder.

### Example of using tags:
```
https://youtu.be/STeeOaX2FBs?si=5rz1QhvuiauZ7A4d#youtube#mytag#tag123
```
The video caption will include:
```
#youtube #mytag #tag123
```

---

### /tags Command

The `/tags` command lets you get a list of all your unique tags (one per line). If the list is long, the bot will send several messages.

**Example:**
```
/tags
```
Response:
```
#youtube
#mytag
#tag123
...
```
---

## Help

**This bot allows you to download videos and audio, and also work with playlists.**

• Simply send a video link and the bot will start downloading. \
• For playlists, specify the range of indexes separated by asterisks (e.g. `https://example.com*1*4`) to download videos from position 1 to 4. \
• You can set a custom playlist name by adding it after the range (e.g. `https://example.com*1*4*My Playlist`). 

• To change the caption of a video, reply to the video with your message – the bot will send the video with your caption. \
• To extract audio from a video, use the **/audio** command (e.g. `/audio https://example.com`). \
• Upload a cookie file to download private videos and playlists. \
• Check or update your cookie file with **/check_cookie**, **/download_cookie**, **/save_as_cookie** and **/cookies_from_browser** commands. \
• To clean your workspace on server from bad files (e.g. old cookies or media) use **/clean** command (might be helpfull for get rid of errors). \
• See your usage statistics and logs by sending the **/usage** command. \
• Control subtitle embedding with **/subs** command - enable or disable automatic subtitle burning into videos. \
• Clear cached subtitle language data with **/uncache** command if you experience issues with subtitle detection. \
• Reload cache from firebase to local json file with **/reload_cache** command. \
• Toggle turn ON/OFF mode of auto reloading of cache every **N** hours with **/auto_cache** command. 

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

- ~~Add a custom formatter selector for downloads.~~
- ~~Enhance MP3 support.~~
- Add Google Drive support to store files.

---

Below is an example section for your GitHub README.md that explains how to set up Firebase for your Telegram bot, including creating a Firebase project, setting up a Realtime Database with authentication, and creating a user.

---

## Firebase Setup for Telegram Bot

This section describes how to create a Firebase project, set up the Realtime Database with authentication, create a test user, and integrate Firebase into your Telegram bot.

### 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/) and click **Add Project** (or select an existing project).
2. Follow the setup wizard to create your new project.
3. After the project is created, navigate to **Project Settings** and copy your configuration parameters (such as `apiKey`, `authDomain`, `databaseURL`, `projectId`, etc.). These values are required for configuring the connection in your bot.

### 2. Create a Realtime Database

1. In the Firebase Console, select **Realtime Database**.
2. Click **Create Database**.
3. Choose your database location and set the mode. For initial testing, you may choose **Test Mode** (keep in mind that test mode does not enforce authentication).
4. Once your database is created, update its security rules as described in Step 4.

### 3. Enable Authentication

1. In the left-hand menu of the Firebase Console, select **Authentication**.
2. Click **Get Started**.
3. Navigate to the **Sign-in Method** tab and enable the desired provider. For a basic setup, enable **Email/Password**:
   - Click on **Email/Password**.
   - Toggle the switch to **Enable**.
4. After enabling the sign-in method, create a test user manually in the **Users** tab, or implement user registration in your application.

### 4. Update Realtime Database Security Rules

To restrict access to your database only to authenticated users, update your security rules as follows:

```json
{
  "rules": {
    // Allow access only to authenticated user with certain email
    ".read":  "auth != null && auth.token.email === 'YOUREMAIL@gmail.com'",
    ".write": "auth != null && auth.token.email === 'YOUREMAIL@gmail.com'"
  }
}
```

These rules allow read and write operations only if the request contains a valid `idToken`—meaning the user is authenticated.

### 5. Autostart service

To create auto-start service for this bot - copy text from this file https://github.com/chelaxian/tg-ytdlp-bot/blob/main/etc/systemd/system/tg-ytdlp-bot.service and paste it to 
```bash
/etc/systemd/system/tg-ytdlp-bot.service
```
do not forget to change path in service to yoyr actual path

reload systemctl and enable/start service
```bash
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable tg-ytdlp-bot.service
systemctl restart tg-ytdlp-bot.service
journalctl -u tg-ytdlp-bot -f
```

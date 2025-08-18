# tg-ytdlp-bot (supports your own cookies)

Support me on [BuyMeACoffee](https://buymeacoffee.com/upekshaip) \
Thanks to Contributor - [@IIlIlIlIIIlllIIlIIlIllIIllIlIIIl](https://t.me/IIlIlIlIIIlllIIlIIlIllIIllIlIIIl) - [chelaxian](https://github.com/chelaxian/tg-ytdlp-bot)

Download private YouTube/videos using a cookie file.

Test free Telegram bots - https://t.me/tg_ytdlp \
https://t.me/tgytdlp_uae_bot \
https://t.me/tgytdlp_uk_bot \
https://t.me/tgytdlp_fr_bot \
https://t.me/tgytdlp_bot

## Full Documentation
[https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU](https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU)

---

## Deploy on a VM 

- First, add your bot to the **logging channel** and **subscription channel**. Both are required.
- Star and fork this repository. Then rename the file **_config.py** to **config.py**.
- Add your configuration to the **config.py** file.
- Install required dependencies and start the bot.

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
cd tg-ytdlp-bot/TXT
nano cookie.txt
```
---

##  local deployment on a VM 
For local deployment you should use this commands:

#### Install `git` and `python3` (example for Ubuntu/Debian)
```sh
sudo apt update
sudo apt install mediainfo rsync
sudo apt install git python3.10 python3-pip python3.10-venv
```
#### Setting up `config.py`
```sh
git clone https://github.com/upekshaip/tg-ytdlp-bot.git
cd tg-ytdlp-bot/CONFIG
sudo mv _config.py config.py
nano config.py
```
Edit your configuration before deployment.

#### Install `python` modules

```sh
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt
```
---
### Installing ffmpeg (example for Ubuntu/Debian)
      
   you also need to install `ffmpeg`
   **ffmpeg** is essential since **yt-dlp** relies on it for merging streams (and in some cases for transcoding or extracting thumbnails). Also ffmpeg is needed for embedding subtitles and for slpitting bigger that 2gb videos into parts. To install ffmpeg on a Debian-based system, run:

   ```sh
   sudo apt-get update
   sudo apt-get install -y ffmpeg
   ```

   Verify the installation:
   ```sh
   ffmpeg -version
   ```
---
### (Optional) Arabic and Asian fonts

<details>
   <summary>spoiler</summary> 
      
If you need to support extra languages such as arabic, chinese, japanese, korean - you also need to install this language packs:
   ```sh
   sudo apt update
   sudo add-apt-repository universe
   sudo apt update

   sudo apt install fonts-noto-core             # – Noto Sans, Noto Serif, … base fonts Google Noto
   sudo apt install fonts-noto-extra            # – extra fonts (including arabic)
   sudo apt install fonts-kacst fonts-kacst-one # – KACST arabic fonts
   sudo apt install fonts-noto-cjk              # – Chinese-Japanese-Korean characters
   sudo apt install fonts-indic                 # – extra indian fonts

   sudo apt install fonts-noto-color-emoji fontconfig libass9
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

## Running Telegram bot
Now you can start the bot via commands:
```sh
source venv/bin/activate
python3 magic.py
```

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
- **/auto_cache** - Control auto cache reload: `/auto_cache on` | `/auto_cache off` | `/auto_cache N` (N = 1..168 hours, persisted to `CONFIG/config.py`).
---

## Auto cache – how it works (on/off/N)

The bot maintains a local JSON cache (dump) of Firebase data. A background reloader can periodically refresh this cache by first downloading a fresh dump and then reloading it into memory.

- Refresh cycle:
  - Download dump via REST (`download_firebase.py` logic)
  - Reload local JSON into memory
- Interval alignment: next run is aligned to steps from midnight (00:00) with your interval step (N hours).
- Logging examples you will see:
  - `🔄 Downloading and reloading Firebase cache dump...`
  - `✅ Firebase cache refreshed successfully!`

### Command usage
- `/auto_cache on` – enable background auto-refresh
- `/auto_cache off` – disable background auto-refresh
- `/auto_cache N` – set refresh interval to N hours (1..168)
  - This immediately updates runtime settings
  - The value is also persisted to `CONFIG/config.py` by updating `RELOAD_CACHE_EVERY = N`
  - The background thread is safely restarted so the new interval takes effect right away

Your current default interval comes from `CONFIG/config.py`:
```python
RELOAD_CACHE_EVERY = 24  # in hours
```

---

## Updating the bot (updater scripts)

You can update only Python files from the `main` branch of `chelaxian/tg-ytdlp-bot` using provided scripts. The updater will:
- Clone the repository to a temporary directory
- Update only `*.py` files in your working directory
- Preserve your `CONFIG/config.py` and other excluded files/directories
- Make backups of changed files with suffix `.backup_YYYYMMDD_HHMM` and move them into `_backup/` (original structure preserved)
- Ask for confirmation before applying changes

### One-command update (recommended)
```bash
./update.sh
```
- The script checks prerequisites and runs the Python updater.
- After a successful update, restart the bot service (if you use systemd):
```bash
systemctl restart tg-ytdlp-bot
journalctl -u tg-ytdlp-bot -f
```

### Manual update via Python
```bash
python3 update_from_repo.py --show-excluded   # show excluded files/folders
python3 update_from_repo.py                   # interactive update (prompts for confirmation)
```

---

## Restoring from backups

When the updater changes files, it creates backups and moves them into the `_backup/` folder, preserving the original directory structure. Backup filenames have a suffix `.backup_YYYYMMDD_HHMM` (minute-level). The restore tool allows you to revert to a selected backup index.

### Interactive restore (recommended)
```bash
python3 restore_from_backup.py
```
- Use Arrow keys (or j/k) to navigate, PgUp/PgDn for paging, Enter to select, q to quit.
- The list shows grouped backups by minute: `[YYYY-MM-DD HH:MM:SS] files: N (id: YYYYMMDD_HHMM)`.
- After confirmation, all files from that backup are restored to the project root, with the `.backup_YYYYMMDD_HHMM` suffix stripped.

### List available backups
```bash
python3 restore_from_backup.py --list
```
Outputs available backup IDs (newest first) with file counts.

### Non-interactive restore by ID
```bash
python3 restore_from_backup.py --timestamp YYYYMMDD_HHMM
```
Restores all files for the specified backup ID.

### After restore
If you run the bot as a service, restart it:
```bash
systemctl restart tg-ytdlp-bot
journalctl -u tg-ytdlp-bot -f
```

## Link Command Pattern Spec

- **`https://example.com`** \
  Download the video with its original name. \
  If it is a playlist, only the first video is downloaded. 

- **`https://example.com*1*3`**  \
  Download a specified range of videos from the playlist with their original names. 

- **`https://example.com*1*3*name`**  \
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

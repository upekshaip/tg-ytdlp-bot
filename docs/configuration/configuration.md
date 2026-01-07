# Configuration

## Table of Contents
- [Required Configuration](#required-configuration)
- [Optional Configuration](#optional-configuration)
  - [Proxy Support](#proxy-support)
  - [PO Token Provider](#po-token-provider-youtube-bypass)
- [Firebase Setup](#firebase-setup)
- [Limits & Cooldowns](#limits--cooldowns-configlimitspy)
- [Auto Cache](#auto-cache--how-it-works-onoffn)
- [Porn Detection Management](#porn-detection-management)
  - [Porn Detection Commands](#porn-detection-commands)
- [Updating the Bot](#updating-the-bot-updater-scripts)
- [Restoring from Backups](#restoring-from-backups)
- [Auto-Cleaning User Directories](#auto-cleaning-user-directories-with-crontab)
- [Firebase Setup for Telegram Bot](#firebase-setup-for-telegram-bot)
- [Autostart Service](#autostart-service)
- [Dashboard Autostart Service](#dashboard-autostart-service)

## ⚙️ Configuration

### Required Configuration

Edit `CONFIG/config.py` with your settings:

```python
# Bot Configuration
BOT_NAME = "your_bot_name"                    # Your bot's name
BOT_NAME_FOR_USERS = "tg-ytdlp-bot"          # Name in database
ADMIN = [123456789, 987654321]               # List of admin user IDs
API_ID = 12345678                            # Your Telegram API ID
API_HASH = "your_api_hash_here"              # Your Telegram API Hash
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Your bot token

# Channel Configuration (Multiple Log Channels)
LOGS_ID = -1001234567890                     # Main logging channel
LOGS_VIDEO_ID = -1001234567891               # Video download logs
LOGS_NSFW_ID = -1001234567892                # NSFW content logs
LOGS_IMG_ID = -1001234567893                 # Image download logs
LOGS_PAID_ID = -1001234567894                # Paid media logs
LOG_EXCEPTION = -1001234567895               # Error logs
SUBSCRIBE_CHANNEL = -1001234567890           # Subscription channel
SUBSCRIBE_CHANNEL_URL = "https://t.me/your_channel"  # Channel invite link

# Cookie Configuration
COOKIE_URL = "https://your-domain.com/cookies/cookie.txt"  # Fallback cookie URL

# YouTube Cookie URLs (Multiple Sources)
YOUTUBE_COOKIE_URL = "https://your-domain.com/cookies/youtube/cookie1.txt"
YOUTUBE_COOKIE_URL_1 = "https://your-domain.com/cookies/youtube/cookie2.txt"
YOUTUBE_COOKIE_URL_2 = "https://your-domain.com/cookies/youtube/cookie3.txt"
# ... up to YOUTUBE_COOKIE_URL_9

# Firebase Configuration
USE_FIREBASE = True

FIREBASE_USER = "your-email@gmail.com"
FIREBASE_PASSWORD = "your-firebase-password"
FIREBASE_CONF = {
    "apiKey": "your-api-key",
    "authDomain": "your-project.firebaseapp.com",
    "projectId": "your-project-id",
    "storageBucket": "your-project.appspot.com",
    "messagingSenderId": "123456789",
    "appId": "1:123456789:web:abcdef123456",
    "databaseURL": "https://your-project-default-rtdb.firebaseio.com"
}
```

## Optional Configuration

### Proxy Support

```python
# Proxy configuration (up to 2 proxies)
PROXY_TYPE = "http"  # http, https, socks4, socks5, socks5h
PROXY_IP = "X.X.X.X"
PROXY_PORT = 3128
PROXY_USER = "username"
PROXY_PASSWORD = "password"

# Additional Proxy
PROXY_2_TYPE = "socks5"
PROXY_2_IP = "X.X.X.X"
PROXY_2_PORT = 3128
PROXY_2_USER = "username"
PROXY_2_PASSWORD = "password"

# Proxy selection method
PROXY_SELECT = "round_robin"  # random, round_robin
```

### PO Token Provider (YouTube Bypass)

```python
# PO Token Provider configuration
YOUTUBE_POT_ENABLED = True
YOUTUBE_POT_BASE_URL = "http://127.0.0.1:4416"
YOUTUBE_POT_DISABLE_INNERTUBE = False
```

## Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Realtime Database and Authentication
4. Create a user with email/password
5. Get configuration from Project Settings
6. Update `FIREBASE_CONF` in config.py

## Limits & Cooldowns (`CONFIG/limits.py`)

`CONFIG/limits.py` is the single place where all runtime limits for the bot are configured. Before deploying, review this file and tune values for your hardware and hosting:

For more information about administrative commands related to limits, see the [Admin Commands documentation](../commands/admin-commands.md).

- **Downloads & subtitles:** `MAX_FILE_SIZE_GB`, `MAX_VIDEO_DURATION`, and `MAX_SUB_*` prevent extremely large videos/subtitles from entering the queue. In groups, `GROUP_MULTIPLIER` is applied automatically.
- **Images & live streams:** `MAX_IMG_*`, `ENABLE_LIVE_STREAM_BLOCKING`, and `MAX_LIVE_STREAM_DURATION` protect you from endless album/live-stream downloads. On slow connections, increase `MAX_IMG_TOTAL_WAIT_TIME`.
- **Cookie cache:** `COOKIE_CACHE_DURATION`, `COOKIE_CACHE_MAX_LIFETIME`, and `YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR` control how aggressively YouTube cookies are reused and how many retry attempts a single user gets per hour.
- **Rate limits:** `RATE_LIMIT_PER_MINUTE|HOUR|DAY` and the corresponding `RATE_LIMIT_COOLDOWN_*` values implement anti‑spam. When a user exceeds limits, they are put on cooldown for 5/60/1440 minutes.
- **Commands:** `COMMAND_LIMIT_PER_MINUTE` and the exponential `COMMAND_COOLDOWN_MULTIPLIER` protect all commands (not only URLs) from abuse.
- **NSFW monetization:** `NSFW_STAR_COST` defines the Telegram Stars price for paid NSFW posts and can be adjusted at any time.

After changing this file, restart the bot so new limits are applied. If you run multiple instances with different limits, keep separate copies of `CONFIG/limits.py` and mount them via `systemd` or Docker volumes.

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

## Porn Detection Management

The bot includes advanced porn detection capabilities with configurable domain and keyword lists. Admins can manage these lists using dedicated commands.

For more information about these admin commands, see the [Admin Commands documentation](../commands/admin-commands.md#porn-detection-management).

### Porn Detection Commands

#### `/update_porn`
Runs an external script to update porn domains and keywords from external sources.

**Features:**
- Executes customizable script (default: `./script.sh`)
- Shows real-time script output and execution status
- Comprehensive error handling and logging
- Script path configurable via `CONFIG/domains.py`

**Configuration:**
```python
# In CONFIG/domains.py
UPDATE_PORN_SCRIPT_PATH = "./script.sh"  # Customize script path
```

#### `/reload_porn`
Reloads the porn detection cache without restarting the bot.

**Features:**
- Hot-reloads porn domains from `TXT/porn_domains.txt`
- Hot-reloads porn keywords from `TXT/porn_keywords.txt`
- Hot-reloads supported sites from `TXT/supported_sites.txt`
- Shows current cache statistics
- Immediate effect - no bot restart required

### File Structure
```
TXT/
├── porn_domains.txt      # List of porn domains (one per line)
├── porn_keywords.txt     # List of porn keywords (one per line)
└── supported_sites.txt   # List of supported video sites

script.sh                 # Update script (customizable)
```

### Domain Filtering System
The bot uses a three-tier domain filtering system:

1. **WHITELIST** (`CONFIG/domains.py`): Domains completely excluded from porn detection
   - These domains and their subdomains are never checked for porn content
   - Example: `youtube.com`, `bilibili.com`, `dailymotion.com`

2. **GREYLIST** (`CONFIG/domains.py`): Domains excluded only from domain list check
   - These domains are still checked for porn keywords in titles/descriptions
   - But they are excluded from the `porn_domains.txt` file check
   - Useful for sites that might have mixed content

3. **BLACKLIST** (`CONFIG/domains.py`): Domains explicitly blocked
   - Currently empty by default, can be used to block specific domains

**Configuration in `CONFIG/domains.py`:**
```python
# Whitelist - completely excluded from porn detection
WHITELIST = [
    'bilibili.com', 'dailymotion.com', 'youtube.com', 'youtu.be',
    'twitch.tv', 'vimeo.com', 'facebook.com', 'tiktok.com'
]

# Greylist - excluded from domain list but still checked for keywords
GREYLIST = [
    'example.com', 'test.com'
    # Add domains here that should be excluded from porn_domains.txt check
    # but still checked against porn_keywords.txt
]
```

### Integration
These commands integrate with the existing porn detection system:
- **Domain Detection**: Checks video URLs against porn domain lists
- **Keyword Detection**: Scans video titles, descriptions, and captions
- **Auto-tagging**: Automatically adds `#nsfw` tag to detected content
- **Spoiler Protection**: Hides porn content under spoiler tags in Telegram

### Security
- Both commands are admin-only with proper access control
- Script execution is logged for audit purposes
- Script runs from the bot's root directory
- Script output is captured and displayed to the admin

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

## Autostart service

To create auto-start service for this bot - copy text from this file https://github.com/chelaxian/tg-ytdlp-bot/blob/main/etc/systemd/system/tg-ytdlp-bot.service and paste it to
```bash
/etc/systemd/system/tg-ytdlp-bot.service
```
do not forget to change path in service to your actual path

reload systemctl and enable/start service
```bash
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable tg-ytdlp-bot.service
systemctl restart tg-ytdlp-bot.service
journalctl -u tg-ytdlp-bot -f
```

## Dashboard auto-start service

To auto-start the FastAPI dashboard, copy the template `_etc/systemd/system/tg-ytdlp-dashboard.service` to:
```bash
/etc/systemd/system/tg-ytdlp-dashboard.service
```
edit `WorkingDirectory`, `ExecStart`, and port according to your setup.

Reload systemd and enable the unit:
```bash
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable tg-ytdlp-dashboard.service
systemctl restart tg-ytdlp-dashboard.service
journalctl -u tg-ytdlp-dashboard -f
```

The default command runs `uvicorn web.dashboard_app:app --host 0.0.0.0 --port 5555`; add `--reload` or change the port if required.
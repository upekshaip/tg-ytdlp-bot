# 🤖 tg-ytdlp-bot

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PyroTGFork](https://img.shields.io/badge/PyroTGFork-Latest-green.svg)](https://github.com/pyrogram/pyrogram)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![gallery-dl](https://img.shields.io/badge/gallery--dl-Latest-orange.svg)](https://github.com/mikf/gallery-dl)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/tgytdlp)

> 🎥 **Advanced Telegram bot for downloading videos and media from 1500+ platforms**

A powerful Telegram bot that downloads videos, audio, and images from YouTube, TikTok, Instagram, and 1500+ other platforms using yt-dlp and gallery-dl. Features advanced format selection, codec support, intelligent subtitle handling, proxy support, and direct stream links.

## ✨ Features

- 🎬 **1500+ Platforms**: YouTube, TikTok, Instagram, Twitter, Facebook, and many more
- 🌍 **Multi-Language Support**: 4 languages - 🇺🇸 English, 🇷🇺 Русский, 🇸🇦 العربية, 🇮🇳 हिन्दी
- 🍪 **Cookie Support**: Download private/age-restricted content with your own cookies
- 🎯 **Smart Format Selection**: Advanced codec support (H.264/AVC, AV1, VP9) with container preferences
- 📱 **Interactive Menus**: Always Ask quality selection with real-time filtering
- 🔗 **Direct Links**: Get direct stream URLs for media players (VLC, MX Player, etc.)
- 🌐 **Proxy Support**: Global proxy control for all downloads
- 💬 **Subtitle Integration**: Intelligent subtitle handling with language detection
- 🏷️ **Tag System**: Organize your downloads with custom tags
- 📊 **Usage Statistics**: Track your download history and usage
- 🔒 **Privacy Focused**: User-specific settings and secure cookie handling
- 🚀 **PO Token Provider**: Bypass YouTube restrictions automatically
- 🖼️ **Image Support**: Download images from various platforms using gallery-dl
- 🔞 **NSFW Content Management**: Advanced NSFW detection and content filtering
- ⏱️ **Flood Wait Protection**: Smart rate limiting and flood wait handling

## 🚀 Quick Start

### Try the Bot

**Live Demo Bots:**
- 🇮🇹 [@tgytdlp_it_bot](https://t.me/tgytdlp_it_bot) - Main IT bot
- 🇦🇪 [@tgytdlp_uae_bot](https://t.me/tgytdlp_uae_bot) - UAE server
- 🇬🇧 [@tgytdlp_uk_bot](https://t.me/tgytdlp_uk_bot) - UK server
- 🇫🇷 [@tgytdlp_fr_bot](https://t.me/tgytdlp_fr_bot) - FR server

**Community Channel:** [@tg_ytdlp](https://t.me/tg_ytdlp)

### Basic Usage

1. **Send a video URL** to the bot
2. **Choose quality** from the interactive menu
3. **Download** your video with custom settings

```
https://youtube.com/watch?v=dQw4w9WgXcQ
```

## 📋 Table of Contents

- [Installation](#-installation)
- [Configuration](#-configuration)
- [User Commands](#-user-commands)
- [Advanced Features](#-advanced-features)
- [Admin Commands](#-admin-commands)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Support](#-support)

---

## 🛠️ Installation

### 🚢 Docker Deployment (recommended for most users)

This is the easiest way to run the bot: everything (bot + PO token provider + cookie webserver) runs in Docker containers.

**Requirements:**
- **Docker** and **Docker Compose**
- A server or VPS with Linux (Ubuntu/Debian recommended)

**Step 1 – Create config file:**

```bash
git clone https://github.com/chelaxian/tg-ytdlp-bot.git
cd tg-ytdlp-bot
cp CONFIG/_config.py CONFIG/config.py
```

Then edit `CONFIG/config.py` and fill in at least:
- **BOT_NAME** – any internal name of your bot
- **BOT_NAME_FOR_USERS** – name used in DB (usually real bot username without `@`)
- **ADMIN** – list with at least your Telegram user ID
- **API_ID**, **API_HASH** – from [my.telegram.org](https://my.telegram.org) (see section [Getting API Credentials](#getting-api-credentials))
- **BOT_TOKEN** – from [@BotFather](https://t.me/BotFather) (see section [Getting API Credentials](#getting-api-credentials))
- **LOGS\_*** (LOGS_ID, LOGS_VIDEO_ID, LOGS_NSFW_ID, LOGS_IMG_ID, LOGS_PAID_ID, LOG_EXCEPTION) – Fill in all the fields, if you want you can use the same channel for all
- **SUBSCRIBE_CHANNEL** and **SUBSCRIBE_CHANNEL_URL** – channel ID and invite link users must join

**Configuration Example:**

`tg-ytdlp-bot/CONFIG/config.py`:
```python
#####################################################################
# FILL IN ONLY THAT PART !!!
#####################################################################

# Bot Configuration
BOT_NAME = "your_bot_name"                   # Your bot's name
BOT_NAME_FOR_USERS = "tg-ytdlp-bot"          # Name in database
ADMIN = [123456789]                          # List of admin user IDs
API_ID = 12345678                            # Your Telegram API ID
API_HASH = "your_api_hash_here"              # Your Telegram API Hash
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Your bot token

# Channel Configuration (Multiple Log Channels)
LOGS_ID = -1001234567890                     # Main logging channel
LOGS_VIDEO_ID = -1001234567890               # Video download logs
LOGS_NSFW_ID = -1001234567890                # NSFW content logs
LOGS_IMG_ID = -1001234567890                 # Image download logs
LOGS_PAID_ID = -1001234567890                # Paid media logs
LOG_EXCEPTION = -1001234567890               # Error logs
SUBSCRIBE_CHANNEL = -1000987654321           # Subscription channel
SUBSCRIBE_CHANNEL_URL = "https://t.me/your_channel"  # Channel invite link

#####################################################################
# LEAVE ALL ANOTHER PARTS UNCHANGED !!!
#####################################################################
```

**Cookies configuration:**

First fill in `TXT/cookie.txt` file. That cookie will be used by default for all users. You can paste YouTube cookie here.(see section [Get YouTube cookies](#get-youtube-cookies) below for export and requirements).


```
tg-ytdlp-bot/
└── TXT/
    └── cookie.txt
```

`tg-ytdlp-bot/TXT/cookie.txt`:
```
# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This file was generated by Cookie-Editor
.youtube.com  TRUE  /  FALSE  111  ST-xxxxx  session_logininfo=AAA
.youtube.com  TRUE  /  FALSE  222  ST-xxxxx  session_logininfo=BBB
.youtube.com  TRUE  /  FALSE  33333  ST-xxxxx  session_logininfo=CCC
```

Aslo you can fill in extra cookie files for only services you need (for ex. YouTube, TikTok e.t.c.) and left others unchanged. 
You can add up to 10 extra YouTube cookies. They will be used as a backup cookie if previous become invalid.
All cookie URLs in the template already point to the internal `configuration-webserver` container,
you only need to put real cookie files into `docker/configuration-webserver/site/cookies` before starting.
```
tg-ytdlp-bot/
└── docker/
    └── configuration-webserver/
        └── site/
            └── cookies/
                ├── README.txt
                ├── cookie.txt
                ├── facebook.txt
                ├── instagram.txt
                ├── tiktok.txt
                ├── twitter.txt
                ├── vk.txt
                ├── youtube.txt
                ├── youtube-1.txt
                ├── youtube-[N=2-9].txt
                └── youtube-10.txt
```

`tg-ytdlp-bot/docker/configuration-webserver/site/cookies/youtube.txt`:
```
# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This file was generated by Cookie-Editor
.youtube.com  TRUE  /  FALSE  111  ST-xxxxx  session_logininfo=AAA
.youtube.com  TRUE  /  FALSE  222  ST-xxxxx  session_logininfo=BBB
.youtube.com  TRUE  /  FALSE  33333  ST-xxxxx  session_logininfo=CCC
```
**Step 2 – Environment file (.env):**

```bash
cp .env.example .env
```

You can optionally change:
- `COMPOSE_PROJECT_NAME` – project name prefix for Docker
- `TZ` – your timezone (e.g. `Europe/Moscow`)

**Step 3 – Start containers:**

```bash
docker compose up -d --build
```

The bot container will be built from the included `Dockerfile`, and:
- `configuration-webserver` will serve cookie files at `http://configuration-webserver/cookies/<filename>`
- `bgutil-provider` will be available at `http://bgutil-provider:4416` for YouTube PO tokens
- **Dashboard panel** will be available at `http://localhost:5555` (or `http://<your-server-ip>:5555`)

**Step 4 – Access the Dashboard Panel:**

After starting the containers, the web dashboard panel will automatically start on port **5555** (configurable via `DASHBOARD_PORT` in `CONFIG/config.py`). You can access it at:
- `http://localhost:5555` (if accessing from the same machine)
- `http://<your-server-ip>:5555` (if accessing remotely)

**Note:** If you change `DASHBOARD_PORT` in the config, make sure to update the port mapping in `docker-compose.yml` accordingly.

**Default credentials:**
- **Username:** `admin` (defined in `CONFIG/config.py` as `DASHBOARD_USERNAME`)
- **Password:** `admin123` (defined in `CONFIG/config.py` as `DASHBOARD_PASSWORD`)

**⚠️ Important:** Change the default password immediately after first login!

**How to change the password:**

1. Log in to the dashboard at `http://<your-server-ip>:5555`
2. Go to the **System** tab
3. Find the **Configuration** section
4. Locate the **Password** field (under "Dashboard authentication")
5. Enter your new password and click **Save**

The password will be automatically updated in `CONFIG/config.py` and will take effect immediately (no restart required).

**Dashboard features:**
- Real-time active users monitoring
- Top downloaders, domains, countries statistics
- NSFW content tracking
- System metrics and configuration management
- User blocking/unblocking functionality
- And much more...

P.S. do not forget to add your bot to your channels with admin rights
---

### Manual Installation (without Docker)

#### Prerequisites

- **Python 3.10+**
- **Ubuntu/Debian** (recommended) or other Linux distribution
- **Chromium** (recommended) or other Browser (optional, for `/cookies_from_browser` command)
- **Docker** (optional, for PO Token Provider)
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **Telegram API Credentials** from [my.telegram.org](https://my.telegram.org)

### Step 1: Clone Repository

```bash
git clone https://github.com/chelaxian/tg-ytdlp-bot.git
cd tg-ytdlp-bot
```

### Step 2: Install Dependencies

```bash
# Update system packages
sudo apt update
sudo apt install -y git python3.10 python3-pip python3.10-venv mediainfo rsync

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --no-cache-dir -r requirements.txt
```

### Step 3: Install FFmpeg

```bash
# Install FFmpeg (required for video processing)
sudo apt-get install -y ffmpeg

# Verify installation
ffmpeg -version
```

### Step 4: Setup Configuration

```bash
# Navigate to config directory
cd CONFIG

# Copy template configuration
cp _config.py config.py

# Edit configuration
nano config.py
```

### Step 5: Start the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Start the bot
python3 magic.py
```

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
### Optional Configuration

#### Proxy Support

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

#### PO Token Provider (YouTube Bypass)

```python
# PO Token Provider configuration
YOUTUBE_POT_ENABLED = True
YOUTUBE_POT_BASE_URL = "http://127.0.0.1:4416"
YOUTUBE_POT_DISABLE_INNERTUBE = False
```

### Getting API Credentials

#### 1. Bot Token
1. Message [@BotFather](https://t.me/BotFather)
2. Create a new bot with `/newbot`
3. Copy the bot token

#### 2. API ID & Hash
1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy API ID and API Hash

#### 3. Channel IDs
1. Create channels and add your bot as admin
2. Get channel IDs using [@userinfobot](https://t.me/userinfobot)
3. Channel IDs start with `-100`

#### 4. User ID
1. Message [@UserInfoToBot](https://t.me/UserInfoToBot)
2. Copy your user ID
3. Add to `ADMIN` list in config.py

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Realtime Database and Authentication
4. Create a user with email/password
5. Get configuration from Project Settings
6. Update `FIREBASE_CONF` in config.py

### Cookie Setup

1. Use [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) browser extension
2. Export cookies in Netscape format
3. Upload to web server (HTTPS required)
4. Update cookie URLs in config.py
5. Files must be under 100KB and accessible without authentication
---
### Installing ffmpeg (example for Ubuntu/Debian)
      
   you also need to install `ffmpeg` https://github.com/btbn/ffmpeg-builds/releases
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

#### Get YouTube cookies

YouTube rotates account cookies frequently on open YouTube browser tabs as a security measure. To export cookies that will remain working with yt-dlp, you will need to export cookies in such a way that they are never rotated.

One way to do this is through a private browsing/incognito window:

- Open a new private browsing/incognito window and log into YouTube
- In same window and same tab from step 1, navigate to https://www.youtube.com/robots.txt (this should be the only private/incognito browsing tab open)
- Export youtube.com cookies from the browser, then close the private browsing/incognito window so that the session is never opened in the browser again.

For export you can use browser extension [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)

create in project folder subfolder `TXT` and place `cookie.txt` extracted from YouTube here

```sh
cd tg-ytdlp-bot/TXT
nano cookie.txt
```

---

#### Advanced YouTube Cookie Management

The bot now supports automatic downloading and validation of YouTube cookies from multiple sources:

**Features:**
- **Multiple Sources**: Configure up to 10 different cookie sources
- **Automatic Validation**: Each downloaded cookie is tested for functionality
- **Fallback System**: If one source fails, automatically tries the next
- **Real-time Progress**: Shows download and validation progress to users

**Configuration in `CONFIG/config.py`:**
```python
# YouTube cookies URLs - main URL and backups
# The bot will check cookies in the order: YOUTUBE_COOKIE_URL, YOUTUBE_COOKIE_URL_1, YOUTUBE_COOKIE_URL_2, etc.
# If one URL does not work or the cookies are expired, the bot will automatically try the next one
YOUTUBE_COOKIE_URL = "https://your-domain.com/cookies/youtube/cookie1.txt"
YOUTUBE_COOKIE_URL_1 = "https://your-domain.com/cookies/youtube/cookie2.txt"
YOUTUBE_COOKIE_URL_2 = "https://your-domain.com/cookies/youtube/cookie3.txt"
YOUTUBE_COOKIE_URL_3 = "https://your-domain.com/cookies/youtube/cookie4.txt"
YOUTUBE_COOKIE_URL_4 = "https://your-domain.com/cookies/youtube/cookie5.txt"
# Add more sources as needed (up to YOUTUBE_COOKIE_URL_9)
```

**How it works:**
1. User runs `/cookie` and selects YouTube
2. Bot downloads cookies from the first available source
3. Validates cookies by testing them with a YouTube video
4. If validation fails, automatically tries the next source
5. Continues until working cookies are found or all sources are exhausted

**User Experience:**
- Progress updates: "🔄 Downloading and checking YouTube cookies... Attempt 1 of 4"
- Success message: "✅ YouTube cookies successfully downloaded and validated! Used source 2 of 4"
- Failure message: "❌ All YouTube cookies are expired or unavailable! Contact the bot administrator to replace them."

Also you may fill in `porn_domains.txt` `porn_keywords.txt` files in `TXT` folder if you want to tag #nsfw videos and hide them under spoiler

---

## ⏳ Limits & Cooldowns (`CONFIG/limits.py`)

`CONFIG/limits.py` is the single place where all runtime limits for the bot are configured. Before deploying, review this file and tune values for your hardware and hosting:

- **Downloads & subtitles:** `MAX_FILE_SIZE_GB`, `MAX_VIDEO_DURATION`, and `MAX_SUB_*` prevent extremely large videos/subtitles from entering the queue. In groups, `GROUP_MULTIPLIER` is applied automatically.
- **Images & live streams:** `MAX_IMG_*`, `ENABLE_LIVE_STREAM_BLOCKING`, and `MAX_LIVE_STREAM_DURATION` protect you from endless album/live-stream downloads. On slow connections, increase `MAX_IMG_TOTAL_WAIT_TIME`.
- **Cookie cache:** `COOKIE_CACHE_DURATION`, `COOKIE_CACHE_MAX_LIFETIME`, and `YOUTUBE_COOKIE_RETRY_LIMIT_PER_HOUR` control how aggressively YouTube cookies are reused and how many retry attempts a single user gets per hour.
- **Rate limits:** `RATE_LIMIT_PER_MINUTE|HOUR|DAY` and the corresponding `RATE_LIMIT_COOLDOWN_*` values implement anti‑spam. When a user exceeds limits, they are put on cooldown for 5/60/1440 minutes.
- **Commands:** `COMMAND_LIMIT_PER_MINUTE` and the exponential `COMMAND_COOLDOWN_MULTIPLIER` protect all commands (not only URLs) from abuse.
- **NSFW monetization:** `NSFW_STAR_COST` defines the Telegram Stars price for paid NSFW posts and can be adjusted at any time.

After changing this file, restart the bot so new limits are applied. If you run multiple instances with different limits, keep separate copies of `CONFIG/limits.py` and mount them via `systemd` or Docker volumes.

---

## 👤 User Commands

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot | `/start` |
| `/help` | Show help message | `/help` |
| `/settings` | Open settings menu | `/settings` |
| `/usage` | Show usage statistics | `/usage` |
| `/tags` | Get all your tags | `/tags` |
| `/lang` | Change bot language | `/lang ru` |

### Download Commands

| Command | Description | Example |
|---------|-------------|---------|
| **Video URL** | Download video (auto-detect) | `https://youtube.com/watch?v=...` |
| `/vid` | Download video | `/vid https://youtube.com/watch?v=...` |
| `/audio` | Download audio only | `/audio https://youtube.com/watch?v=...` |
| `/link` | Get direct video links | `/link 720 https://youtube.com/watch?v=...` |
| `/img` | Download images | `/img https://instagram.com/p/...` |

### Format & Quality Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/format` | Choose video format/codec | `/format 720` |
| `/split` | Set video split size | `/split 500mb` |
| `/mediainfo` | Toggle mediainfo display | `/mediainfo on` |

### Subtitle Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/subs` | Configure subtitles | `/subs en auto` |

### Cookie Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/cookie` | Download cookies | `/cookie youtube` |
| `/check_cookie` | Validate cookies | `/check_cookie` |
| `/save_as_cookie` | Upload cookie file | `/save_as_cookie` |
| `/cookies_from_browser` | Extract from browser | `/cookies_from_browser` |

### Advanced Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/args` | Configure yt-dlp arguments (grouped menu) | `/args` |
| `/list` | Show available formats for URL | `/list https://youtube.com/watch?v=...` |
| `/proxy` | Enable/disable proxy | `/proxy on` |
| `/keyboard` | Manage reply keyboard | `/keyboard full` |
| `/search` | Inline search helper | `/search` |
| `/clean` | Clean user files | `/clean args` |
| `/nsfw` | NSFW content settings | `/nsfw on` |
| `/flood_wait` | Flood wait settings | `/flood_wait` |

### Command Arguments

Many commands support direct arguments for quick configuration:

```bash
# Format with quality
/format 720    # Set to 720p or lower
/format 4k     # Set to 4K or lower
/format best   # Set to best quality

# Keyboard layouts
/keyboard off   # Hide keyboard
/keyboard 1x3   # Single row
/keyboard 2x3   # Double row (default)
/keyboard full  # Emoji keyboard

# Split sizes
/split 100mb   # 100MB (minimum)
/split 500mb   # 500MB
/split 1gb     # 1GB
/split 2gb     # 2GB (maximum)

# Subtitle languages
/subs off       # Disable subtitles
/subs ru        # Russian subtitles
/subs en auto   # English with auto-translate

# Cookie services
/cookie youtube  # YouTube cookies
/cookie tiktok   # TikTok cookies
/cookie x        # Twitter/X cookies

# Language settings
/lang en         # 🇺🇸 Set to English
/lang ru         # 🇷🇺 Set to Russian
/lang ar         # 🇸🇦 Set to Arabic
/lang in         # 🇮🇳 Set to Hindi

# Clean specific settings
/clean args      # Clear yt-dlp arguments
/clean nsfw      # Clear NSFW settings
/clean proxy     # Clear proxy settings
/clean flood_wait # Clear flood wait settings

# Format with ID selection
/format id 134   # Download specific format ID (with audio)
/format id 401   # Download specific format ID (with audio)

# List available formats
/list https://youtube.com/watch?v=...  # Show all available formats
```

---

## 🌍 Multi-Language Support

The bot supports 4 languages with full interface translation:

### Supported Languages

| Language | Code | Native Name | Flag |
|----------|------|-------------|------|
| 🇺🇸 English | `en` | English | 🇺🇸 |
| 🇷🇺 Russian | `ru` | Русский | 🇷🇺 |
| 🇸🇦 Arabic | `ar` | العربية | 🇸🇦 |
| 🇮🇳 Hindi | `in` | हिन्दी | 🇮🇳 |

### Language Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/lang` | Show language selection menu | `/lang` |
| `/lang en` | 🇺🇸 Quick switch to English | `/lang en` |
| `/lang ru` | 🇷🇺 Quick switch to Russian | `/lang ru` |
| `/lang ar` | 🇸🇦 Quick switch to Arabic | `/lang ar` |
| `/lang in` | 🇮🇳 Quick switch to Hindi | `/lang in` |

### Language Features

- **Persistent Settings**: Your language choice is saved and remembered
- **Full Interface Translation**: All menus, buttons, and messages are translated
- **Quick Switching**: Change language instantly with `/lang <code>`
- **Interactive Menu**: Use `/lang` without arguments for visual language selection
- **Fallback Support**: Defaults to English if language file is unavailable

### Language Files Structure

```
CONFIG/LANGUAGES/
├── messages_EN.py    # English messages
├── messages_RU.py    # Russian messages  
├── messages_AR.py    # Arabic messages
├── messages_IN.py    # Hindi messages
└── language_router.py # Language routing system
```

---

## 🎯 Advanced Features

### 🎬 Always Ask Menu

Interactive quality selection with advanced filtering:

- **📼 CODEC Button**: Choose between H.264/AVC, AV1, VP9 codecs
- **📹 DUBS Button**: Select audio language with flag indicators
- **💬 SUBS Button**: Choose subtitle language with smart detection
- **☑️ LINK Button**: Toggle direct link mode for media players
- **Dynamic Filtering**: Real-time quality filtering based on selections

### 🍪 Advanced Cookie Management

- **Multiple Sources**: Configure up to 10 YouTube cookie sources
- **Automatic Validation**: Each cookie is tested for functionality
- **Fallback System**: Automatic switching between sources
- **Browser Integration**: Extract cookies from installed browsers
- **Real-time Progress**: Live updates during download and validation

**Configuration Example:**
```python
# In CONFIG/config.py
YOUTUBE_COOKIE_URL = "https://your-domain.com/cookies/youtube/cookie1.txt"
YOUTUBE_COOKIE_URL_1 = "https://your-domain.com/cookies/youtube/cookie2.txt"
YOUTUBE_COOKIE_URL_2 = "https://your-domain.com/cookies/youtube/cookie3.txt"
# ... up to YOUTUBE_COOKIE_URL_9
```

**User Commands:**
- `/cookie` → YouTube: Downloads and validates cookies from multiple sources
- `/check_cookie`: Validates existing cookies and checks YouTube functionality
- `/cookies_from_browser`: Extracts cookies from installed browsers
- `/save_as_cookie`: Upload custom cookie file

**Cookie Validation Process:**
1. **Download**: Fetches cookie file from configured source
2. **Format Check**: Validates Netscape cookie format
3. **Size Validation**: Ensures file size is under 100KB
4. **YouTube Test**: Tests cookies with a short YouTube video
5. **Error Analysis**: Distinguishes between authentication and network errors
6. **Fallback**: Tries next source if current one fails

**Cookie File Requirements:**
- **Format**: Must be in Netscape cookie format
- **Size Limit**: Maximum 100KB per cookie file
- **Access**: Cookie files must be accessible via HTTP/HTTPS URLs

**Security Features:**
- **URL Hiding**: Source URLs are hidden from users in error messages
- **Error Sanitization**: Sensitive information is removed from logs
- **Temporary Files**: Cookie files are cleaned up after validation
- **Access Control**: Cookie management commands are properly restricted

### 🌐 Proxy Support

- **Global Control**: Enable/disable proxy for all operations
- **User-Specific**: Each user controls their own proxy usage
- **Multiple Proxies**: Support for up to 2 proxy servers
- **Selection Methods**: Round-robin or random proxy selection
- **Automatic Integration**: Works with all download operations

### 🔗 Direct Link Extraction

- **Quality Selection**: Specify desired quality (720, 1080, 4k, 8k)
- **Player Integration**: Direct links for VLC, MX Player, Infuse, IINA, nPlayer, MPV
- **Smart Fallback**: Automatic fallback to best available quality
- **Dual Stream Support**: Separate video and audio stream URLs

### 🏷️ Tag System

Add tags to any link for organization:

```
https://youtube.com/watch?v=... #music #favorite #2024
```

Tags are automatically added to video captions and saved in your `tags.txt` file.

### 🖼️ Image Download Support

Download images from various platforms:

- **Direct URLs**: Any image link with common extensions
- **Platforms**: Imgur, Flickr, DeviantArt, Pinterest, Instagram, Twitter/X, Reddit
- **Cloud Storage**: Google Drive, Dropbox, Mega.nz
- **Ranges**: Download specific ranges from albums/feeds

### ⚙️ Custom yt-dlp Arguments (`/args`)

Configure advanced yt-dlp parameters with grouped interface:

- **Boolean Options**: Enable/disable features (extract_flat, write_automatic_sub, etc.)
- **Text Parameters**: Custom referer, user agent, output template
- **Numeric Settings**: Retries, timeout, fragment retries
- **JSON Headers**: Custom HTTP headers for specific sites
- **Selection Options**: Audio quality, video quality, format selection

**Grouped Menu Interface:**
- ✅/❌ **Boolean** - True/False switches
- 📋 **Select** - Choose from options
- 🔢 **Numeric** - Number input
- 📝🔧 **Text** - Text/JSON input

**Example Configuration:**
```
Referer: https://example.com
User Agent: Custom Bot 1.0
Custom HTTP Headers: {"X-API-Key": "your-key"}
Retries: 5
Timeout: 30
```

### 📋 Format List Command (`/list`)

View all available formats for any video URL:

- **Complete Format List**: Shows all available video/audio formats
- **Format Details**: Resolution, codec, file size, quality information
- **Download Hints**: Instructions on how to use `/format` command
- **File Export**: Sends complete format list as downloadable text file

**Usage:**
```bash
/list https://youtube.com/watch?v=dQw4w9WgXcQ
```

**Features:**
- Shows format ID, resolution, codec, file size
- Includes download instructions for `/format` command
- Exports complete list as text file
- Works with all supported platforms

### 🚀 PO Token Provider (YouTube Bypass)

Automatically bypass YouTube restrictions:

- **"Sign in to confirm"** message bypass
- **IP-based blocking** protection
- **Rate limiting** mitigation
- **Transparent Operation**: Works with existing proxy and cookie systems
- **Automatic Fallback**: Falls back to standard extraction if provider unavailable

**Setup:**
```bash
# Install Docker
sudo apt install -y docker.io

# Run PO Token Provider
docker run -d --name bgutil-provider -p 4416:4416 --init --restart unless-stopped brainicism/bgutil-ytdlp-pot-provider

# Install yt-dlp plugin
python3 -m pip install -U bgutil-ytdlp-pot-provider
```

**Configuration:**
```python
# In CONFIG/config.py
YOUTUBE_POT_ENABLED = True
YOUTUBE_POT_BASE_URL = "http://127.0.0.1:4416"
YOUTUBE_POT_DISABLE_INNERTUBE = False
```

**Technical Details:**
- Uses proper Python API format for `extractor_args`: `dict -> dict -> list[str]`
- `disable_innertube` is only added when enabled (as `["1"]` string in list)
- Compatible with yt-dlp >= 2025.05.22
- Works with both HTTP and script-based providers
- **Automatic Fallback**: If PO token provider is unavailable, bot automatically falls back to standard YouTube extraction
- **Health Monitoring**: Provider availability is cached and checked every 30 seconds

**Requirements:**
- Docker container running `brainicism/bgutil-ytdlp-pot-provider`
- yt-dlp plugin: `bgutil-ytdlp-pot-provider`

**Fallback Mechanism:**
- **Automatic Detection**: Bot checks provider availability before each YouTube request
- **Cached Health Checks**: Provider status is cached for 30 seconds to avoid excessive requests
- **Graceful Degradation**: If provider is unavailable, bot automatically falls back to standard YouTube extraction
- **No User Impact**: Fallback is completely transparent to users
- **Admin Monitoring**: Provider health is automatically monitored and logged

### Proxy Download Support (`/proxy`)
- **Global Proxy Control**: Enable/disable proxy for all yt-dlp operations
- **User-Specific Settings**: Each user can independently control their proxy usage
- **Automatic Integration**: When enabled, proxy is automatically applied to all downloads
- **Cookie Support**: Works with user's cookie settings for private content
- **Persistent Settings**: Proxy preference is saved per-user in `proxy.txt` file

**Usage Examples:**
```bash
/proxy on                    # Enable proxy for all downloads
/proxy off                   # Disable proxy for all downloads
/proxy                      # Show proxy control menu
```

**How it works:**
1. User runs `/proxy on` to enable proxy
2. Bot saves preference to `users/{user_id}/proxy.txt`
3. All subsequent yt-dlp operations automatically use the configured proxy
4. User can disable with `/proxy off` at any time

### Enhanced Direct Link Extraction (`/link`)
- **Quality Selection**: Specify desired quality (e.g., `720`, `1080`, `4k`, `8k`)
- **Flexible Format**: Support for both numeric (`720`) and descriptive (`720p`, `4k`, `8K`) quality specifications
- **Smart Fallback**: Automatically falls back to best available quality if specified quality is not available
- **Dual Stream Support**: Returns both video and audio stream URLs when available
- **Proxy Support**: Works with configured proxy settings for restricted domains
- **Cookie Integration**: Uses user's cookie settings for private content access
- **Player Integration**: 🔗Link button in Always Ask menu now provides direct links for media players (VLC, MX Player, Infuse, IINA, nPlayer, MPV)

**Usage Examples:**
```bash
/link https://youtube.com/watch?v=...          # Best quality
/link 720 https://youtube.com/watch?v=...     # 720p or lower
/link 720p https://youtube.com/watch?v=...    # Same as above
/link 4k https://youtube.com/watch?v=...      # 4K or lower
/link 8k https://youtube.com/watch?v=...      # 8K or lower
```

**Player Support:**
- **🌐 Browser**: Direct stream URL for web browsers
- **🎬 VLC (iOS)**: iOS VLC player with x-callback support
- **🎬 VLC (Android)**: Android VLC player with intent support

### Enhanced Format Selection (`/format`)
- **Codec Support**: Choose between H.264/AVC (avc1), AV1 (av01), and VP9 (vp9)
- **Container Toggle**: Switch between MP4 and MKV containers
- **Smart Quality Selection**: Prioritizes exact height matches before falling back to "less than or equal to"
- **Persistent Preferences**: Your codec and container choices are saved per-user
- **Quick Quality Setting**: Use arguments to set quality directly (e.g., `/format 720`, `/format 4k`)
- **Format ID Support**: Download specific format IDs with automatic audio addition
- **Smart Audio Handling**: Video-only formats automatically get best audio added

### Advanced Command Arguments
The bot now supports command arguments for quick configuration without opening menus:

#### `/format` with Quality Arguments
```bash
/format 720    # Set quality to 720p or lower
/format 4k     # Set quality to 4K or lower  
/format 8k     # Set quality to 8K or lower
/format best   # Set to best quality
/format ask    # Always ask for quality selection
/format id 134 # Download specific format ID (with audio)
/format id 401 # Download specific format ID (with audio)
```

#### `/keyboard` with Layout Arguments
```bash
/keyboard off   # Hide reply keyboard
/keyboard 1x3  # Set single row layout
/keyboard 2x3  # Set double row layout (default)
/keyboard full  # Set emoji keyboard
```

#### `/split` with Size Arguments
```bash
/split 100mb   # Set split size to 100MB (minimum)
/split 250mb   # Set split size to 250MB
/split 500mb   # Set split size to 500MB
/split 750mb   # Set split size to 750MB
/split 1gb     # Set split size to 1GB
/split 1.5gb   # Set split size to 1.5GB
/split 2gb     # Set split size to 2GB (maximum)
/split 300mb   # Any custom size between 100MB-2GB
/split 1.2gb   # Decimal values supported
/split 1500mb  # Up to 2000MB (2GB)
```

#### `/subs` with Language and Mode Arguments
```bash
/subs off       # Disable subtitles
/subs ru        # Set subtitle language to Russian
/subs en        # Set subtitle language to English
/subs en auto   # Set language to English with AUTO/TRANS enabled
/subs fr auto   # Set language to French with AUTO/TRANS enabled
```

#### `/cookie` with Service Arguments
```bash
/cookie                # Show cookie menu
/cookie youtube        # Download YouTube cookies directly
/cookie tiktok         # Download TikTok cookies directly
/cookie x              # Download Twitter/X cookies directly (alias)
/cookie twitter        # Download Twitter/X cookies directly
/cookie custom         # Show custom cookie instructions
```

#### YouTube Cookie Index Selection

You can select a specific YouTube cookie source by index and then verify it:

```bash
/cookie youtube 1     # use source #1 (1–N as shown in the /cookie menu)
/cookie youtube 3     # use source #3
/check_cookie         # validate current YouTube cookies (tests on RickRoll)
```

#### Format List Command

View all available formats for any video URL:

```bash
/list https://youtube.com/watch?v=dQw4w9WgXcQ  # Show all formats
```

**Features:**
- Complete format list with ID, resolution, codec, file size
- Download instructions for `/format` command
- Exports as downloadable text file
- Works with all supported platforms

### Always Ask Menu
- **📼CODEC Button**: Access advanced codec and container filters
  - AVC (H.264/AVC) - Traditional, widely supported
  - AV1 - Modern royalty-free codec with ~25-40% better efficiency
  - VP9 - Google's VP9 codec
  - MP4/MKV container selection
- **📹 DUBS Button**: Select audio language with flag indicators
  - Only appears when multiple audio languages are detected
  - Pagination support for long language lists
- **💬 SUBS Button**: Choose subtitle language with smart detection
  - Auto-generated vs. normal captions
  - Translation indicators
  - Pagination support
- **☑️LINK Button**: Toggle direct link mode
  - When enabled (✅LINK), clicking quality buttons returns direct links instead of downloading
  - Respects all selected filters (codec, container, audio language, subtitles)
  - No caching for direct links
  - Always available in the main menu (not just in CODEC filters)
- **Dynamic Filtering**: Real-time quality filtering based on selected codec/container
- **Smart Subtitle Logic**: Differentiates between "Always Ask" mode and manual subtitle selection

### Intelligent Subtitle Handling
- **Container-Aware Embedding**:
  - **MKV**: Soft-muxing (subtitles as separate track, no quality loss)
  - **MP4**: Hard-embedding (burned into video for universal compatibility)
- **Language Detection**: Optimized yt-dlp client selection for faster subtitle discovery
- **Auto Mode**: Automatically selects auto-generated or normal captions based on user preference
- **Always Ask Mode**: Shows all available subtitle languages for manual selection

### Enhanced Cookie Management
- **Browser Integration**: Extract cookies from installed browsers
- **Fallback Support**: Automatic download from Config.COOKIE_URL if no browsers found
- **Multiple Sources**: Choose between browser extraction and direct download
- **YouTube Cookie Validation**: Automatic testing and validation of YouTube cookies
- **Multi-Source Fallback**: Automatic switching between multiple cookie sources
- **Real-time Progress**: Live updates during cookie download and validation process
- **Proxy Support**: Automatic proxy usage for restricted domains (configurable in `CONFIG/domains.py`)

### Reply Keyboard Management
- **Customizable Layout**: Choose between 1x3 (single row), 2x3 (double row), and FULL (emoji) keyboard layouts
- **Smart Display**: Keyboard automatically shows/hides based on user preferences
- **Persistent Settings**: User keyboard preferences are saved in `keyboard.txt` file
- **Easy Toggle**: Quickly switch between OFF, 1x3, 2x3, and FULL modes via `/keyboard` command
- **Quick Arguments**: Set layout directly with arguments (e.g., `/keyboard off`, `/keyboard full`)

**Keyboard Modes:**
- **OFF**: Completely hides the reply keyboard
- **1x3**: Shows single row with `/clean`, `/cookie`, `/settings`
- **2x3**: Shows two rows with full command set (default mode)
- **FULL**: Shows emoji keyboard with visual command representation

### 🔞 NSFW Content Management

Advanced NSFW detection and content filtering system:

- **Automatic Detection**: Scans video titles, descriptions, and domains for adult content
- **Smart Tagging**: Automatically adds `#nsfw` tag to detected content
- **Spoiler Protection**: Hides NSFW content under spoiler tags in Telegram
- **User Control**: Toggle NSFW blur settings with `/nsfw on/off`
- **Admin Management**: Update and manage porn detection lists
- **Multi-Source Detection**: Domain-based and keyword-based filtering
- **Configurable Lists**: Customizable porn domains and keywords

**NSFW Commands:**
```bash
/nsfw on          # Enable NSFW blur
/nsfw off         # Disable NSFW blur
/nsfw             # Show NSFW settings menu
```

**Admin NSFW Commands:**
```bash
/update_porn      # Update porn detection lists
/reload_porn      # Reload porn detection cache
/check_porn       # Check URL for NSFW content
```

### ⏱️ Flood Wait Protection

Smart rate limiting and flood wait handling:

- **Automatic Detection**: Detects Telegram API rate limits
- **User Notification**: Informs users about flood wait periods
- **Settings Persistence**: Saves flood wait settings per user
- **Smart Recovery**: Automatically handles rate limit recovery
- **Admin Monitoring**: Tracks flood wait events in logs

**Flood Wait Features:**
- Automatic flood wait detection and handling
- User notification with estimated wait time
- Settings persistence across bot restarts
- Integration with all bot commands
- Admin monitoring and logging

### Improved Error Handling
- **Upload Retries**: Smart retry logic for failed uploads with fallback to document mode
- **Dynamic Disk Space**: Intelligent space estimation based on video size
- **Graceful Degradation**: Better handling of format unavailability and network issues
- **Flood Wait Recovery**: Automatic handling of Telegram API rate limits

---

## Paid posts (Telegram Stars) and Group Mode

- **Paid posts (Stars)**: The bot can send paid posts via Telegram Stars for NSFW content in private chats.
  - The cover is prepared automatically (320×320 with padding) to meet Telegram requirements.
  - Price is configured in `CONFIG/limits.py` via `NSFW_STAR_COST`.
  - For channels/groups, relay is supported (when the bot is added as an admin); paid media is cached properly.

- **Adding the bot to a group**: Add the bot as an admin to your group/supergroup to use commands inside the chat.
  - In group mode, extended limits apply: **limits are doubled** (sizes/queues), reducing fallbacks to document mode for large files.
  - All other features (formats, proxy, cookies, direct links) work the same as in private chats.
  - NSFW content has no Telegram Stars cost in groups

Note: You can tune exact limit values and behavior in `CONFIG/limits.py` and `CONFIG/config.py` according to your hosting and needs.



---

## 👨‍💼 Admin Commands

### User Management

| Command | Description | Example |
|---------|-------------|---------|
| `/block_user` | Block a user | `/block_user 123456789` |
| `/unblock_user` | Unblock a user | `/unblock_user 123456789` |
| `/all_users` | Get all users | `/all_users` |
| `/all_blocked` | Get blocked users | `/all_blocked` |
| `/all_unblocked` | Get unblocked users | `/all_unblocked` |

### System Management

| Command | Description | Example |
|---------|-------------|---------|
| `/run_time` | Show bot runtime | `/run_time` |
| `/log` | Get user logs | `/log 123456789` |
| `/broadcast` | Broadcast message | `/broadcast` (reply to message) |
| `/reload_cache` | Reload Firebase cache | `/reload_cache` |
| `/auto_cache` | Control auto cache | `/auto_cache 24` |

### Content Management

| Command | Description | Example |
|---------|-------------|---------|
| `/update_porn` | Update porn detection lists | `/update_porn` |
| `/reload_porn` | Reload porn detection cache | `/reload_porn` |
| `/check_porn` | Check URL for NSFW content with detailed explanation | `/check_porn https://example.com/video` |
| `/uncache` | Clear subtitle cache | `/uncache` |

### Language Management

| Command | Description | Example |
|---------|-------------|---------|
| `/lang` | 🌍 Show language selection menu | `/lang` |
| `/lang <code>` | 🌍 Set bot language | `/lang ru` |

### System Monitoring

| Command | Description | Example |
|---------|-------------|---------|
| `/flood_wait` | Show flood wait settings | `/flood_wait` |
| `/nsfw` | NSFW content settings | `/nsfw on` |
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

## Porn Detection Management

The bot includes advanced porn detection capabilities with configurable domain and keyword lists. Admins can manage these lists using dedicated commands.

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
   - Useful for sites that might have adult content but aren't primarily porn sites

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

### Dashboard auto-start service

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

---

### /vid range shortcut
- Use range before URL and it will be transformed to playlist indices:
  - `/vid 3-7 https://youtube.com/playlist?list=...` → `/vid https://youtube.com/playlist?list=...*3*7`

---

## Inline search helper (/search)

Use this command to quickly activate inline search via `@vid`.

- 📱 Mobile: tap the button shown by `/search`. It opens your chat with prefilled `@vid` and a zero‑width space. Add your query after `@vid`.
- 💻 PC/Desktop: inline deep-linking cannot prefill reliably. Type manually in any chat:
  - `@vid Your_Search_Query`

Notes:
- Desktop Telegram does not always send `/start` payloads from links repeatedly; avoid relying on `https://t.me/<bot>?start=...` for inline prefill.
- The bot's `/search` shows only working options and a concise manual hint.

---

## 🔧 Troubleshooting

### Common Issues

#### Bot Doesn't Start

**Symptoms:** Bot fails to start or crashes immediately

**Solutions:**
1. Check all required fields in `config.py`
2. Verify API credentials are correct
3. Ensure channels are set up and bot has admin permissions
4. Check Firebase configuration and credentials
5. Verify Python version (3.10+ required)

#### Cookie Download Fails

**Symptoms:** Cookie download fails or validation errors

**Solutions:**
1. Verify cookie URLs are accessible via HTTPS
2. Check file size is under 100KB
3. Ensure files are in Netscape cookie format
4. Test URLs in browser to confirm they work
5. Check proxy settings if using proxy

#### YouTube Videos Fail to Download

**Symptoms:** YouTube videos fail with authentication errors

**Solutions:**
1. Run `/check_cookie` to verify YouTube cookies
2. Use `/cookie youtube` to get fresh cookies
3. Check if video is age-restricted or private
4. Verify yt-dlp is properly installed and up to date
5. Try PO Token Provider setup for bypass

#### Firebase Connection Errors

**Symptoms:** Firebase authentication or database errors

**Solutions:**
1. Verify Firebase project is set up correctly
2. Check authentication credentials
3. Ensure Realtime Database rules allow read/write access
4. Verify database URL is correct
5. Check network connectivity

#### Channel Subscription Issues

**Symptoms:** Users can't access bot features

**Solutions:**
1. Ensure bot is admin in subscription channel
2. Check channel invite link is valid
3. Verify channel ID format (should start with -100)
4. Test channel access manually
5. Check bot permissions in channels

#### Language Issues

**Symptoms:** Bot interface not in selected language

**Solutions:**
1. Check if language file exists in `CONFIG/LANGUAGES/`
2. Verify language code is supported (en, ru, ar, in)
3. Use `/lang` command to reset language
4. Check user's `lang.txt` file in user directory
5. Restart bot if language files were updated

#### NSFW Detection Issues

**Symptoms:** NSFW content not being detected or filtered

**Solutions:**
1. Run `/update_porn` to update detection lists
2. Check `TXT/porn_domains.txt` and `TXT/porn_keywords.txt` files
3. Use `/reload_porn` to refresh detection cache
4. Test with `/check_porn <url>` command
5. Verify NSFW settings with `/nsfw` command

#### Flood Wait Issues

**Symptoms:** Bot stops responding due to rate limits

**Solutions:**
1. Wait for the specified flood wait period
2. Check bot logs for flood wait notifications
3. Use `/flood_wait` command to check settings
4. Consider reducing bot usage frequency
5. Check if multiple instances are running

### Getting Help

If you encounter issues:

1. **Check Logs**: Review bot logs for error messages
2. **Verify Configuration**: Ensure all config fields are correct
3. **Test Components**: Test individual components (cookies, Firebase, channels)
4. **GitHub Issues**: Check [GitHub Issues](https://github.com/chelaxian/tg-ytdlp-bot/issues) for similar problems
5. **Create Issue**: Create a new issue with detailed error information and logs

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/tg-ytdlp-bot.git
cd tg-ytdlp-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make your changes and test
python3 magic.py
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Original Author**: [upekshaip](https://github.com/upekshaip)
- **Main Developer and Contrubutor**: [chelaxian](https://github.com/chelaxian)
- **Telegram Bot's Admin**: [@IIlIlIlIIIlllIIlIIlIllIIllIlIIIl](https://t.me/IIlIlIlIIIlllIIlIIlIllIIllIlIIIl)
- **yt-dlp**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video extraction
- **gallery-dl**: [gallery-dl](https://github.com/mikf/gallery-dl) for image extraction
- **PyroTGFork**: [PyroTGFork](https://telegramplayground.github.io/pyrogram/) for Telegram API

---

## 📈 Statistics dashboard (port 5555)

We provide a separate FastAPI service with a multi-tab UI and REST API that shows key bot metrics in real time without constantly hitting Firebase.

### How to run

```bash
pip install -r requirements.txt           # make sure fastapi/uvicorn are installed
./venv/bin/python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port 5555 --reload
```

After starting, open `http://<your-host>:5555`. The dashboard does not start automatically with the bot, so you may want to wrap this command into a dedicated systemd unit or Docker service.

### What it shows

- Active users “right now” (based on `Config.STATS_ACTIVE_TIMEOUT`), their links, and quick ban via ❌ button.
- Top downloads by day/week/month/all-time, top countries, gender and age groups (heuristics based on Telegram data).
- Popular domains, NSFW sources, playlist lovers, and heavy NSFW consumers.
- “Persistent” users who send ≥10 URLs per day for 7 days in a row.
- Channel join/leave log for the last 48 hours and a list of banned users with ✅ unban button.

On each tab with long lists, the top‑10 items are displayed with a “Show all” button.

### Where the data comes from

- The base snapshot is read from local `dump.json`, which is already refreshed by `DATABASE/download_firebase.py`.
- Hooks in `DATABASE/firebase_init.py` and `HELPERS/logger.py`, plus the `StatsAwareDBAdapter` proxy, intercept all DB writes and update the in‑memory cache without extra REST calls.
- User information is enriched via Telegram Bot API (`getChat`) with a local cache, and instant data is taken directly from incoming `message` objects.

### REST API

The UI uses simple JSON endpoints (`/api/active-users`, `/api/top-downloaders`, `/api/block-user`, `/api/channel-events`, etc.), so you can reuse the same statistics in external monitoring tools, alerts, or bots without rendering HTML.

### Configuration and usage of the dashboard

1. **Update the config.** In `CONFIG/config.py`, set `DASHBOARD_PORT`, `DASHBOARD_USERNAME`, and `DASHBOARD_PASSWORD`. In Docker you can also override them via environment variables. Values are read at runtime, but you typically rebuild/restart the container or service once after changes.
2. **Start the service.** On bare‑metal use `./venv/bin/python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port $DASHBOARD_PORT`. In Docker add a separate service or wire the dashboard into an existing compose file.
3. **Secure access.** Put the dashboard behind HTTPS (Nginx/Traefik) and an IP allowlist if it is exposed to the internet. For local‑only use, prefer SSH port forwarding instead of public exposure.
4. **Working in the UI.**
   - The **Active Users** tab shows live sessions; the ❌ button instantly blocks a user.  
   - **Top Downloads / Domains** helps you spot abuse patterns.  
   - **Channel Events / Blocked Users** lets you manage subscriptions and the ban‑list without touching the database directly.
5. **Debugging.** If the dashboard stops responding, check `journalctl -u tg-ytdlp-dashboard -f` (or Docker logs) and verify that `DATABASE/download_firebase.py` is still updating `dump.json`.

Add a dedicated systemd unit (see `etc/systemd/system/tg-ytdlp-bot.service` as a reference) or a Docker healthcheck so the dashboard is automatically restarted after host or container restarts.

---

## 💖 Support

If you find this project helpful, please consider:

- ⭐ **Starring** the repository
- 🍕 **Buying a coffee** for original author on [BuyMeACoffee](https://buymeacoffee.com/upekshaip)
- 🐛 **Reporting bugs** and suggesting features
- 📢 **Sharing** with others who might find it useful

---

**Made with ❤️ by the tg-ytdlp-bot community** 

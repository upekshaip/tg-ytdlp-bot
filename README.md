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
- 🌍 **Multi-Language Support**: 4 languages - 🇺🇸 English, 🇷🇺 Russian, 🇸🇦 العربية, 🇮🇳 हिन्दी
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

## 📚 Documentation

### Getting Started
- [Overview](docs/getting-started/overview.md) - Introduction to the bot and its features
- [Installation](docs/getting-started/installation.md) - How to install and set up the bot

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
| 🇷🇺 Russian | `ru` | Russian | 🇷🇺 |
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

### Advanced Topics
- [Advanced Features](docs/advanced/advanced-features.md) - Advanced functionality and features
- [Troubleshooting](docs/advanced/troubleshooting.md) - Common issues and solutions

### Development and Contributing
- [Contributing](docs/development/contributing.md) - How to contribute to the project

### Additional Information
- [Support](docs/misc/support.md) - Support information and acknowledgments

## 💖 Support

If you find this project helpful, please consider:

- ⭐ **Starring** the repository
- 🍕 **Buying a coffee** for original author on [BuyMeACoffee](https://buymeacoffee.com/upekshaip)
- 🐛 **Reporting bugs** and suggesting features
- 📢 **Sharing** with others who might find it useful

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Author**: [upekshaip](https://github.com/upekshaip)
- **Main Developer and Contributor**: [chelaxian](https://github.com/chelaxian)
- **yt-dlp**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video extraction
- **gallery-dl**: [gallery-dl](https://github.com/mikf/gallery-dl) for image extraction
- **PyroTGFork**: [PyroTGFork](https://telegramplayground.github.io/pyrogram/) for Telegram API

---

**Made with ❤️ by the tg-ytdlp-bot community**
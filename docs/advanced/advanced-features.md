# Advanced Features

## Table of Contents
- [Always Ask Menu](#🎬-always-ask-menu)
- [Advanced Cookie Management](#🍪-advanced-cookie-management)
- [Proxy Support](#🌐-proxy-support)
- [Direct Link Extraction](#🔗-direct-link-extraction)
- [Tag System](#🏷️-tag-system)
- [Image Download Support](#🖼️-image-download-support)
- [Custom yt-dlp Arguments](#⚙️-custom-yt-dlp-arguments-args)
- [Format List Command](#📋-format-list-command-list)
- [PO Token Provider](#🚀-po-token-provider-youtube-bypass)
- [Proxy Download Support](#proxy-download-support-proxy)
- [Enhanced Direct Link Extraction](#enhanced-direct-link-extraction-link)
- [Enhanced Format Selection](#enhanced-format-selection-format)
- [Advanced Command Arguments](#advanced-command-arguments)
- [Always Ask Menu](#always-ask-menu)
- [Intelligent Subtitle Handling](#intelligent-subtitle-handling)
- [Enhanced Cookie Management](#enhanced-cookie-management)
- [Reply Keyboard Management](#reply-keyboard-management)
- [NSFW Content Management](#🔞-nsfw-content-management)
- [Flood Wait Protection](#⏱️-flood-wait-protection)
- [Improved Error Handling](#improved-error-handling)
- [Paid posts and Group Mode](#paid-posts-telegram-stars-and-group-mode)
- [Statistics Dashboard](#📈-statistics-dashboard-port-5555)

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

## Paid posts (Telegram Stars) and Group Mode

- **Paid posts (Stars)**: The bot can send paid posts via Telegram Stars for NSFW content in private chats.

For more information about NSFW management, see the [User Commands documentation](../commands/user-commands.md#advanced-commands) and [Admin Commands documentation](../commands/admin-commands.md).

Note: You can tune exact limit values and behavior in `CONFIG/limits.py` and `CONFIG/config.py` according to your hosting and needs.
  - The cover is prepared automatically (320×320 with padding) to meet Telegram requirements.
  - Price is configured in `CONFIG/limits.py` via `NSFW_STAR_COST`.
  - For channels/groups, relay is supported (when the bot is added as an admin); paid media is cached properly.

- **Adding the bot to a group**: Add the bot as an admin to your group/supergroup to use commands inside the chat.
  - In group mode, extended limits apply: **limits are doubled** (sizes/queues), reducing fallbacks to document mode for large files.
  - All other features (formats, proxy, cookies, direct links) work the same as in private chats.
  - NSFW content has no Telegram Stars cost in groups

Note: You can tune exact limit values and behavior in `CONFIG/limits.py` and `CONFIG/config.py` according to your hosting and needs.

## 📈 Statistics dashboard (port 5555)

We provide a separate FastAPI service with a multi-tab UI and REST API that shows key bot metrics in real time without constantly hitting Firebase.

For more information about dashboard configuration, see the [Configuration documentation](../configuration/configuration.md#dashboard-auto-start-service).

### How to run

```bash
pip install -r requirements.txt           # make sure fastapi/uvicorn are installed
./venv/bin/python -m uvicorn web.dashboard_app:app --host 0.0.0.0 --port 5555 --reload
```

After starting, open `http://<your-host>:5555`. The dashboard does not start automatically with the bot, so you may want to wrap this command into a dedicated systemd unit or Docker service.

### What it shows

- Active users "right now" (based on `Config.STATS_ACTIVE_TIMEOUT`), their links, and quick ban via ❌ button.
- Top downloads by day/week/month/all-time, top countries, gender and age groups (heuristics based on Telegram data).
- Popular domains, NSFW sources, playlist lovers, and heavy NSFW consumers.
- "Persistent" users who send ≥10 URLs per day for 7 days in a row.
- Channel join/leave log for the last 48 hours and a list of banned users with ✅ unban button.

On each tab with long lists, the top‑10 items are displayed with a "Show all" button.

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
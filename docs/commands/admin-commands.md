# Admin Commands

## Table of Contents
- [User Management](#user-management)
- [System Management](#system-management)
- [Content Management](#content-management)
- [Language Management](#language-management)
- [System Monitoring](#system-monitoring)
- [Auto Cache](#auto-cache--how-it-works-onoffn)
- [Porn Detection Management](#porn-detection-management)
  - [Porn Detection Commands](#porn-detection-commands)

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
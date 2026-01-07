# User Commands

## Table of Contents
- [Basic Commands](#basic-commands)
- [Download Commands](#download-commands)
- [Format & Quality Commands](#format--quality-commands)
- [Subtitle Commands](#subtitle-commands)
- [Cookie Commands](#cookie-commands)
- [Advanced Commands](#advanced-commands)
- [Command Arguments](#command-arguments)
- [Multi-Language Support](#multi-language-support)
- [Link Command Pattern](#link-command-pattern-spec)
- [Tags System](#tags-system-navigation-tags)
- [/tags Command](#tags-command)
- [/vid range shortcut](#vid-range-shortcut)
- [Inline search helper](#inline-search-helper-search)

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

## Command Arguments

Many commands support direct arguments for quick configuration:

For more information about advanced configuration options, see the [Configuration documentation](../configuration/configuration.md).

For more information about advanced features, see the [Advanced Features documentation](../advanced/advanced-features.md).

### Format with Quality
```bash
/format 720    # Set to 720p or lower
/format 4k     # Set to 4K or lower
/format best   # Set to best quality
```

### Keyboard Layouts
```bash
/keyboard off   # Hide keyboard
/keyboard 1x3   # Single row
/keyboard 2x3   # Double row (default)
/keyboard full  # Emoji keyboard
```

### Split Sizes
```bash
/split 100mb   # 100MB (minimum)
/split 500mb   # 500MB
/split 1gb     # 1GB
/split 2gb     # 2GB (maximum)
```

### Subtitle Languages
```bash
/subs off       # Disable subtitles
/subs ru        # Russian subtitles
/subs en auto   # English with auto-translate
```

### Cookie Services
```bash
/cookie youtube  # YouTube cookies
/cookie tiktok   # TikTok cookies
/cookie x        # Twitter/X cookies
```

### Language Settings
```bash
/lang en         # 🇺🇸 Set to English
/lang ru         # 🇷🇺 Set to Russian
/lang ar         # 🇸🇦 Set to Arabic
/lang in         # 🇮🇳 Set to Hindi
```

### Clean Specific Settings
```bash
/clean args      # Clear yt-dlp arguments
/clean nsfw      # Clear NSFW settings
/clean proxy     # Clear proxy settings
/clean flood_wait # Clear flood wait settings
```

### Format with ID Selection
```bash
/format id 134   # Download specific format ID (with audio)
/format id 401   # Download specific format ID (with audio)
```

### List Available Formats
```bash
/list https://youtube.com/watch?v=...  # Show all available formats
```

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

## /vid range shortcut
- Use range before URL and it will be transformed to playlist indices:
  - `/vid 3-7 https://youtube.com/playlist?list=...` → `/vid https://youtube.com/playlist?list=...*3*7`

## Inline search helper (/search)

Use this command to quickly activate inline search via `@vid`.

- 📱 Mobile: tap the button shown by `/search`. It opens your chat with prefilled `@vid` and a zero‑width space. Add your query after `@vid`.
- 💻 PC/Desktop: inline deep-linking cannot prefill reliably. Type manually in any chat:
  - `@vid Your_Search_Query`

Notes:
- Desktop Telegram does not always send `/start` payloads from links repeatedly; avoid relying on `https://t.me/<bot>?start=...` for inline prefill.
- The bot's `/search` shows only working options and a concise manual hint.
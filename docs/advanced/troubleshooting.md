# Troubleshooting

## Table of Contents
- [Common Issues](#common-issues)
  - [Bot Doesn't Start](#bot-doesnt-start)
  - [Cookie Download Fails](#cookie-download-fails)
  - [YouTube Videos Fail to Download](#youtube-videos-fail-to-download)
  - [Firebase Connection Errors](#firebase-connection-errors)
  - [Channel Subscription Issues](#channel-subscription-issues)
  - [Language Issues](#language-issues)
  - [NSFW Detection Issues](#nsfw-detection-issues)
  - [Flood Wait Issues](#flood-wait-issues)
- [Getting Help](#getting-help)

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
2. **Verify Configuration**: Ensure all config fields are correct - see the [Configuration documentation](../configuration/configuration.md)
3. **Test Components**: Test individual components (cookies, Firebase, channels)
4. **GitHub Issues**: Check [GitHub Issues](https://github.com/chelaxian/tg-ytdlp-bot/issues) for similar problems
5. **Create Issue**: Create a new issue with detailed error information and logs

For more information about common issues, see the [Installation documentation](../getting-started/installation.md) and [Configuration documentation](../configuration/configuration.md).
from CONFIG.messages import Messages

class LoggerMsg(object):
    # Generic user/admin/access
    ACCESS_DENIED_ADMIN = Messages.LOGGER_ACCESS_DENIED_ADMIN_MSG
    WELCOME_MASTER = Messages.LOGGER_WELCOME_MASTER_MSG

    # URL Extractor / start logs
    USER_STARTED_BOT = "{chat_id} - user started the bot"
    HELP_SENT_TO_USER = "Send help txt to user"
    ADD_BOT_TO_GROUP_SENT = "Send add_bot_to_group txt to user"

    # Image command logs
    IMG_HELP_SHOWN = "Showed /img help"
    INVALID_URL_PROVIDED = "Invalid URL provided: {url}"
    REPOSTED_CACHED_ALBUMS = "Reposted {count} cached albums for {url}"
    FAILED_ANALYZE_IMAGE = "Failed to analyze image URL: {url}"
    STREAMED_AND_SENT_MEDIA = "Streamed and sent {total_sent} media: {url}"
    IMAGE_COMMAND_ERROR = "Error in image command: {url}, error: {error}"

    # Search helper logs
    SEARCH_HELPER_OPENED = "User {user_id} opened search helper"
    SEARCH_HELPER_CLOSED = "User {user_id} closed search command"
    SEARCH_CALLBACK_ERROR = "Error in search callback handler: {error}"

    # Settings menu logs
    SETTINGS_OPENED = "Opened /settings menu"

    # Direct link flows
    DIRECT_LINK_EXTRACTED = "Direct link extracted via {source} for user {user_id} from {url}"
    DIRECT_LINK_FAILED = "Failed to extract direct link via {source} for user {user_id} from {url}: {error}"

    # Cache and sends
    PLAYLIST_VIDEOS_SENT_FROM_CACHE = "Playlist videos sent from cache (quality={quality}) to user {user_id}"
    VIDEO_SENT_FROM_CACHE = "Video sent from cache (quality={quality}) to user {user_id}"
    PLAYLIST_AUDIO_SENT_FROM_CACHE = "Playlist audio sent from cache (quality={quality}) to user{user_id}"
    AUDIO_SENT_FROM_CACHE = "Audio sent from cache (quality={quality}) to user{user_id}"

    # Limits and errors
    SIZE_LIMIT_EXCEEDED = Messages.LOGGER_SIZE_LIMIT_EXCEEDED_MSG
    DOWNLOAD_ERROR_GENERIC = Messages.LOGGER_DOWNLOAD_ERROR_GENERIC_MSG
    DOWNLOAD_TIMEOUT_LOG = "Download cancelled due to timeout"


# Messages Configuration
import sys
import os

# Add the LANGUAGES directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'LANGUAGES'))

try:
    from language_router import get_messages, get_message, set_user_language
except ImportError:
    # Fallback if language router is not available
    def get_messages(user_id=None, language_code=None):
        return {}
    def get_message(message_key, user_id=None, language_code=None):
        return f"[{message_key}]"
    def set_user_language(user_id, language_code):
        return False

class Messages(object):
    def __init__(self, user_id=None, language_code=None):
        """
        Initialize Messages with user-specific language
        """
        self.user_id = user_id
        self.language_code = language_code
        self._messages = get_messages(user_id, language_code)
    
    def __getattr__(self, name):
        """
        Get message by name from user's selected language ONLY
        """
        if name.startswith('_'):
            return super().__getattribute__(name)
        
        # STRICT: Only use language-specific messages, NO fallback to English
        if hasattr(self, '_messages') and self._messages and name in self._messages:
            value = self._messages[name]
            if isinstance(value, str):
                return _format_message(value)
            return value
        
        # If message not found in selected language, return placeholder
        return f"[{name}]"

    # All messages are now loaded dynamically from language-specific files
    # through the language router. No static variables needed here.

# -------------------------------------------------------------------------------------------------
# Runtime formatting helpers
# -------------------------------------------------------------------------------------------------

class _SafeFormatDict(dict):
    def __missing__(self, key):
        # Preserve placeholders we don't know how to fill yet
        return "{" + str(key) + "}"


def _get_message_placeholders():
    """
    Return a dict of placeholders used by translations.
    Must not import Config at module import time (CONFIG/_config.py imports this module).
    """
    defaults = {
        # Defaults preserve original upstream branding unless overridden in Config.
        "required_channel": "@tg_ytdlp",
        "managed_by": "@iilililiiillliiliililliilliliiil",
        "credits_bots": "🇮🇹 @tgytdlp_it_bot\n🇦🇪 @tgytdlp_uae_bot\n🇬🇧 @tgytdlp_uk_bot\n🇫🇷 @tgytdlp_fr_bot",
    }

    try:
        from CONFIG.config import Config  # local import to avoid circular import at startup

        required_channel = getattr(Config, "REQUIRED_CHANNEL_MENTION", None)
        if not required_channel:
            # Best-effort derive from SUBSCRIBE_CHANNEL_URL if it looks like a t.me link
            url = getattr(Config, "SUBSCRIBE_CHANNEL_URL", "") or ""
            if "t.me/" in url:
                tail = url.split("t.me/", 1)[1].strip("/")
                if tail and not tail.startswith("+"):
                    required_channel = "@" + tail.lstrip("@")
        if required_channel:
            defaults["required_channel"] = required_channel

        defaults["managed_by"] = getattr(Config, "CREDITS_MANAGED_BY", defaults["managed_by"]) or defaults["managed_by"]
        defaults["credits_bots"] = getattr(Config, "CREDITS_BOTS", defaults["credits_bots"]) or defaults["credits_bots"]
    except Exception:
        pass

    return defaults


def _format_message(template: str) -> str:
    try:
        return template.format_map(_SafeFormatDict(_get_message_placeholders()))
    except Exception:
        return template

# Global function to get Messages instance with user language
def get_messages_instance(user_id=None, language_code=None):
    """
    Get Messages instance with user-specific language
    """
    return Messages(user_id, language_code)

# GLOBAL PROTECTION: Safe function that NEVER fails
def safe_get_messages(user_id=None, language_code=None):
    """
    SAFE function that NEVER raises NameError for 'messages'
    This function is GUARANTEED to return a Messages object
    """
    try:
        return get_messages_instance(user_id, language_code)
    except Exception:
        # If everything fails, return a minimal Messages object
        return Messages(None, None)

# GLOBAL PROTECTION: Safe function for any context
def safe_messages(user_id=None):
    """
    ULTRA-SAFE function that works in ANY context
    """
    try:
        return get_messages_instance(user_id)
    except:
        try:
            return get_messages_instance(None)
        except:
            # Last resort - return a dummy object
            class DummyMessages:
                def __getattr__(self, name):
                    return f"[{name}]"
            return DummyMessages()

# Backward compatibility - create default instance with English language
messages = Messages(None, 'en')

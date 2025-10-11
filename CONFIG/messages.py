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
            return self._messages[name]
        
        # If message not found in selected language, return placeholder
        return f"[{name}]"
    
    # All messages are now loaded dynamically from language-specific files
    # through the language router. No static variables needed here.

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
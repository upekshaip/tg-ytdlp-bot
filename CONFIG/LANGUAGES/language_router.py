"""
Language Router for Multi-language Support
Handles dynamic loading of messages based on user's selected language
"""

import os
import sys
from typing import Dict, Any, Optional

# Add the parent directory to the path to import CONFIG
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LanguageRouter:
    """Router for handling multi-language message loading"""
    
    def __init__(self):
        self.languages_dir = os.path.dirname(os.path.abspath(__file__))
        self.available_languages = {
            'en': 'messages_EN.py',
            'ru': 'messages_RU.py', 
            'ar': 'messages_AR.py',
            'in': 'messages_IN.py'
        }
        self.default_language = 'en'
        self._cached_messages = {}
        
    def get_user_language(self, user_id: int) -> str:
        """
        Get user's selected language from database/storage
        Returns default language if not set
        """
        # TODO: Implement database lookup for user language preference
        # For now, return default language
        return self.default_language
    
    def set_user_language(self, user_id: int, language_code: str) -> bool:
        """
        Set user's language preference
        Returns True if successful, False if language not supported
        """
        if language_code not in self.available_languages:
            return False
            
        # TODO: Implement database storage for user language preference
        # For now, just return True
        return True
    
    def load_messages(self, language_code: str = None) -> Dict[str, Any]:
        """
        Load messages for specified language
        Falls back to default language if specified language not found
        """
        if language_code is None:
            language_code = self.default_language
            
        # Check if already cached
        if language_code in self._cached_messages:
            return self._cached_messages[language_code]
        
        # Validate language code
        if language_code not in self.available_languages:
            language_code = self.default_language
            
        # Load messages file
        messages_file = self.available_languages[language_code]
        messages_path = os.path.join(self.languages_dir, messages_file)
        
        try:
            # Import the messages module
            module_name = f"CONFIG.LANGUAGES.{messages_file[:-3]}"  # Remove .py extension
            
            # Clear any existing module from cache
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Add the languages directory to Python path temporarily
            if self.languages_dir not in sys.path:
                sys.path.insert(0, self.languages_dir)
            
            # Import the module
            messages_module = __import__(module_name, fromlist=['Messages'])
            messages_class = getattr(messages_module, 'Messages')
            
            # Create instance and get all attributes
            messages_instance = messages_class()
            messages_dict = {}
            
            for attr_name in dir(messages_instance):
                if not attr_name.startswith('_'):
                    attr_value = getattr(messages_instance, attr_name)
                    messages_dict[attr_name] = attr_value
            
            # Cache the messages
            self._cached_messages[language_code] = messages_dict
            
            return messages_dict
            
        except Exception as e:
            print(f"Error loading messages for language {language_code}: {e}")
            # Fall back to default language
            if language_code != self.default_language:
                return self.load_messages(self.default_language)
            return {}
    
    def get_message(self, message_key: str, user_id: int = None, language_code: str = None) -> str:
        """
        Get a specific message for user or language
        """
        if language_code is None and user_id is not None:
            language_code = self.get_user_language(user_id)
        elif language_code is None:
            language_code = self.default_language
            
        messages = self.load_messages(language_code)
        return messages.get(message_key, f"[{message_key}]")
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get list of available languages with their display names
        """
        return {
            'en': '🇺🇸 English',
            'ru': '🇷🇺 Русский', 
            'ar': '🇸🇦 العربية',
            'in': '🇮🇳 हिन्दी'
        }
    
    def clear_cache(self):
        """Clear cached messages"""
        self._cached_messages.clear()

# Global instance
language_router = LanguageRouter()

def get_messages(user_id: int = None, language_code: str = None) -> Dict[str, Any]:
    """
    Convenience function to get messages for user or language
    """
    if language_code is None and user_id is not None:
        language_code = language_router.get_user_language(user_id)
    elif language_code is None:
        language_code = language_router.default_language
        
    return language_router.load_messages(language_code)

def get_message(message_key: str, user_id: int = None, language_code: str = None) -> str:
    """
    Convenience function to get a specific message
    """
    return language_router.get_message(message_key, user_id, language_code)

def set_user_language(user_id: int, language_code: str) -> bool:
    """
    Convenience function to set user language
    """
    return language_router.set_user_language(user_id, language_code)

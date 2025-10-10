"""
Language Router for Multi-language Support
Handles dynamic loading of messages based on user's selected language
"""

import os
import sys
import ast
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
        Get user's selected language from lang.txt file in user directory
        Returns default language if not set
        """
        try:
            user_dir = f'./users/{str(user_id)}'
            lang_file = os.path.join(user_dir, 'lang.txt')
            
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_code = f.read().strip()
                    if lang_code in self.available_languages:
                        return lang_code
        except Exception as e:
            print(f"Error reading user language for {user_id}: {e}")
        
        return self.default_language
    
    def set_user_language(self, user_id: int, language_code: str) -> bool:
        """
        Set user's language preference by saving to lang.txt file
        Returns True if successful, False if language not supported
        """
        if language_code not in self.available_languages:
            return False
            
        try:
            # Create user directory if it doesn't exist
            user_dir = f'./users/{str(user_id)}'
            os.makedirs(user_dir, exist_ok=True)
            
            # Save language preference to lang.txt
            lang_file = os.path.join(user_dir, 'lang.txt')
            with open(lang_file, 'w', encoding='utf-8') as f:
                f.write(language_code)
            
            # Clear cache for this user to force reload with new language
            if language_code in self._cached_messages:
                del self._cached_messages[language_code]
            
            return True
        except Exception as e:
            print(f"Error saving user language for {user_id}: {e}")
            return False
    
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
            # Load messages using import method (more reliable)
            messages_dict = self._load_messages_with_import(messages_path)
            
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
    
    def _load_messages_with_ast(self, messages_path: str) -> Dict[str, Any]:
        """
        Load messages using AST parsing to get all variables including duplicates
        This ensures we get the last value of duplicate variables
        """
        try:
            with open(messages_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the file as AST
            tree = ast.parse(content)
            
            # Find the Messages class
            messages_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == 'Messages':
                    messages_class = node
                    break
            
            if not messages_class:
                return {}
            
            # Create a namespace to execute the class
            namespace = {}
            
            # Execute the class definition to get all variables
            # We need to handle the class body manually to preserve duplicates
            messages_dict = {}
            
            for node in messages_class.body:
                if isinstance(node, ast.Assign):
                    # Handle assignment nodes
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Evaluate the value
                            try:
                                # Convert AST node to Python value
                                value = ast.literal_eval(node.value)
                                messages_dict[target.id] = value
                            except (ValueError, TypeError):
                                # If literal_eval fails, try to evaluate as string
                                try:
                                    # For complex expressions, we'll need to evaluate them
                                    # This is a simplified approach
                                    if isinstance(node.value, ast.Str):
                                        messages_dict[target.id] = node.value.s
                                    elif isinstance(node.value, ast.Constant):
                                        messages_dict[target.id] = node.value.value
                                    elif isinstance(node.value, ast.JoinedStr):
                                        # Handle f-strings
                                        messages_dict[target.id] = self._evaluate_joined_str(node.value)
                                    elif isinstance(node.value, ast.BinOp):
                                        # Handle binary operations
                                        messages_dict[target.id] = self._evaluate_binop(node.value)
                                    elif isinstance(node.value, ast.List):
                                        # Handle lists
                                        messages_dict[target.id] = self._evaluate_list(node.value)
                                    elif isinstance(node.value, ast.Tuple):
                                        # Handle tuples
                                        messages_dict[target.id] = self._evaluate_tuple(node.value)
                                    else:
                                        # For other complex expressions, try to convert to string
                                        messages_dict[target.id] = str(ast.unparse(node.value))
                                except:
                                    pass
            
            # If AST method didn't work well, fall back to import method
            if len(messages_dict) < 1000:  # If we didn't get enough variables
                return self._load_messages_with_import(messages_path)
            
            return messages_dict
            
        except Exception as e:
            print(f"Error in AST loading: {e}")
            # Fall back to import method
            return self._load_messages_with_import(messages_path)
    
    def _load_messages_with_import(self, messages_path: str) -> Dict[str, Any]:
        """
        Fallback method using import to load messages
        """
        try:
            # Get the module name from the file path
            messages_file = os.path.basename(messages_path)
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
            
            # Get all attributes from the instance
            for attr_name in dir(messages_instance):
                if not attr_name.startswith('_'):
                    attr_value = getattr(messages_instance, attr_name)
                    messages_dict[attr_name] = attr_value
            
            return messages_dict
            
        except Exception as e:
            print(f"Error in import loading: {e}")
            return {}
    
    def _evaluate_joined_str(self, node: ast.JoinedStr) -> str:
        """Evaluate f-string (JoinedStr) nodes"""
        try:
            result = ""
            for value in node.values:
                if isinstance(value, ast.Str):
                    result += value.s
                elif isinstance(value, ast.Constant):
                    result += str(value.value)
                elif isinstance(value, ast.FormattedValue):
                    # For f-string expressions, we'll just use the string representation
                    result += f"{{{ast.unparse(value.value)}}}"
                else:
                    result += str(ast.unparse(value))
            return result
        except:
            return str(ast.unparse(node))
    
    def _evaluate_binop(self, node: ast.BinOp) -> str:
        """Evaluate binary operation nodes"""
        try:
            return str(ast.unparse(node))
        except:
            return ""
    
    def _evaluate_list(self, node: ast.List) -> list:
        """Evaluate list nodes"""
        try:
            result = []
            for elt in node.elts:
                if isinstance(elt, ast.Str):
                    result.append(elt.s)
                elif isinstance(elt, ast.Constant):
                    result.append(elt.value)
                else:
                    result.append(str(ast.unparse(elt)))
            return result
        except:
            return []
    
    def _evaluate_tuple(self, node: ast.Tuple) -> tuple:
        """Evaluate tuple nodes"""
        try:
            result = []
            for elt in node.elts:
                if isinstance(elt, ast.Str):
                    result.append(elt.s)
                elif isinstance(elt, ast.Constant):
                    result.append(elt.value)
                else:
                    result.append(str(ast.unparse(elt)))
            return tuple(result)
        except:
            return ()
    
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

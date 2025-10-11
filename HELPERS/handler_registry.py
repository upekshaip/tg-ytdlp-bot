# Handler Registry System
# This module provides a way to register handlers that will be applied when app is initialized

from HELPERS.app_instance import get_app_lazy
from CONFIG.messages import Messages, safe_get_messages

class HandlerRegistry:
    def __init__(self):
        messages = safe_get_messages(None)
        self.handlers = []
    
    def register(self, handler_type, filters=None):
        messages = safe_get_messages(None)
        """Register a handler to be applied when app is ready"""
        def decorator(func):
            messages = safe_get_messages(None)
            print(messages.HANDLER_REGISTERING_MSG.format(handler_type=handler_type, func_name=func.__name__))
            self.handlers.append((handler_type, filters, func))
            return func
        return decorator
    
    def apply_handlers(self, app):
        """Apply all registered handlers to the app"""
        for handler_type, filters, func in self.handlers:
            if handler_type == 'message':
                app.on_message(filters)(func)
            elif handler_type == 'callback_query':
                app.on_callback_query(filters)(func)
    
    def clear(self):
        """Clear all registered handlers"""
        self.handlers.clear()

# Global registry instance
registry = HandlerRegistry()

def on_message(filters=None):
    """Decorator for message handlers"""
    return registry.register('message', filters)

def on_callback_query(filters=None):
    """Decorator for callback query handlers"""
    return registry.register('callback_query', filters)

def apply_all_handlers(app):
    """Apply all registered handlers to the app"""
    registry.apply_handlers(app) 
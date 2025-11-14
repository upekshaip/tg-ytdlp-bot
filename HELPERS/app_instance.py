# Global app instance
# This module provides a global app instance that can be imported by other modules

from CONFIG.messages import Messages, safe_get_messages

app = None

def set_app(app_instance):
    """Set the global app instance"""
    global app
    app = app_instance

def get_app():
    """Get the global app instance"""
    return app

def get_app_lazy():
    messages = safe_get_messages(None)
    """Get app instance with lazy loading - returns a proxy that will work when app is set"""
    class AppProxy:
        def __getattr__(self, name):
            messages = safe_get_messages(None)
            if app is None:
                raise RuntimeError(messages.APP_INSTANCE_NOT_INITIALIZED_MSG.format(name=name))
            return getattr(app, name)
    
    return AppProxy() 
# Global app instance
# This module provides a global app instance that can be imported by other modules

app = None

def set_app(app_instance):
    """Set the global app instance"""
    global app
    app = app_instance

def get_app():
    """Get the global app instance"""
    return app

def get_app_lazy():
    """Get app instance with lazy loading - returns a proxy that will work when app is set"""
    class AppProxy:
        def __getattr__(self, name):
            if app is None:
                raise RuntimeError(f"App not initialized yet. Cannot access {name}")
            return getattr(app, name)
    
    return AppProxy() 
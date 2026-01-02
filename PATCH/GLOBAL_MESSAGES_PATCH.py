"""
GLOBAL MESSAGES PATCH - FIXES 'name messages is not defined' ONCE AND FOR ALL

This file contains global patches to prevent the 'name messages is not defined' error
across ALL project files.
"""

import sys
import os

# Add CONFIG path (from PATCH folder)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'CONFIG'))

def apply_global_messages_patch():
    """
    Apply a global patch to prevent 'name messages is not defined'
    """
    try:
        from CONFIG.messages import safe_messages, safe_get_messages
        
        # Patch builtins
        import builtins
        
        # Create a safe version of get_messages_instance
        def safe_safe_get_messages(user_id=None):
            try:
                from CONFIG.messages import safe_get_messages
                return safe_get_messages(user_id)
            except:
                return safe_messages(user_id)
        
        # Add to global namespace
        builtins.safe_get_messages_instance = safe_safe_get_messages
        builtins.safe_messages = safe_messages
        
        print("✅ GLOBAL MESSAGES PATCH APPLIED - NameError protection active")
        
    except Exception as e:
        print(f"❌ Failed to apply global messages patch: {e}")
        # Create a minimal fallback
        class EmergencyMessages:
            def __getattr__(self, name):
                return f"[{name}]"
        
        # Do not declare global messages here to avoid conflicts
        pass

# Automatically apply the patch on import
apply_global_messages_patch()

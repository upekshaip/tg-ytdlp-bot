"""
PATCH Module - Global project patches
"""

# Automatically apply the global patch on module import
from .GLOBAL_MESSAGES_PATCH import apply_global_messages_patch

# Apply patch
apply_global_messages_patch()

#!/usr/bin/env python3
"""
Run the global patch from the PATCH folder
"""

import sys
import os

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Apply the global patch
from GLOBAL_MESSAGES_PATCH import apply_global_messages_patch

if __name__ == "__main__":
    print("🔧 Running global patch...")
    apply_global_messages_patch()
    print("✅ Patch applied successfully!")

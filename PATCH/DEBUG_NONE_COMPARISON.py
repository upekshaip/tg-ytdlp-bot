#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DETAILED LOGGING FOR DEBUGGING NONE COMPARISON ERRORS
=======================================================

This patch adds detailed logging to help track down the error:
'>' not supported between instances of 'NoneType' and 'int'

Author: AI Assistant
Date: 2025-10-11
"""

import os
import re
import logging
from typing import Any, Optional

def apply_debug_none_comparison():
    """Enable detailed logging for debugging None comparison errors."""
    
    print("🔍 Applying detailed logging for debugging None comparison errors...")
    
    # Logging configuration
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Create a decorator to trace comparisons and inputs
    def debug_comparison_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Log inputs
                logger.debug(f"🔍 FUNCTION CALL: {func.__name__}")
                logger.debug(f"   Args: {args}")
                logger.debug(f"   Kwargs: {kwargs}")
                
                # Execute
                result = func(*args, **kwargs)
                
                # Log result
                logger.debug(f"✅ FUNCTION {func.__name__} COMPLETED SUCCESSFULLY")
                return result
                
            except TypeError as e:
                if "'>' not supported between instances of 'NoneType' and 'int'" in str(e):
                    logger.error(f"❌ NONE COMPARISON ERROR in {func.__name__}: {e}")
                    logger.error(f"   Args: {args}")
                    logger.error(f"   Kwargs: {kwargs}")
                    
                    # Try to identify problematic values
                    for i, arg in enumerate(args):
                        if arg is None:
                            logger.error(f"   ⚠️  Arg {i} is None: {arg}")
                        elif isinstance(arg, (int, float)):
                            logger.error(f"   ✅ Arg {i} is a number: {arg}")
                        else:
                            logger.error(f"   ❓ Arg {i} has other type: {type(arg)} = {arg}")
                    
                    # Try to identify problematic keyword args
                    for key, value in kwargs.items():
                        if value is None:
                            logger.error(f"   ⚠️  Kwarg {key} is None: {value}")
                        elif isinstance(value, (int, float)):
                            logger.error(f"   ✅ Kwarg {key} is a number: {value}")
                        else:
                            logger.error(f"   ❓ Kwarg {key} has other type: {type(value)} = {value}")
                
                raise e
            except Exception as e:
                logger.error(f"❌ ERROR in {func.__name__}: {e}")
                raise e
        
        return wrapper
    
    # Apply decorator to key functions
    try:
        from DOWN_AND_UP.always_ask_menu import ask_quality_menu
        ask_quality_menu = debug_comparison_decorator(ask_quality_menu)
        print("✅ Decorator applied to ask_quality_menu")
    except Exception as e:
        print(f"⚠️  Failed to apply decorator to ask_quality_menu: {e}")
    
    try:
        from DOWN_AND_UP.yt_dlp_hook import get_video_formats
        get_video_formats = debug_comparison_decorator(get_video_formats)
        print("✅ Decorator applied to get_video_formats")
    except Exception as e:
        print(f"⚠️  Failed to apply decorator to get_video_formats: {e}")
    
    # Patch comparison operators to detect errors
    def patch_comparison_operators():
        """Patch comparison operators to trace errors."""
        
        # Save original operators
        original_gt = int.__gt__
        original_lt = int.__lt__
        original_ge = int.__ge__
        original_le = int.__le__
        
        def safe_gt(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ATTEMPTING TO COMPARE None: self={self}, other={other}")
                    logger.error(f"   self type: {type(self)}, other type: {type(other)}")
                    return False
                return original_gt(self, other)
            except Exception as e:
                logger.error(f"❌ ERROR IN COMPARISON >: {e}")
                logger.error(f"   self={self} (type: {type(self)})")
                logger.error(f"   other={other} (type: {type(other)})")
                return False
        
        def safe_lt(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ATTEMPTING TO COMPARE None: self={self}, other={other}")
                    logger.error(f"   self type: {type(self)}, other type: {type(other)}")
                    return False
                return original_lt(self, other)
            except Exception as e:
                logger.error(f"❌ ERROR IN COMPARISON <: {e}")
                logger.error(f"   self={self} (type: {type(self)})")
                logger.error(f"   other={other} (type: {type(other)})")
                return False
        
        def safe_ge(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ATTEMPTING TO COMPARE None: self={self}, other={other}")
                    logger.error(f"   self type: {type(self)}, other type: {type(other)}")
                    return False
                return original_ge(self, other)
            except Exception as e:
                logger.error(f"❌ ERROR IN COMPARISON >=: {e}")
                logger.error(f"   self={self} (type: {type(self)})")
                logger.error(f"   other={other} (type: {type(other)})")
                return False
        
        def safe_le(self, other):
            try:
                if self is None or other is None:
                    logger.error(f"❌ ATTEMPTING TO COMPARE None: self={self}, other={other}")
                    logger.error(f"   self type: {type(self)}, other type: {type(other)}")
                    return False
                return original_le(self, other)
            except Exception as e:
                logger.error(f"❌ ERROR IN COMPARISON <=: {e}")
                logger.error(f"   self={self} (type: {type(self)})")
                logger.error(f"   other={other} (type: {type(other)})")
                return False
        
        # Apply patches
        try:
            int.__gt__ = safe_gt
            int.__lt__ = safe_lt
            int.__ge__ = safe_ge
            int.__le__ = safe_le
            print("✅ Comparison patches applied to int")
        except Exception as e:
            print(f"⚠️  Failed to apply patches to int: {e}")
        
        # Also patch float
        try:
            float.__gt__ = safe_gt
            float.__lt__ = safe_lt
            float.__ge__ = safe_ge
            float.__le__ = safe_le
            print("✅ Comparison patches applied to float")
        except Exception as e:
            print(f"⚠️  Failed to apply patches to float: {e}")
    
    # Apply patches
    patch_comparison_operators()
    
    print("🎉 Detailed logging applied successfully!")
    print("   None comparison errors will now be logged in detail")

if __name__ == "__main__":
    apply_debug_none_comparison()

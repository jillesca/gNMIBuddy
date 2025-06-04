"""
Thread-related utility functions to handle Python 3.13 specific thread cleanup issues.

This module specifically addresses a known issue in Python 3.13 where thread cleanup
during program termination causes this error:
"TypeError: 'NoneType' object does not support the context manager protocol"

The error occurs in the __del__ method of the _DeleteDummyThreadOnDel class in threading.py,
which is triggered during garbage collection when thread-local storage has already been set to None.

https://github.com/python/cpython/issues/130522
"""

import atexit
import logging
import threading


def patch_threading_for_python_3_13():
    """
    Monkey patch the threading module to prevent NoneType errors on program exit in Python 3.13.

    This addresses the 'NoneType' object does not support context manager protocol error
    that occurs during threading cleanup in Python 3.13 when using ThreadPoolExecutor.

    The issue occurs specifically in the __del__ method of _DeleteDummyThreadOnDel when
    the _tlock attribute has been set to None during interpreter shutdown.
    """
    # Original __del__ method from threading.py
    original_del = threading._DeleteDummyThreadOnDel.__del__

    # Replacement __del__ method that handles the case when _tlock is None
    def safe_del(self):
        try:
            # If _tlock is None, this will fail gracefully
            if hasattr(self, "_tlock") and self._tlock is not None:
                original_del(self)
        except Exception:
            pass  # Suppress all exceptions in __del__

    # Replace the method
    threading._DeleteDummyThreadOnDel.__del__ = safe_del

    # Register shutdown handler to prevent thread-related errors
    @atexit.register
    def _cleanup_threads():
        """Handle thread cleanup gracefully on exit"""
        # Suppress threading-related errors during interpreter shutdown
        logging.shutdown()


def apply_thread_safety_patches():
    """
    Apply all thread safety patches required for proper program shutdown.

    Call this function early in your application startup to ensure clean thread
    handling during program termination, especially when using concurrent.futures.
    """
    import sys

    if sys.version_info.major == 3 and sys.version_info.minor == 13:
        patch_threading_for_python_3_13()

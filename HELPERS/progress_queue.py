"""
Global progress queue for cross-process progress updates
"""

import asyncio
import threading
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GlobalProgressQueue:
    """Global progress queue for cross-process communication"""
    
    def __init__(self):
        self._queues: Dict[int, List[Tuple[int, str]]] = defaultdict(list)  # user_id -> [(msg_id, progress_text), ...]
        self._lock = threading.Lock()
        self._active_updaters: Dict[int, asyncio.Task] = {}  # user_id -> task
        self._updater_lock = asyncio.Lock()
    
    def add_progress(self, user_id: int, msg_id: int, progress_text: str):
        """Add progress update to queue"""
        with self._lock:
            self._queues[user_id].append((msg_id, progress_text))
            logger.debug("Added progress for user %s: %s", user_id, progress_text)
    
    def get_progress(self, user_id: int) -> Optional[Tuple[int, str]]:
        """Get next progress update for user"""
        with self._lock:
            if self._queues[user_id]:
                return self._queues[user_id].pop(0)
            return None
    
    def has_progress(self, user_id: int) -> bool:
        """Check if user has pending progress updates"""
        with self._lock:
            return len(self._queues[user_id]) > 0
    
    def clear_user_progress(self, user_id: int):
        """Clear all progress for user"""
        with self._lock:
            self._queues[user_id].clear()
    
    async def start_updater(self, user_id: int, app=None):
        """Start progress updater for user"""
        async with self._updater_lock:
            if user_id in self._active_updaters:
                return  # Already running
            
            async def updater():
                from HELPERS.safe_messeger import safe_edit_message_text
                while True:
                    try:
                        progress = self.get_progress(user_id)
                        if progress:
                            msg_id, progress_text = progress
                            try:
                                await safe_edit_message_text(user_id, msg_id, progress_text)
                                logger.info("Progress updated for user %s: %s", user_id, progress_text)
                            except Exception as e:
                                logger.error("Progress update error for user %s: %s", user_id, e)
                        else:
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error("Progress updater error for user %s: %s", user_id, e)
                        await asyncio.sleep(1.0)
            
            self._active_updaters[user_id] = asyncio.create_task(updater())
            logger.info("Started progress updater for user %s", user_id)
    
    async def stop_updater(self, user_id: int):
        """Stop progress updater for user"""
        async with self._updater_lock:
            if user_id in self._active_updaters:
                task = self._active_updaters[user_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._active_updaters[user_id]
                logger.info("Stopped progress updater for user %s", user_id)
    
    def get_queue_size(self, user_id: int) -> int:
        """Get queue size for user"""
        with self._lock:
            return len(self._queues[user_id])
    
    def process_progress_sync(self, user_id: int):
        """Process progress updates synchronously (for use in sync contexts)"""
        try:
            progress = self.get_progress(user_id)
            if progress:
                msg_id, progress_text = progress
                # Use asyncio.run to handle async function in sync context
                import asyncio
                from HELPERS.safe_messeger import safe_edit_message_text
                try:
                    asyncio.run(safe_edit_message_text(user_id, msg_id, progress_text))
                    logger.info("Progress updated for user %s: %s", user_id, progress_text)
                except Exception as e:
                    logger.error("Progress update error for user %s: %s", user_id, e)
                return True
            return False
        except Exception as e:
            logger.error("Sync progress processing error for user %s: %s", user_id, e)
            return False

# Global instance
progress_queue = GlobalProgressQueue()

"""
Global progress queue for cross-process progress updates
Updated to work with the new reliable progress system
"""

import asyncio
import threading
import time
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GlobalProgressQueue:
    """Global progress queue for cross-process communication with reliable updates"""
    
    def __init__(self):
        self._queues: Dict[int, List[Tuple[int, str, float]]] = defaultdict(list)  # user_id -> [(msg_id, progress_text, timestamp), ...]
        self._lock = threading.Lock()
        self._active_updaters: Dict[int, asyncio.Task] = {}  # user_id -> task
        self._updater_lock = asyncio.Lock()
        self._last_update: Dict[Tuple[int, int], float] = {}  # (user_id, msg_id) -> timestamp
        self._throttle_interval = 1.0  # Minimum interval between updates per message
    
    def add_progress(self, user_id: int, msg_id: int, progress_text: str):
        """Add progress update to queue with throttling"""
        current_time = time.time()
        key = (user_id, msg_id)
        
        # Throttle updates to avoid spam
        if key in self._last_update:
            if current_time - self._last_update[key] < self._throttle_interval:
                return
        
        with self._lock:
            self._queues[user_id].append((msg_id, progress_text, current_time))
            self._last_update[key] = current_time
            logger.debug("Added progress for user %s: %s", user_id, progress_text)
    
    def get_progress(self, user_id: int) -> Optional[Tuple[int, str]]:
        """Get next progress update for user"""
        with self._lock:
            if self._queues[user_id]:
                msg_id, progress_text, timestamp = self._queues[user_id].pop(0)
                return (msg_id, progress_text)
            return None
    
    def has_progress(self, user_id: int) -> bool:
        """Check if user has pending progress updates"""
        with self._lock:
            return len(self._queues[user_id]) > 0
    
    def clear_user_progress(self, user_id: int):
        """Clear all progress for user"""
        with self._lock:
            self._queues[user_id].clear()
            # Clear throttling data for this user
            keys_to_remove = [key for key in self._last_update.keys() if key[0] == user_id]
            for key in keys_to_remove:
                del self._last_update[key]
    
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
                # Use threading to avoid event loop conflicts
                import threading
                from HELPERS.safe_messeger import safe_edit_message_text
                
                def run_async_in_thread():
                    try:
                        import asyncio
                        # Create new event loop in thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(safe_edit_message_text(user_id, msg_id, progress_text))
                            logger.info("Progress updated for user %s: %s", user_id, progress_text)
                        finally:
                            loop.close()
                    except Exception as e:
                        logger.error("Progress update error for user %s: %s", user_id, e)
                
                # Run in background thread
                thread = threading.Thread(target=run_async_in_thread, daemon=True)
                thread.start()
                return True
            return False
        except Exception as e:
            logger.error("Sync progress processing error for user %s: %s", user_id, e)
            return False
    
    def set_throttle_interval(self, interval: float):
        """Set throttle interval for progress updates"""
        self._throttle_interval = interval
        logger.info("Set throttle interval to %s seconds", interval)
    
    def get_status(self) -> Dict:
        """Get queue status"""
        with self._lock:
            return {
                'total_users': len(self._queues),
                'total_updates': sum(len(queue) for queue in self._queues.values()),
                'active_updaters': len(self._active_updaters),
                'throttle_interval': self._throttle_interval
            }

# Global instance
progress_queue = GlobalProgressQueue()
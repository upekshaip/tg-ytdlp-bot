
import threading
import time
import os
import re
import asyncio
from CONFIG.config import Config
from CONFIG.messages import Messages, safe_get_messages
from HELPERS.app_instance import get_app
from HELPERS.logger import logger
from HELPERS.safe_messeger import safe_edit_message_text
from HELPERS.filesystem_hlp import create_directory, cleanup_user_temp_files

# Global dictionary to track active downloads and lock for thread-safe access
active_downloads = {}
active_downloads_lock = threading.Lock()

# Global dictionary to track playlist errors and lock for thread-safe access
playlist_errors = {}
playlist_errors_lock = threading.Lock()

# Add a global dictionary to track download start times
download_start_times = {}
download_start_times_lock = threading.Lock()

# Get app instance for decorators
app = get_app()

# Global progress update queue for reliable progress updates
class ProgressUpdateQueue:
    def __init__(self):
        self.queue = {}
        self.locks = {}
        self.last_update = {}
        
    def add_update(self, user_id, msg_id, text):
        """Add progress update to queue"""
        key = (user_id, msg_id)
        if key not in self.locks:
            self.locks[key] = threading.Lock()
        
        with self.locks[key]:
            self.queue[key] = text
            self.last_update[key] = time.time()
    
    def get_update(self, user_id, msg_id):
        """Get latest progress update from queue"""
        key = (user_id, msg_id)
        if key not in self.locks:
            return None
            
        with self.locks[key]:
            return self.queue.get(key)
    
    def clear_update(self, user_id, msg_id):
        """Clear progress update from queue"""
        key = (user_id, msg_id)
        if key in self.locks:
            with self.locks[key]:
                self.queue.pop(key, None)
                self.last_update.pop(key, None)

# Global progress update queue instance
progress_queue = ProgressUpdateQueue()

# Background thread for processing progress updates
class ProgressUpdateProcessor:
    def __init__(self):
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        
    def start(self):
        """Start the progress update processor"""
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._process_updates, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the progress update processor"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def _process_updates(self):
        """Process progress updates in background thread"""
        while self.running and not self.stop_event.is_set():
            try:
                # Process all queued updates
                updates_to_process = []
                for key in list(progress_queue.queue.keys()):
                    user_id, msg_id = key
                    text = progress_queue.get_update(user_id, msg_id)
                    if text:
                        updates_to_process.append((user_id, msg_id, text))
                        progress_queue.clear_update(user_id, msg_id)
                
                # Process updates
                for user_id, msg_id, text in updates_to_process:
                    try:
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Update message
                        result = loop.run_until_complete(
                            safe_edit_message_text(user_id, msg_id, text)
                        )
                        
                        loop.close()
                        
                        # If update failed, stop processing for this message
                        if result is None:
                            progress_queue.clear_update(user_id, msg_id)
                            
                    except Exception as e:
                        logger.error(f"Error processing progress update: {e}")
                        progress_queue.clear_update(user_id, msg_id)
                
                # Sleep before next iteration
                if not self.stop_event.wait(0.5):
                    continue
                    
            except Exception as e:
                logger.error(f"Error in progress update processor: {e}")
                break
                
        logger.debug("Progress update processor stopped")

# Global progress update processor
progress_processor = ProgressUpdateProcessor()

# Start the progress update processor
progress_processor.start()

# Class for managing hourglass animations with proper cleanup
class HourglassManager:
    def __init__(self, user_id, hourglass_msg_id):
        self.user_id = user_id
        self.hourglass_msg_id = hourglass_msg_id
        self.stop_event = threading.Event()
        self.thread = None
        self.messages = safe_get_messages(user_id)

    def start(self):
        """Start the hourglass animation"""
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self, timeout=2.0):
        """Stop the hourglass animation and wait for thread to finish"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=timeout)

    def _animate(self):
        """Internal animation method"""
        counter = 0
        emojis = self.messages.DOWNLOAD_STATUS_HOURGLASS_EMOJIS
        active = True
        start_time = time.time()
        last_update = 0

        while active and not self.stop_event.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                minutes_passed = int(elapsed // 60)
                
                # Adaptive animation interval (linear slow-down every 5 minutes)
                if minutes_passed and minutes_passed >= 60:
                    interval = 90.0  # After 1 hour, update once per 90 seconds
                else:
                    # 0-4 min: 3s, 5-9: 4s, 10-14: 5s, ... up to 55-59: 14s
                    interval = 3.0 + max(0, minutes_passed // 5)
                
                if current_time - last_update < interval:
                    # Use Event.wait() instead of time.sleep() for interruptible sleep
                    if self.stop_event.wait(1.0):
                        break
                    continue
                
                emoji = emojis[counter % len(emojis)]
                # Use progress queue for reliable updates
                progress_queue.add_update(
                    self.user_id, 
                    self.hourglass_msg_id, 
                    f"{emoji} {self.messages.DOWNLOAD_STATUS_PLEASE_WAIT_MSG}"
                )
                
                counter += 1
                last_update = current_time
                
            except Exception as e:
                logger.error(f"Error in hourglass animation: {e}")
                active = False
                break

        logger.debug(f"Hourglass animation stopped for message {self.hourglass_msg_id}")

# Class for managing cycle progress animations with proper cleanup
class CycleProgressManager:
    def __init__(self, user_id, proc_msg_id, current_total_process, user_dir_name, progress_data=None):
        self.user_id = user_id
        self.proc_msg_id = proc_msg_id
        self.current_total_process = current_total_process
        self.user_dir_name = user_dir_name
        self.progress_data = progress_data
        self.stop_event = threading.Event()
        self.thread = None
        self.messages = safe_get_messages(user_id)

    def start(self):
        """Start the cycle progress animation"""
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self, timeout=2.0):
        """Stop the cycle progress animation and wait for thread to finish"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=timeout)
            self.thread = None

    def _animate(self):
        """Internal animation method"""
        counter = 0
        active = True
        start_time = time.time()
        last_update = 0

        while active and not self.stop_event.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                minutes_passed = int(elapsed // 60)
                
                # Adaptive update interval (linear; after 1h fixed 90s)
                if minutes_passed and minutes_passed >= 60:
                    interval = 90.0
                else:
                    interval = 3.0 + max(0, minutes_passed // 5)
                
                if current_time - last_update < interval:
                    # Use Event.wait() instead of time.sleep() for interruptible sleep
                    if self.stop_event.wait(1.0):
                        break
                    continue
                
                counter = (counter + 1) % 11
                
                # Check for fragment files
                frag_files = []
                try:
                    frag_files = [f for f in os.listdir(self.user_dir_name) if 'Frag' in f]
                except (FileNotFoundError, PermissionError) as e:
                    logger.debug(f"Error checking fragment files: {e}")

                if frag_files:
                    last_frag = sorted(frag_files)[-1]
                    m = re.search(r'Frag(\d+)', last_frag)
                    frag_text = f"Frag{m.group(1)}" if m else "Frag?"
                else:
                    frag_text = self.messages.DOWNLOAD_STATUS_WAITING_FRAGMENTS_MSG

                # Check if we have real progress data (percentages)
                if self.progress_data and self.progress_data.get('downloaded_bytes') and self.progress_data.get('total_bytes'):
                    downloaded = self.progress_data.get('downloaded_bytes', 0)
                    total = self.progress_data.get('total_bytes', 0)
                    percent = (downloaded / total * 100) if total else 0
                    blocks = int(percent // 10)
                    bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                    # Use progress queue for reliable updates
                    progress_queue.add_update(
                        self.user_id, 
                        self.proc_msg_id,
                        f"{self.current_total_process}\n{self.messages.DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG}\n{bar}   {percent:.1f}%"
                    )
                else:
                    # Fallback to fragment-based animation
                    bar = "🟩" * counter + "⬜️" * (10 - counter)
                    # Use progress queue for reliable updates
                    progress_queue.add_update(
                        self.user_id, 
                        self.proc_msg_id,
                        f"{self.current_total_process}\n{self.messages.DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG} {frag_text}\n{bar}"
                    )

                last_update = current_time
                
            except Exception as e:
                logger.warning(f"Cycle progress error: {e}")
                active = False
                break

        logger.debug(f"Cycle progress animation stopped for message {self.proc_msg_id}")

def set_download_start_time(user_id):
    """
    Sets the download start time for a user
    """
    with download_start_times_lock:
        download_start_times[user_id] = time.time()


def clear_download_start_time(user_id):
    """
    Clears the download start time for a user
    """
    with download_start_times_lock:
        if user_id in download_start_times:
            del download_start_times[user_id]


def check_download_timeout(user_id):
    """
    Checks if the download timeout has been exceeded. For admins, timeout does not apply.
    """
    # If the user is an admin, timeout does not apply
    if hasattr(Config, 'ADMIN') and int(user_id) in Config.ADMIN:
        return False
    with download_start_times_lock:
        if user_id in download_start_times:
            start_time = download_start_times[user_id]
            current_time = time.time()
            if current_time - start_time > Config.DOWNLOAD_TIMEOUT:
                return True
    return False

# Helper function to safely get active download status
def get_active_download(user_id):
    """
    Thread-safe function to get the active download status for a user

    Args:
        user_id: The user ID

    Returns:
        bool: Whether the user has an active download
    """
    with active_downloads_lock:
        return active_downloads.get(user_id, False)



# Helper function to safely set active download status
def set_active_download(user_id, status):
    """
    Thread-safe function to set the active download status for a user

    Args:
        user_id: The user ID
        status (bool): Whether the user has an active download
    """
    with active_downloads_lock:
        active_downloads[user_id] = status

# Helper function to start the hourglass animation
def start_hourglass_animation(user_id, hourglass_msg_id, stop_anim):
    messages = safe_get_messages(user_id)
    """
    Start an hourglass animation in a separate thread

    Args:
        user_id: The user ID
        hourglass_msg_id: The message ID to animate
        stop_anim: An event to signal when to stop the animation

    Returns:
        The animation thread
    """

    def animate_hourglass():
        messages = safe_get_messages(user_id)
        """Animate an hourglass emoji by toggling between two hourglass emojis"""
        counter = 0
        emojis = messages.DOWNLOAD_STATUS_HOURGLASS_EMOJIS
        active = True
        start_time = time.time()
        last_update = 0

        while active and not stop_anim.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                minutes_passed = int(elapsed // 60)
                
                # Adaptive animation interval (linear slow-down every 5 minutes)
                if minutes_passed and minutes_passed >= 60:
                    interval = 90.0  # After 1 hour, update once per 90 seconds
                else:
                    # 0-4 min: 3s, 5-9: 4s, 10-14: 5s, ... up to 55-59: 14s
                    interval = 3.0 + max(0, minutes_passed // 5)
                
                if current_time - last_update < interval:
                    # Use Event.wait() instead of time.sleep() for interruptible sleep
                    if stop_anim.wait(1.0):
                        break
                    continue
                
                emoji = emojis[counter % len(emojis)]
                # Use progress queue for reliable updates
                progress_queue.add_update(
                    user_id, 
                    hourglass_msg_id, 
                    f"{emoji} {messages.DOWNLOAD_STATUS_PLEASE_WAIT_MSG}"
                )
                
                counter += 1
                last_update = current_time
                
            except Exception as e:
                logger.error(f"Error in hourglass animation: {e}")
                active = False
                break

        logger.debug(f"Hourglass animation stopped for message {hourglass_msg_id}")

    # Start animation in a daemon thread so it will exit when the main thread exits
    hourglass_thread = threading.Thread(target=animate_hourglass, daemon=True)
    hourglass_thread.start()
    return hourglass_thread

# Cache for throttling upload progress edits per message
_last_upload_update_ts = {}

# Helper function to start cycle progress animation
def start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop, progress_data=None):
    messages = safe_get_messages(user_id)
    """
    Start a progress animation for HLS downloads

    Args:
        user_id: The user ID
        proc_msg_id: The message ID to update with progress
        current_total_process: String describing the current process
        user_dir_name: Directory name where fragments are saved
        cycle_stop: Event to signal animation stop
        progress_data: Optional dict with 'downloaded_bytes' and 'total_bytes' for real progress

    Returns:
        The animation thread
    """

    def cycle_progress():
        messages = safe_get_messages(user_id)
        """Show progress animation for HLS downloads"""
        counter = 0
        active = True
        start_time = time.time()
        last_update = 0

        while active and not cycle_stop.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - start_time
                minutes_passed = int(elapsed // 60)
                
                # Adaptive update interval (linear; after 1h fixed 90s)
                if minutes_passed and minutes_passed >= 60:
                    interval = 90.0
                else:
                    interval = 3.0 + max(0, minutes_passed // 5)
                
                if current_time - last_update < interval:
                    # Use Event.wait() instead of time.sleep() for interruptible sleep
                    if cycle_stop.wait(1.0):
                        break
                    continue
                
                counter = (counter + 1) % 11
                
                # Check for fragment files
                frag_files = []
                try:
                    frag_files = [f for f in os.listdir(user_dir_name) if 'Frag' in f]
                except (FileNotFoundError, PermissionError) as e:
                    logger.debug(f"Error checking fragment files: {e}")

                if frag_files:
                    last_frag = sorted(frag_files)[-1]
                    m = re.search(r'Frag(\d+)', last_frag)
                    frag_text = f"Frag{m.group(1)}" if m else "Frag?"
                else:
                    frag_text = messages.DOWNLOAD_STATUS_WAITING_FRAGMENTS_MSG

                # Check if we have real progress data (percentages)
                if progress_data and progress_data.get('downloaded_bytes') and progress_data.get('total_bytes'):
                    downloaded = progress_data.get('downloaded_bytes', 0)
                    total = progress_data.get('total_bytes', 0)
                    percent = (downloaded / total * 100) if total else 0
                    blocks = int(percent // 10)
                    bar = "🟩" * blocks + "⬜️" * (10 - blocks)
                    # Use progress queue for reliable updates
                    progress_queue.add_update(
                        user_id, 
                        proc_msg_id,
                        f"{current_total_process}\n{messages.DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG}\n{bar}   {percent:.1f}%"
                    )
                else:
                    # Fallback to fragment-based animation
                    bar = "🟩" * counter + "⬜️" * (10 - counter)
                    # Use progress queue for reliable updates
                    progress_queue.add_update(
                        user_id, 
                        proc_msg_id,
                        f"{current_total_process}\n{messages.DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG} {frag_text}\n{bar}"
                    )

                last_update = current_time
                
            except Exception as e:
                logger.warning(f"Cycle progress error: {e}")
                active = False
                break

        logger.debug(f"Cycle progress animation stopped for message {proc_msg_id}")
    
    cycle_thread = threading.Thread(target=cycle_progress, daemon=True)
    cycle_thread.start()
    return cycle_thread

async def progress_bar(*args):
    # It is expected that Pyrogram will cause Progress_BAR with five parameters:
    # Current, Total, Speed, ETA, File_SIZE, and then additionally your Progress_args (User_id, Msg_id, Status_text)
    if len(args) < 8:
        return
    current, total, speed, eta, file_size, user_id, msg_id, status_text = args[:8]
    # Throttle to avoid flood: update at most once per second per message
    now = time.time()
    key = (user_id, msg_id)
    last_ts = _last_upload_update_ts.get(key, 0)
    if now - last_ts < 1.0 and current < total:
        return
    # Build a simple progress bar
    try:
        percent = (current / total * 100) if total else 0
        blocks = int(percent // 10)
        bar = "🟩" * blocks + "⬜️" * (10 - blocks)
        text = f"{status_text}\n{bar}   {percent:.1f}%"
        # Use progress queue for reliable updates
        progress_queue.add_update(user_id, msg_id, text)
        _last_upload_update_ts[key] = now
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

# Helper function to update progress directly
def update_progress(user_id, msg_id, text):
    """Update progress message using the reliable queue system"""
    try:
        progress_queue.add_update(user_id, msg_id, text)
    except Exception as e:
        logger.error(f"Error adding progress update to queue: {e}")

# Helper function to clear progress updates
def clear_progress_updates(user_id, msg_id):
    """Clear progress updates for a specific message"""
    try:
        progress_queue.clear_update(user_id, msg_id)
    except Exception as e:
        logger.error(f"Error clearing progress updates: {e}")
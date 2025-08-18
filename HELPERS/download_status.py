

import threading
import time
from CONFIG.config import Config
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



from HELPERS.app_instance import get_app

# Get app instance for decorators
app = get_app()

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
        """Animate an hourglass emoji by toggling between two hourglass emojis"""
        counter = 0
        emojis = ["⏳", "⌛"]
        active = True

        while active and not stop_anim.is_set():
            try:
                emoji = emojis[counter % len(emojis)]
                # Attempt to edit message but don't keep trying if message is invalid
                result = safe_edit_message_text(user_id, hourglass_msg_id, f"{emoji} Please wait...")

                # If message edit returns None due to MESSAGE_ID_INVALID, stop animation
                if result is None and counter > 0:  # Allow first attempt to fail
                    active = False
                    break

                counter += 1
                time.sleep(3.0)
            except Exception as e:
                logger.error(f"Error in hourglass animation: {e}")
                # Stop animation on error to prevent log spam
                active = False
                break

        logger.debug(f"Hourglass animation stopped for message {hourglass_msg_id}")

    # Start animation in a daemon thread so it will exit when the main thread exits
    hourglass_thread = threading.Thread(target=animate_hourglass, daemon=True)
    hourglass_thread.start()
    return hourglass_thread

# Helper function to start cycle progress animation
def start_cycle_progress(user_id, proc_msg_id, current_total_process, user_dir_name, cycle_stop):
    """
    Start a progress animation for HLS downloads

    Args:
        user_id: The user ID
        proc_msg_id: The message ID to update with progress
        current_total_process: String describing the current process
        user_dir_name: Directory name where fragments are saved
        cycle_stop: Event to signal animation stop

    Returns:
        The animation thread
    """

    def cycle_progress():
        """Show progress animation for HLS downloads"""
        counter = 0
        active = True

        while active and not cycle_stop.is_set():
            counter = (counter + 1) % 11
            try:
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
                    frag_text = "waiting for fragments"

                bar = "🟩" * counter + "⬜️" * (10 - counter)

                # Use safe_edit_message_text and check if message exists
                result = safe_edit_message_text(user_id, proc_msg_id,
                    f"{current_total_process}\n📥 Downloading HLS stream: {frag_text}\n{bar}")

                # If message was deleted (returns None), stop animation
                if result is None and counter > 2:  # Allow first few attempts to fail
                    active = False
                    break

            except Exception as e:
                logger.warning(f"Cycle progress error: {e}")
                # Stop animation on consistent errors to prevent log spam
                active = False
                break

            # Sleep with check for stop event
            if cycle_stop.wait(3.0):
                break

        logger.debug(f"Cycle progress animation stopped for message {proc_msg_id}")

    cycle_thread = threading.Thread(target=cycle_progress, daemon=True)
    cycle_thread.start()
    return cycle_thread

def progress_bar(*args):
    # It is expected that Pyrogram will cause Progress_BAR with five parameters:
    # Current, Total, Speed, ETA, File_SIZE, and then additionally your Progress_args (User_id, Msg_id, Status_text)
    if len(args) < 8:
        return
    current, total, speed, eta, file_size, user_id, msg_id, status_text = args[:8]
    try:
        app.edit_message_text(user_id, msg_id, status_text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

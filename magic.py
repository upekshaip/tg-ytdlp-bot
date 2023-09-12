import pyrebase
import os
from pyrogram import Client, filters
from pyrogram import enums
from pyrogram import errors
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import requests
import math
import time
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import subprocess
from config import Config
################################################################################################
# this is the bot's starting point. do not touch this one
starting_point = []
################################################################################################

# Firebase initialization
firebase = pyrebase.initialize_app(Config.FIREBASE_CONF)
db = firebase.database()

##############################################################################################################################
##############################################################################################################################


# App
app = Client(
    "magic",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

##############################################################################################################################
##############################################################################################################################


@app.on_message(filters.command("start") & filters.private)
def command1(app, message):
    if int(message.chat.id) in Config.ADMIN:
        send_to_user(message, "Welcome Master 🥷")
    else:
        check_user(message)
        app.send_message(
            message.chat.id, f"Hello {message.chat.first_name},\n \n__This bot🤖 can download any videos into telegram directly.😊 For more information press **/help**__ 👈\n \n __Developed by__ @upekshaip")
        send_to_logger(message, f"{message.chat.id} - user started the bot")


@app.on_message(filters.command("help"))
def command2(app, message):
    app.send_message(message.chat.id, (Config.HELP_MSG),
                     parse_mode=enums.ParseMode.MARKDOWN)
    send_to_logger(message, f"Send help txt to user")


#####################################################################################

# checking user is blocked or not
def is_user_blocked(message):
    blocked = db.child(f"{Config.BOT_DB_PATH}/blocked_users").get().each()
    blocked_users = [int(b_user.key()) for b_user in blocked]
    if int(message.chat.id) in blocked_users:
        send_to_user(message, "You are banned from the bot!")
        return True
    else:
        return False


# cheking users are in main user directory in db
def check_user(message):
    user_db = db.child(f"{Config.BOT_DB_PATH}/users").get().each()
    users = [int(user.key()) for user in user_db]

    if int(message.chat.id) not in users:
        data = {"ID": message.chat.id,
                "timestamp": math.floor(time.time())}
        db.child(
            f"{Config.BOT_DB_PATH}/users/{str(message.chat.id)}").set(data)

#####################################################################################


# checking actions
@ app.on_message(filters.text & filters.private)
def url_distractor(app, message):
    user_id = message.chat.id
    try:
        if is_user_in_channel(app, message):
            # download video function
            if ("https://" in message.text) or ("http://" in message.text):
                if not is_user_blocked(message):
                    video_url_extractor(app, message)

            # calling caption_editor function for videos
            if message.reply_to_message:
                if not is_user_blocked(message):
                    if message.reply_to_message.video:
                        caption_editor(app, message)

            if Config.CLEAN_COMMAND in message.text:
                remove_media(message)
                send_to_all(message, 'All files are removed.')

            if Config.USAGE_COMMAND in message.text:
                get_user_log(app, message)

            # calling check cookie function
            if Config.CHECK_COOKIE_COMMAND == message.text:
                checking_cookie_file(app, message)

            # calling update the cookie file function
            if Config.SAVE_AS_COOKIE_COMMAND in message.text:
                save_as_cookie_file(app, message)

        # Admin commands
        if int(message.chat.id) in Config.ADMIN:

            # Broadcast messages to users
            if message.reply_to_message and message.text == Config.BROADCAST_MESSAGE:
                send_promo_message(app, message)
                # send_to_user(message, message.reply_to_message)

            # download cookiefile
            if Config.DOWNLOAD_COOKIE_COMMAND == message.text:
                download_cookie(app, message)

            # Block user
            if Config.BLOCK_USER_COMMAND in message.text:
                block_user(app, message)

            # Unblock user
            if Config.UNBLOCK_USER_COMMAND in message.text:
                unblock_user(app, message)

            # Check running time
            if Config.RUN_TIME in message.text:
                check_runtime(message)

            # get all users deatial list
            if Config.GET_USER_DETAILS_COMMAND in message.text:
                get_user_details(app, message)

            # Getting logs of specific user
            if Config.GET_USER_LOGS_COMMAND in message.text:
                get_user_log(app, message)

    except IndexError:
        send_to_all(message, f"{IndexError}\n{Config.INDEX_ERROR}")
    except:
        send_to_all(message, "Some error occurred 😕")

    else:
        print(user_id, f"No system errors found on above activity")


# Check the usage of the bot
def is_user_in_channel(app, message):
    try:
        cht_member = app.get_chat_member(
            Config.SUBSCRIBE_CHANNEL, message.chat.id)
        if cht_member.status == ChatMemberStatus.MEMBER or cht_member.status == ChatMemberStatus.OWNER or cht_member.status == ChatMemberStatus.ADMINISTRATOR:
            return True

    except:

        text = "__To use this bot you needs to subscribe @upekshaip's Telegram channel.__\nAfter you join the channel, **send your link** ❤️\n \n \n__Developed by @upekshaip__"
        button = InlineKeyboardButton(
            "Join Channel", url=Config.SUBSCRIBE_CHANNEL_URL)
        keyboard = InlineKeyboardMarkup([[button]])
        # Use the send_message() method to send the message with the button
        app.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        return False


# Remove all user media files
def remove_media(message):
    dir = f'./users/{str(message.chat.id)}'
    if os.path.exists(dir):

        allfiles = os.listdir(dir)

        mp4_files = [fname for fname in allfiles if fname.endswith('.mp4')]
        mp3_files = [fname for fname in allfiles if fname.endswith('.mp3')]
        jpg_files = [fname for fname in allfiles if fname.endswith('.jpg')]
        part_files = [fname for fname in allfiles if fname.endswith('.part')]
        ytdl_files = [fname for fname in allfiles if fname.endswith('.ytdl')]
        txt_files = [fname for fname in allfiles if fname.endswith('.txt')]
        webm_files = [fname for fname in allfiles if fname.endswith('.webm')]

        if len(mp4_files) > 0:
            for file in mp4_files:
                os.remove(f"{dir}/{file}")
        if len(mp3_files) > 0:
            for file in mp3_files:
                os.remove(f"{dir}/{file}")
        if len(jpg_files) > 0:
            for file in jpg_files:
                os.remove(f"{dir}/{file}")
        if len(part_files) > 0:
            for file in part_files:
                os.remove(f"{dir}/{file}")
        if len(ytdl_files) > 0:
            for file in ytdl_files:
                os.remove(f"{dir}/{file}")
        if len(txt_files) > 0:
            for file in txt_files:
                os.remove(f"{dir}/{file}")
        if len(webm_files) > 0:
            for file in webm_files:
                os.remove(f"{dir}/{file}")

        print("All media removed.")


# Send messages to all the users
def send_promo_message(app, message):
    user_lst = db.child(f"{Config.BOT_DB_PATH}/users").get().each()
    user_lst = [int(user.key()) for user in user_lst]
    for admin in Config.ADMIN:
        user_lst.append(admin)
    try:
        reply = message.reply_to_message
        for user in user_lst:
            try:
                if user != 0:
                    if reply.text:
                        app.send_message(user, reply.text)
                    if reply.video:
                        app.send_video(user, reply.video.file_id,
                                       caption=reply.caption)
                    if reply.photo:
                        app.send_photo(user, reply.photo.file_id,
                                       caption=reply.caption)
                    if reply.sticker:
                        app.send_sticker(user, reply.sticker.file_id)
                    if reply.document:
                        app.send_document(user, reply.document.file_id,
                                          caption=reply.caption)
                    if reply.audio:
                        app.send_audio(user, reply.audio.file_id,
                                       caption=reply.caption)
                    if reply.animation:
                        app.send_animation(user, reply.animation.file_id,
                                           caption=reply.caption)
            except:
                pass

        send_to_all(message, "**Promo message sent to all other users**")
    except:
        send_to_all(
            message, "**Cannot send the promo message. Try repling to a massege\n Or some error occured**")


# Getting the user logs
def get_user_log(app, message):
    user_id = message.chat.id
    if int(message.chat.id) in Config.ADMIN:
        user_id = message.chat.id
        if Config.GET_USER_LOGS_COMMAND in message.text:
            user_id = message.text.split(Config.GET_USER_LOGS_COMMAND + " ")[1]

    try:
        db_data = db.child(f"{Config.BOT_DB_PATH}/logs/{user_id}").get().each()
        lst = [user.val() for user in db_data]
        data = []
        data_tg = []
        least_10 = []
        topics = ["TS", "ID", "Name", "Video Title", "URL"]

        for l in lst:
            ts = datetime.fromtimestamp(int(l["timestamp"]))
            row = f"""{ts} | {l["ID"]} | {l["name"]} | {l["title"]} | {l["urls"]}"""
            row_2 = f"""**{ts}** | `{l["ID"]}` | **{l["name"]}** | {l["title"]} | {l["urls"]}"""
            data.append(row)
            data_tg.append(row_2)
        total = len(data_tg)
        if total > 10:
            for i in range(10):
                info = data_tg[(total - 10) + i]
                least_10.append(info)
            least_10.sort(key=str.lower)
            format = '\n \n'.join(least_10)
        else:
            data_tg.sort(key=str.lower)
            format = '\n \n'.join(data_tg)
        data.sort(key=str.lower)
        now = datetime.fromtimestamp(math.floor(time.time()))
        txt_format = f"Logs of {Config.BOT_NAME_FOR_USERS}\nUser: {user_id}\nTotal logs: {total}\nCurrent time: {now}\n \n" + \
            '\n'.join(data)

        create_directory(str(message.chat.id))
        log_path = f"./users/{str(message.chat.id)}/logs.txt"
        with open(log_path, 'w', encoding="utf-8") as f:
            f.write(str(txt_format))

        send_to_all(
            message, f"Total: **{total}**\n**{user_id}** - logs (Last 10):\n \n \n{format}")
        app.send_document(message.chat.id, log_path,
                          caption=f"{user_id} - all logs")
        app.send_document(Config.LOGS_ID, log_path,
                          caption=f"{user_id} - all logs")
    except:
        send_to_all(
            message, "**User did not download any content yet...** Not exist in logs")

# Get all kinds of users (users/ blocked/ unblocked)


def get_user_details(app, message):
    command = message.text.split(Config.GET_USER_DETAILS_COMMAND)[1]
    if command == "_blocked":
        path = "blocked_users"
    if command == "_unblocked":
        path = "unblocked_users"
    if command == "_users":
        path = "users"
    modified_lst = []
    txt_lst = []
    raw_data = db.child(
        f"{Config.BOT_DB_PATH}/{path}").get().each()
    data_users = [user.val() for user in raw_data]
    for user in data_users:
        if user["ID"] != "0":
            id = user["ID"]
            ts = datetime.fromtimestamp(int(user["timestamp"]))
            txt_format = f"TS: {ts} | ID: {id}"
            id = f"TS: **{ts}** | ID: `{id}`"
            modified_lst.append(id)
            txt_lst.append(txt_format)

    modified_lst.sort(key=str.lower)
    txt_lst.sort(key=str.lower)
    no_of_users_to_display = 20
    if len(modified_lst) <= no_of_users_to_display:
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " + \
            path + \
            f":\n \n" + \
            '\n'.join(modified_lst)
    else:
        temp = []
        for j in range(no_of_users_to_display):
            temp.append(modified_lst[((j+1) * -1)])
        temp.sort(key=str.lower)
        mod = f"__Total Users: {len(modified_lst)}__\nLast {str(no_of_users_to_display)} " + \
            path + \
            f":\n \n" + '\n'.join(temp)

    now = datetime.fromtimestamp(math.floor(time.time()))
    txt_format = f"{Config.BOT_NAME} {path}\nTotal {path}: {len(modified_lst)}\nCurrent time: {now}\n \n" + '\n'.join(
        txt_lst)
    file = path + '.txt'
    with open(file, 'w', encoding="utf-8") as f:
        f.write(str(txt_format))
    send_to_all(message, mod)
    app.send_document(message.chat.id, "./" + file,
                      caption=f"{Config.BOT_NAME} - all {path}")
    app.send_document(Config.LOGS_ID, "./" + file,
                      caption=f"{Config.BOT_NAME} - all {path}")

    print(mod)


# Block user
def block_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        dt = math.floor(time.time())
        b_user_id = str((message.text).split(
            Config.BLOCK_USER_COMMAND + " ")[1])

        if int(b_user_id) in Config.ADMIN:
            send_to_user(message, "Admin cannot delete an admin")
        else:
            all_blocked_users = db.child(
                f"{Config.BOT_DB_PATH}/blocked_users").get().each()
            b_users = [b_user.key() for b_user in all_blocked_users]

            if b_user_id not in b_users:
                data = {"ID": b_user_id, "timestamp": str(dt)}
                db.child(
                    f"{Config.BOT_DB_PATH}/blocked_users/{b_user_id}").set(data)
                send_to_user(
                    message, f"User blocked 🔒❌\n \nID: `{b_user_id}`\nBlocked Date: {datetime.fromtimestamp(dt)}")

            else:
                send_to_user(message, f"`{b_user_id}` is already blocked ❌😐")
    else:
        send_to_user(message, "Sorry! You are not an admin")


# Unblock user
def unblock_user(app, message):
    if int(message.chat.id) in Config.ADMIN:
        ub_user_id = str((message.text).split(
            Config.UNBLOCK_USER_COMMAND + " ")[1])
        all_blocked_users = db.child(
            f"{Config.BOT_DB_PATH}/blocked_users").get().each()
        b_users = [b_user.key() for b_user in all_blocked_users]

        if ub_user_id in b_users:
            dt = math.floor(time.time())

            data = {"ID": ub_user_id, "timestamp": str(dt)}
            db.child(
                f"{Config.BOT_DB_PATH}/unblocked_users/{ub_user_id}").set(data)
            db.child(
                f"{Config.BOT_DB_PATH}/blocked_users/{ub_user_id}").remove()
            send_to_user(
                message, f"User unblocked 🔓✅\n \nID: `{ub_user_id}`\nUnblocked Date: {datetime.fromtimestamp(dt)}")

        else:
            send_to_user(message, f"`{ub_user_id}` is already unblocked ✅😐")
    else:
        send_to_user(message, "Sorry! You are not an admin")


# Check Runtime
def check_runtime(message):
    if int(message.chat.id) in Config.ADMIN:
        now = time.time()
        now = math.floor((now - starting_point[0]) * 1000)
        now = TimeFormatter(now)
        send_to_user(message, f"__Bot running time -__ **{now}**")
    pass


# Send cookie via document
@app.on_message(filters.document & filters.private)
def save_my_cookie(app, message):
    user_id = str(message.chat.id)
    create_directory(user_id)
    app.download_media(
        message, file_name=f"./users/{user_id}/{Config.COOKIE_FILE_PATH}")
    send_to_user(message, f"Cookie file saved")


# Downloading the cookie file.
def download_cookie(app, message):
    user_id = message.chat.id
    response = requests.get(Config.COOKIE_URL)
    if response.status_code == 200:
        create_directory(user_id)
        cf = open(f"./users/{user_id}/{Config.COOKIE_FILE_PATH}", "wb")
        cf.write(response.content)
        cf.close()
        send_to_all(message, "**cookie file downloaded.**")
    else:
        send_to_all(message, "Cookie URL is not available!")


# caption editor for videos
@app.on_message(filters.text & filters.private)
def caption_editor(app, message):
    users_name = message.chat.first_name
    user_id = message.chat.id
    caption = message.text
    video_file_id = message.reply_to_message.video.file_id
    info_of_video = f"\n**Caption:** `{caption}`\n**User id:** `{user_id}`\n**User first name:** `{users_name}`\n**Video file id:** `{video_file_id}`"
    # sending to logs
    send_to_logger(message, info_of_video)
    app.send_video(user_id, video_file_id, caption=caption)
    app.send_video(Config.LOGS_ID, video_file_id, caption=caption)


# checking the cookie file
@app.on_message(filters.text & filters.private)
def checking_cookie_file(app, message):
    user_id = message.chat.id
    if os.path.exists(f"./users/{user_id}/{Config.COOKIE_FILE_PATH}"):
        send_to_all(message, f"**Cookie file exists.**")
        cookie = open(f"./users/{user_id}/{Config.COOKIE_FILE_PATH}", "r")
        cookie_content = cookie.read()
        cookie.close()
        send_to_all(
            message, f"**cookie data --->>>>>>>>>>>>>>**\n`{cookie_content}`")
        return
    else:
        send_to_all(message, f"**Cookie file is not found.**")


# updating the cookie file.
@app.on_message(filters.text & filters.private)
def save_as_cookie_file(app, message):
    user_id = message.chat.id
    cookie_with_command_list = message.text.split(
        f"{Config.SAVE_AS_COOKIE_COMMAND} ")
    new_cookie = cookie_with_command_list[1]
    if len(new_cookie) > 0:
        send_to_all(message, f"**user gave a new cookie file.**")
        create_directory(str(user_id))
        cookie = open(f"./users/{user_id}/{Config.COOKIE_FILE_PATH}", "w")
        cookie.write(new_cookie)
        cookie.close()
        send_to_all(
            message, f"**User successfully added a cookie ->>>>>>>**\n`{new_cookie}`")
        return
    else:
        send_to_all(message, f"**not a valid** __cookie.__")


# url extractor
@app.on_message(filters.text & filters.private)
def video_url_extractor(app, message):
    user_id = message.chat.id
    full_string = message.text
    if ("https://" in full_string) or ("http://" in full_string):
        # printing
        users_first_name = message.chat.first_name
        send_to_logger(
            message, f"User entered a **url**\n **user's name:** {users_first_name}\nURL: {full_string}")
        for j in range(len(Config.PORN_LIST)):
            if Config.PORN_LIST[j] in full_string:
                send_to_all(
                    message, "User entered a porn content. Cannot be downloaded.")
                return

        url_with_everything = full_string.split("*")
        url = url_with_everything[0]
        if len(url_with_everything) < 3:
            video_count = 1
            video_start_with = 1
            playlist_name = False
        elif len(url_with_everything) == 3:
            video_count = (
                int(url_with_everything[2]) - int(url_with_everything[1]) + 1)
            video_start_with = int(url_with_everything[1])
            playlist_name = False
        else:
            video_start_with = int(url_with_everything[1])
            playlist_name = f"{url_with_everything[3]}"
            video_count = (
                int(url_with_everything[2]) - int(url_with_everything[1]) + 1)

#############################################################################################################################################
        # Downloading and uploading parts comes here..............
        down_and_up(app, message, url, playlist_name,
                    video_count, video_start_with)

#############################################################################################################################################
    else:
        send_to_all(
            message, f"**User entered like this:** {full_string}\n{Config.ERROR1}")

#############################################################################################

# send message to logger


def send_to_logger(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # print(user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)


# send message to user only
def send_to_user(message, msg):
    user_id = message.chat.id
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)


# send message to all...
def send_to_all(message, msg):
    user_id = message.chat.id
    msg_with_id = f"{message.chat.first_name} - {user_id}\n \n{msg}"
    # print(user_id, "-", msg)
    app.send_message(Config.LOGS_ID, msg_with_id,
                     parse_mode=enums.ParseMode.MARKDOWN)
    app.send_message(user_id, msg, parse_mode=enums.ParseMode.MARKDOWN)


def progress_bar(user_id, msg_id,  msg):
    app.edit_message_text(user_id, (msg_id+1), msg)


def send_videos(message, video_abs_path, caption, duration, thumb_file_path, info_text, msg_id):
    stage = f"Uploading Video... 📤"
    send_to_logger(
        message, f"{info_text}")
    user_id = message.chat.id
    app.send_video(
        chat_id=user_id,
        video=video_abs_path,
        caption=caption,
        # parse_mode="HTML",
        duration=duration,
        width=640,
        height=360,
        supports_streaming=True,
        thumb=thumb_file_path,
        # reply_to_message_id=message.id,
        progress=progress_bar(
            user_id, msg_id, (f"{info_text}\n**Video duration:** __{TimeFormatter(duration * 1000)}__\n \n__{stage}__"))
        # progress_args=(
        #     f"videos is uploading...."
        # Translation.UPLOAD_START,
        # usermsg,
        # start_time
        # )
    )
#####################################################################################


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


def create_directory(dir_name):
    if not os.path.exists("users"):
        os.mkdir("users")
    if not os.path.exists("users/" + dir_name):
        os.mkdir("users/" + dir_name)
        print("Directory ", dir_name,  " Created ")


def split_video_2(dir, video_name, video_path, video_size, max_size, duration):

    rounds = (math.floor(video_size / max_size)) + 1
    n = duration / rounds
    caption_lst = []
    path_lst = []
    for x in range(rounds):
        start_time = x * n
        end_time = (x * n) + n
        cap_name = video_name + " - Part " + str(x + 1)
        target_name = dir + "/" + cap_name + ".mp4"
        video = video_path
        caption_lst.append(cap_name)
        path_lst.append(target_name)
        ffmpeg_extract_subclip(
            video, start_time, end_time, targetname=target_name)
    split_vid_dict = {
        "video": caption_lst,
        "path": path_lst
    }
    print("convert successfull")
    return split_vid_dict


def get_duration_thumb_(dir, video_path, thumb_name):
    thumb_dir = os.path.abspath(dir + "/" + thumb_name + ".jpg")
    clip = VideoFileClip(video_path)
    duration = (int(clip.duration))
    clip.save_frame(thumb_dir, t=2)
    clip.close()
    return duration, thumb_dir


def get_duration_thumb(message, dir, video_path, thumb_name):
    thumb_dir = os.path.abspath(os.path.join(dir, thumb_name + ".jpg"))

    # Run ffmpeg command to capture a frame at 2 seconds into the video
    ffmpeg_command = [
        "ffmpeg",
        "-i", video_path,
        "-ss", "2",  # Seek to 2 seconds into the video
        "-vframes", "1",  # Capture only 1 frame
        thumb_dir
    ]

    # Run ffprobe command to get the video duration
    ffprobe_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        # Execute ffmpeg command to capture thumbnail
        subprocess.run(ffmpeg_command, check=True)

        # Execute ffprobe command to get video duration
        result = subprocess.check_output(
            ffprobe_command, stderr=subprocess.STDOUT, universal_newlines=True)
        duration = int(float(result))

        return duration, thumb_dir
    except subprocess.CalledProcessError as e:
        send_to_all(message,
                    f"Error capturing thumbnail or getting video duration: {e}")


def write_logs(message, video_url, video_title):
    ts = str(math.floor(time.time()))
    data = {"ID": str(message.chat.id), "timestamp": ts,
            "name": message.chat.first_name, "urls": str(video_url), "title": video_title}
    db.child(f"{Config.BOT_DB_PATH}/logs/{str(message.chat.id)}/{ts}").set(data)
    print("Log for user added")
#####################################################################################
#####################################################################################


def down_and_up(app, message, url, playlist_name, video_count, video_start_with):
    # def up_and_down(app, message, )
    user_id = message.chat.id
    msg_id = message.id
    plus_one = msg_id + 1
    app.send_message(user_id, "Processing... ♻️")
    check_user(message)

    create_directory(str(user_id))
    user_dir_name = os.path.abspath("./users/" + str(user_id))

    for x in range(video_count):
        j = ((x + 1) / video_count * 100)
        j_bar = f"{'🟩' * math.floor(j / 10)}{'⬜️' * (10 - math.floor(j / 10))}"
        total_process = f"""
**<<<** __Total progress__ **>>>**

**Video number:** __{x + 1}__
**Total videos:** __{video_count}__

            {j_bar}   __{math.floor(j)}%__"""
        defalt_name = "Defalt name will apply"
        if playlist_name and video_count > 1:
            rename_name = playlist_name + \
                " - Part " + str(x + video_start_with)

        else:
            rename_name = defalt_name

        def my_hook(d):
            if d['status'] == 'error':
                print('some error occured.')
                send_to_all(message, f"Sorry... Some error occured.")

        ytdl_opts = {
            # It will download the best quality video if that is uncomented "prefer_ffmpeg" needs to adjust as True
            # 'format': "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b",
            'format': 'best',
            'prefer_ffmpeg': False,
            'cookiefile': f"./users/{user_id}/{Config.COOKIE_FILE_PATH}",
            'progress_hooks': [my_hook],
            'playlist_items': str(x + video_start_with),
            # now directly download as 'title.mp4'
            'outtmpl': user_dir_name + "/%(title)s.%(ext)s"
        }
        URLS = [url]

        with YoutubeDL(ytdl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_url = info_dict.get("url", None)
            video_id = info_dict.get("id", None)
            video_title = info_dict.get('title', None)
            # video_duration = info_dict.get('duration')

            video_name = str(video_title) + ".mp4"
            info_text = f"""
{total_process}


**<<<** __Info__ **>>>**

**Video number:** {x + video_start_with}
**Video Name:** __{(video_title)}__
**Caption Name:** __{rename_name}__
**Video id:** `{video_id}`"""
            app.edit_message_text(
                user_id, plus_one, f"{info_text}\n \n__Downloading...__ 📥")
            ydl.download(URLS)
            app.edit_message_text(
                user_id, plus_one, f"{info_text}\n \n__Downloaded video. Processing for upload...__ ♻️")
            # write_logs(message, video_url, video_title)
        ###############################################################################################################################
        # uploading part
        # Rename file
        dir = "./users/" + str(user_id)
        allfiles = os.listdir(dir)
        files = [fname for fname in allfiles if fname.endswith('.mp4')]
        files.sort()
        # for i in range(len(files)):
        video_name = files[0]
        write_logs(message, url, video_name)
        # rename_name = (files[i].split(" [")[0])
        if rename_name == defalt_name:
            caption_name = video_name.split(".mp4")[0]
            rename = video_name
        else:
            rename = rename_name + ".mp4"
            caption_name = rename_name
            os.rename(dir + "/" + video_name, dir + "/" + rename)
        user_vid_path = dir + "/" + rename
        ##########################################################################################################################
        after_rename_abs_path = os.path.abspath(user_vid_path)

        duration, thumb_dir = get_duration_thumb(
            message, dir, user_vid_path, caption_name)

        video_size_in_bytes = os.path.getsize(user_vid_path)
        video_size = humanbytes(int(video_size_in_bytes))

        max_size = 1850000000
        if int(video_size_in_bytes) > max_size:
            has_error = True
            app.edit_message_text(
                user_id, plus_one, f"{info_text}\n \n__Your video size ({video_size}) is too large.__\n__Splitting file... __ ✂️")
            returned = split_video_2(dir, caption_name, after_rename_abs_path,
                                     int(video_size_in_bytes), max_size, duration)
            caption_lst = returned.get("video")
            path_lst = returned.get("path")

            for p in range(len(caption_lst)):
                duration, splited_thumb_dir = get_duration_thumb(
                    message, dir, path_lst[p], caption_lst[p])
                send_videos(
                    message, path_lst[p], caption_lst[p], duration, splited_thumb_dir, info_text, msg_id)
                app.edit_message_text(
                    user_id, plus_one, f"{info_text}\n \n__splited {p + 1} file uploaded__")
                app.forward_messages(Config.LOGS_ID, user_id, (msg_id + 2 + p))
                time.sleep(2)
                os.remove(splited_thumb_dir)
                os.remove(path_lst[p])
            os.remove(thumb_dir)
            os.remove(user_vid_path)
            success_msg = f"**Upload complete** - `{video_count}` files uploaded.\n \n__Developed by__ @upekshaip"
            app.edit_message_text(user_id, (msg_id + 1), success_msg)
            break

        else:
            has_error = False
            ############################################################################################################################
            if video_name:
                send_videos(message, after_rename_abs_path, caption_name,
                            duration, thumb_dir, info_text, msg_id)
                # message handling
                app.forward_messages(Config.LOGS_ID, user_id, (msg_id + 2 + x))
                # app.forward_messages(
                #     auto_channel_id, user_id, (msg_id + 2 + i))
                app.edit_message_text(
                    user_id, (msg_id + 1), f"{info_text}\n**Video duration:** __{TimeFormatter(duration * 1000)}__\n \n`{x + 1}` __file uploaded.__")
                if video_name:
                    os.remove(after_rename_abs_path)
                    os.remove(thumb_dir)
                    time.sleep(2)
            else:
                send_to_all(message, "some error occured.😢")

    else:
        success_msg = f"**Upload complete** - `{video_count}` files uploaded.\n \n__Developed by__ @upekshaip"
        app.edit_message_text(user_id, (msg_id + 1), success_msg)
        app.send_message(user_id, success_msg)
#####################################################################################
#####################################################################################
#####################################################################################


# yt-dlp hook
def ytdlp_hook(d):
    print(d['status'])


#####################################################################################
_format = {"ID": '0', "timestamp": math.floor(time.time())}
db.child(f"{Config.BOT_DB_PATH}/users/{str(0)}").set(_format)
db.child(f"{Config.BOT_DB_PATH}/blocked_users/{str(0)}").set(_format)
db.child(f"{Config.BOT_DB_PATH}/unblocked_users/{str(0)}").set(_format)
print("db created")
starting_point.append(time.time())
print("Bot started")
app.run()

from language.languages import Languages as Lang

class TelegramMessageFormatter:

    def create_video_info_format(video_info, formats, lang: str) -> str:
        formated_formats = ""
        for fmt in formats:
            formated_formats += f">{fmt.get('height', 'Unknown')}p: {fmt.get('fps', 'Unknown')}fps - {fmt.get('filesize', 'Unknown')} ({fmt.get('height', 'Unknown')}x{fmt.get('width', 'Unknown')})\n"
        
        message = f"""
📺 **{video_info["channel"]}**

**{video_info["name"]}**

📅 {video_info["upload_date"]}  ⏱️ {video_info["duration"]}
👁 {video_info["view_count"]}  ❤️ {video_info["like_count"]}

>
{formated_formats}
>

{Lang.VIDEO_FORMATS_MESSAGE[lang]}
""".strip()
        return message
    
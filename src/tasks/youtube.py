from yt_dlp import YoutubeDL
from helpers.formatter import Formatter
class YouTubeTask:
    """
    A class to handle YouTube-related tasks.
    """

    def __init__(self):
        pass

    

    def get_available_video_formats(self, url, mp4_only=True):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", []) or []
        out = []
        for f in formats:
            # skip formats that don't have video or audio codecs
            if (f.get("vcodec") == "none") and (f.get("acodec") == "none"):
                continue
            if mp4_only and f.get("ext") not in ("mp4", "m4a"):
                continue
            if (f.get("height") is None and f.get("tbr") is None) or f.get("fps") is None:
                continue
            if ("youtube" in url or "youtu.be" in url) :
                if len(formats) > 3 and 'avc' not in f.get("vcodec"):
                    continue
                if f.get("filesize") is None and f.get("filesize_approx") is None :
                    continue
            
            out.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "height": f.get("height"),
                "width": f.get("width"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "tbr": f.get("tbr"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "format_note": f.get("format_note") or f.get("container") or "",
            })

        out.sort(key=lambda x: (x["height"] or 0, x["tbr"] or 0), reverse=True)
        
        video_info = {
            "name": info.get("title", "Unknown Title"),
            "duration": Formatter.human_time(info.get("duration", 0)),
            "channel": info.get("uploader", "Unknown Uploader"),
            "thumbnail": info.get("thumbnail", ""),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "upload_date": Formatter.format_ytdlp_date(info.get("upload_date", None)),
            "tags": info.get("tags", []),
        }
        return out, video_info
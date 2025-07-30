from datetime import datetime

class Formatter:


    def format_ytdlp_date(date):
        if not date:
            return "Unknown Date"
        dt = datetime.strptime(date, "%Y%m%d")
        formatted = dt.strftime("%d.%m.%Y")
        return formatted

    def human_time(seconds):
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        if h > 0:
            return f"{h}h, {m}m, {s}s" if m or s else f"{h}h"
        if m > 0:
            return f"{m}m, {s}s" if s else f"{m}m"
        return f"{s}s"

#!/usr/bin/env python3
import sys
import os
import re
import yt_dlp
import requests

# Ensure relative imports work when run from repo root
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def extract_info_with_clients(url: str):
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'format': 'best',
        'ignore_no_formats_error': True,
        'sleep-requests': 2,
        'min_sleep_interval': 1,
        'max_sleep_interval': 3,
        'retries': 4,
        'extractor_retries': 2,
    }
    last_info = {}
    # Comment out web and android clients since they never return captions - only tv works
    # for client in ('web', 'android', 'tv', None):
    for client in ('tv', None):  # Only try tv client since it always works
        opts = dict(base_opts)
        if client:
            opts['extractor_args'] = {'youtube': {'player_client': [client]}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError:
            continue
        if info.get('subtitles') or info.get('automatic_captions'):
            return info, (client or 'default')
        last_info = info
    return last_info, 'default'

def timedtext_list(url: str):
    vid = None
    m = re.search(r"[?&]v=([\w-]{11})", url)
    if m:
        vid = m.group(1)
    if not vid:
        m = re.search(r"youtu\.be/([\w-]{11})", url)
        if m:
            vid = m.group(1)
    if not vid:
        return [], []
    r = requests.get(f"https://www.youtube.com/api/timedtext?type=list&v={vid}", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200 or not r.text:
        return [], []
    normal, auto = [], []
    for m in re.finditer(r'<track[^>]*lang_code="([^"]+)"[^>]*>', r.text):
        tag = m.group(0)
        code = m.group(1)
        if 'kind="asr"' in tag or "kind='asr'" in tag:
            auto.append(code)
        else:
            normal.append(code)
    return list(sorted(set(normal))), list(sorted(set(auto)))

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=hJXyd_Sh8ZA"
    print(f"URL: {url}")
    info, client = extract_info_with_clients(url)
    subs = list((info.get('subtitles') or {}).keys())
    autos = list((info.get('automatic_captions') or {}).keys())
    print(f"yt-dlp client={client} -> subtitles={subs} auto={autos}")
    if not subs and not autos:
        tt_norm, tt_auto = timedtext_list(url)
        print(f"timedtext -> normal={tt_norm} auto={tt_auto}")
        if not tt_norm and not tt_auto:
            print("RESULT: No subtitles detected")
            sys.exit(2)
        else:
            print("RESULT: OK via timedtext")
            sys.exit(0)
    else:
        print("RESULT: OK via yt-dlp")
        sys.exit(0)

if __name__ == "__main__":
    main()



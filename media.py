# python, media.py
import yt_dlp
import os
import uuid

async def download_media(url: str, audio_only: bool = False):
    filename = f"media_{uuid.uuid4().hex[:8]}"
    ydl_opts = {
        'outtmpl': f'{filename}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get('ext', 'mp4')
            return f"{filename}.{ext}"
    except Exception as e:
        print(f"Download error: {e}")
        return None
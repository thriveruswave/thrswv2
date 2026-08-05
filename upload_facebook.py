"""
Facebook Reels Upload (Resumable)

Uploads video to the Facebook Page using the Graph API RESUMABLE upload
protocol (upload_phase=start -> transfer -> finish), then verifies the video
actually processed and returns the real permalink URL.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

GRAPH_API = "https://graph.facebook.com/v18.0"
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB default chunk


def _compress_video(video_path):
    """Compress video to under 10MB using ffmpeg."""
    compressed = Path(video_path).parent / "facebook_compressed.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "28",
        "-c:a", "aac",
        "-b:a", "64k",
        "-movflags", "+faststart",
        str(compressed)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = compressed.stat().st_size / (1024 * 1024)
    print(f"[facebook] Compressed to {size_mb:.2f} MB")
    return compressed


def _phase(url, params):
    """POST a resumable-upload phase and return parsed JSON or raise."""
    r = requests.post(url, params=params, timeout=300)
    if r.status_code not in (200, 201):
        err = r.json().get('error', {}).get('message', r.text) if r.text else 'unknown'
        raise Exception(f"Resumable phase failed ({r.status_code}): {err}")
    return r.json()


def _to_int(value):
    """Parse an offset returned by Meta (may be decimal or hex, str or int)."""
    if isinstance(value, int):
        return value
    s = str(value).strip()
    return int(s, 16) if s.lower().endswith(('a', 'b', 'c', 'd', 'e', 'f')) else int(s)


def _upload_resumable(video_path, page_id, access_token, description, title):
    """Resumable-upload a video file to a Facebook Page."""
    url = f"{GRAPH_API}/{page_id}/videos"
    file_size = Path(video_path).stat().st_size

    # Phase 1: start
    print(f"[facebook] Resumable upload START (size {file_size // 1024} KB)...")
    start = _phase(url, {
        'access_token': access_token,
        'upload_phase': 'start',
        'file_size': str(file_size),
        'name': Path(video_path).name,
    })
    upload_session_id = start['upload_session_id']
    start_offset = _to_int(start['start_offset'])
    end_offset = _to_int(start['end_offset'])
    chunk_size = _to_int(start.get('video_file_chunk_size', str(CHUNK_SIZE)))
    print(f"[facebook] Session: {upload_session_id}")

    # Phase 2: transfer (chunked)
    print(f"[facebook] Resumable upload TRANSFER (chunk size {chunk_size // 1024} KB)...")
    with open(video_path, 'rb') as f:
        f.seek(start_offset)
        while start_offset < end_offset:
            data = f.read(min(chunk_size, end_offset - start_offset))
            if not data:
                raise Exception("Read past end of file during transfer")
            t = requests.post(
                url,
                params={
                    'access_token': access_token,
                    'upload_phase': 'transfer',
                    'upload_session_id': upload_session_id,
                    'start_offset': hex(start_offset),
                },
                files={
                    'video_file_chunk': (Path(video_path).name, data, 'video/mp4'),
                },
                timeout=300,
            )
            if t.status_code not in (200, 201):
                err = t.json().get('error', {}).get('message', t.text) if t.text else 'unknown'
                raise Exception(f"Transfer failed: {err}")
            resp = t.json()
            start_offset = _to_int(resp['start_offset'])
            end_offset = _to_int(resp['end_offset'])
            print(f"[facebook] Transferred {start_offset // 1024} KB / {file_size // 1024} KB")

    # Phase 3: finish
    print(f"[facebook] Resumable upload FINISH...")
    fin = _phase(url, {
        'access_token': access_token,
        'upload_phase': 'finish',
        'upload_session_id': upload_session_id,
        'description': description[:500],
        'title': title[:100],
    })
    video_id = fin.get('video_id')
    if not video_id:
        raise Exception(f"Finish response missing video_id: {fin}")
    print(f"[facebook] ✅ Upload accepted, video ID: {video_id}")
    return video_id


def _wait_for_ready(video_id, page_id, access_token, max_polls=4):
    """Check video processing status a few times with long sleeps between checks."""
    sleeps = [60, 45, 45, 45][:max_polls]
    for i in range(max_polls):
        time.sleep(sleeps[i])
        try:
            r = requests.get(
                f"{GRAPH_API}/{video_id}",
                params={
                    'fields': 'status,permalink_url',
                    'access_token': access_token
                },
                timeout=30
            )
            if r.status_code != 200:
                print(f"[facebook] Check [{i+1}/{max_polls}] status query error: {r.text}")
                continue
            d = r.json()
            status = d.get('status', {})
            video_status = status.get('video_status', '')
            phase = status.get('processing_phase', {}).get('status', '')
            print(f"[facebook] Check [{i+1}/{max_polls}]: video_status={video_status} processing={phase}")
            if video_status == 'ready':
                return d.get('permalink_url'), video_status
            if video_status == 'error':
                return d.get('permalink_url'), video_status
        except Exception as e:
            print(f"[facebook] Check [{i+1}/{max_polls}] error: {e}")
    return None, 'processing'


def upload_to_facebook(video_path, description, title="Story"):
    """
    Upload video to Facebook Page using Graph API RESUMABLE upload.
    Verifies the video finished processing and returns the real permalink.
    """
    print("\n" + "=" * 60)
    print("📘 FACEBOOK UPLOAD STARTING (RESUMABLE)")
    print("=" * 60)

    access_token = os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FB_PAGE_ID')

    if not access_token:
        raise ValueError("❌ FB_ACCESS_TOKEN not set")
    if not page_id:
        raise ValueError("❌ FB_PAGE_ID not set")

    print(f"[facebook] ✅ Credentials loaded")
    print(f"[facebook] Page ID: {page_id}")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"❌ Video file not found: {video_path}")

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[facebook] ✅ Video file found: {video_path}")
    print(f"[facebook] Video size: {file_size_mb:.2f} MB")

    # Compress if over 100MB (resumable handles large files, but cap keeps it fast)
    current_video = video_path_obj
    if file_size_mb > 100:
        print(f"[facebook] Video over 100MB, compressing...")
        current_video = _compress_video(current_video)

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"[facebook] 🚀 Attempt {attempt}/{max_attempts}...")
        try:
            video_id = _upload_resumable(
                current_video, page_id, access_token, description, title
            )

            print(f"[facebook] Waiting for video processing...")
            permalink, video_status = _wait_for_ready(video_id, page_id, access_token)

            if current_video != video_path_obj and current_video.exists():
                current_video.unlink()

            if video_status == 'ready' and permalink:
                print(f"[facebook] ✅ SUCCESS! Video published!")
                print(f"[facebook] Video ID: {video_id}")
                print(f"[facebook] Permalink: {permalink}")
                print("=" * 60)
                return {
                    'id': video_id,
                    'platform': 'facebook',
                    'status': 'success',
                    'url': permalink
                }

            if video_status == 'error':
                msg = f"Facebook video {video_id} failed processing (status=error)"
                print(f"[facebook] ❌ {msg}")
                last_error = msg
            else:
                msg = f"Facebook video {video_id} still processing after timeout"
                print(f"[facebook] ⚠️ {msg}")
                last_error = msg

        except Exception as e:
            last_error = str(e)
            print(f"[facebook] ❌ Attempt {attempt} failed: {last_error}")

        if attempt < max_attempts:
            wait = attempt * 15
            print(f"[facebook] Waiting {wait}s before retry...")
            time.sleep(wait)

    print("=" * 60)
    raise Exception(f"Facebook upload failed after {max_attempts} attempts. Last error: {last_error}")

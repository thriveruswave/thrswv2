"""
Facebook Reels Upload

Uploads video to Facebook Page via temporary public URL
(avoids multipart upload size limits that cause error 500).
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

def _upload_to_tmpfiles(video_path):
    """Upload video to tmpfiles.org and return a direct download URL."""
    print(f"[facebook] Uploading to temporary hosting...")
    with open(video_path, 'rb') as f:
        resp = requests.post(
            'https://tmpfiles.org/api/v1/upload',
            files={'file': f},
            timeout=120
        )
    resp.raise_for_status()
    data = resp.json()
    temp_url = data['data']['url']
    # Convert to direct download link
    video_url = temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    print(f"[facebook] ✅ Temporary URL created: {video_url}")
    return video_url

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

def upload_to_facebook(video_path, description, title="Story"):
    """
    Upload video to Facebook Page using URL-based upload.
    Falls back to compression if video is too large.
    """
    print("\n" + "=" * 60)
    print("📘 FACEBOOK UPLOAD STARTING")
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

    # Compress if over 15MB (safer for Facebook)
    current_video = video_path_obj
    if file_size_mb > 15:
        print(f"[facebook] Video over 15MB, compressing...")
        current_video = _compress_video(current_video)

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"[facebook] 🚀 Attempt {attempt}/{max_attempts}...")

        try:
            # Step 1: Upload to tmpfiles.org to get public URL
            video_url = _upload_to_tmpfiles(current_video)

            # Step 2: Tell Facebook to fetch the video from the URL
            print(f"[facebook] Creating Facebook video from URL...")
            fb_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
            data = {
                'access_token': access_token,
                'file_url': video_url,
                'description': description[:500],
                'title': title[:100]
            }
            response = requests.post(fb_url, data=data, timeout=600)

            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')

                print(f"[facebook] ✅ SUCCESS! Video uploaded!")
                print(f"[facebook] Video ID: {video_id}")
                print("=" * 60)

                if current_video != video_path_obj and current_video.exists():
                    current_video.unlink()

                return {
                    'id': video_id,
                    'platform': 'facebook',
                    'status': 'success',
                    'url': f"https://facebook.com/{video_id}"
                }

            # Handle errors
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', 'N/A')
            last_error = f"Facebook API Error {response.status_code}: {error_msg}"

            print(f"[facebook] ❌ Attempt {attempt} failed: {last_error}")

            # If "reduce data" error on URL-based upload too, compress more
            if "reduce the amount of data" in error_msg.lower():
                print(f"[facebook] Reducing video size further...")
                if current_video == video_path_obj or current_video.stat().st_size > 3 * 1024 * 1024:
                    compressed = _compress_video(current_video)
                    if current_video != video_path_obj and current_video.exists():
                        current_video.unlink()
                    current_video = compressed

        except Exception as e:
            last_error = str(e)
            print(f"[facebook] ❌ Attempt {attempt} failed: {last_error}")

        if attempt < max_attempts:
            wait = attempt * 15
            print(f"[facebook] Waiting {wait}s before retry...")
            time.sleep(wait)

    print("=" * 60)
    raise Exception(f"Facebook upload failed after {max_attempts} attempts. Last error: {last_error}")

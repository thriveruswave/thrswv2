"""
Instagram Reels Upload - Using temp hosting services for Public URL
Uploads video via fallback chain of free hosts, then uses URL for Instagram API
"""

import os
import sys
import requests
import time
from pathlib import Path

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

REQ_TIMEOUT = (15, 120)


def upload_to_tempfile(file_path):
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://tmpfiles.org/api/v1/upload',
            files={'file': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"tmpfiles.org failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    if data.get('status') != 'success':
        raise Exception(f"tmpfiles.org failed: {data}")
    return data.get('data', {}).get('url', '').replace('tmpfiles.org/', 'tmpfiles.org/dl/')


def upload_to_0x0(file_path):
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://0x0.st',
            files={'file': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"0x0.st failed: {resp.status_code} {resp.text[:200]}")
    url = resp.text.strip()
    if not url.startswith('https://'):
        raise Exception(f"0x0.st returned invalid URL: {url}")
    return url


def upload_to_catbox(file_path):
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload'},
            files={'fileToUpload': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"catbox.moe failed: {resp.status_code} {resp.text[:200]}")
    url = resp.text.strip()
    if not url.startswith('https://'):
        raise Exception(f"catbox.moe returned invalid URL: {url}")
    return url


def upload_to_uguu(file_path):
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://uguu.se/upload',
            files={'files[]': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"uguu.se failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    if not data.get('success'):
        raise Exception(f"uguu.se failed: {data}")
    return data['files'][0]['url']


HOSTING_SERVICES = [
    ("catbox.moe", upload_to_catbox),
    ("uguu.se", upload_to_uguu),
    ("tmpfiles.org", upload_to_tempfile),
    ("0x0.st", upload_to_0x0),
]


def upload_to_temporary_host(file_path):
    last_error = None
    for name, upload_func in HOSTING_SERVICES:
        try:
            print(f"[instagram] Trying {name}...")
            url = upload_func(file_path)
            print(f"[instagram] Uploaded via {name}: {url}")
            return url
        except Exception as e:
            print(f"[instagram] {name} failed: {e}")
            last_error = e
            continue
    raise Exception(f"All hosting services failed. Last error: {last_error}")


def upload_to_instagram(video_path, caption):
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM UPLOAD STARTING")
    print("=" * 60)

    access_token = os.getenv('IG_ACCESS_TOKEN')
    user_id = os.getenv('IG_USER_ID')

    if not access_token:
        print("[instagram] Skipping - IG_ACCESS_TOKEN not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'instagram'}

    if not user_id:
        print("[instagram] Skipping - IG_USER_ID not set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'instagram'}

    print("[instagram] Credentials loaded")
    print(f"[instagram] User ID: {user_id}")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] Video file: {video_path} ({file_size_mb:.2f} MB)")

    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")

    try:
        print("[instagram] Step 1: Uploading to temporary hosting...")
        video_url = upload_to_temporary_host(video_path_obj)
        print(f"[instagram] Temporary URL: {video_url}")

        print("[instagram] Step 2: Creating Instagram container...")
        container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
        container_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption_limited,
            'share_to_feed': 'false',
            'thumb_offset': '5000',
            'access_token': access_token
        }

        container_response = requests.post(container_url, params=container_params, timeout=60)

        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] Container creation failed: {error_msg}")

            print("[instagram] Retrying with Instagram Graph API endpoint...")
            container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
            container_response = requests.post(container_url, params=container_params, timeout=60)

            if container_response.status_code != 200:
                raise Exception(f"Container Error: {error_msg}")

        container_id = container_response.json().get('id')
        print(f"[instagram] Container created: {container_id}")

        print("[instagram] Step 3: Waiting 60 seconds for processing...")
        time.sleep(60)

        # Step 4: Publish
        print("[instagram] Step 4: Publishing...")
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            print("[instagram] First publish failed, retrying after 30s...")
            time.sleep(30)
            publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response and publish_response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            print(f"[instagram] Publish failed: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")

        media_id = publish_response.json().get("id")

        print("[instagram] SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print("=" * 60)

        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }

    except Exception as e:
        print("[instagram] ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise


if __name__ == '__main__':
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "Test upload")
            print(f"\nSuccess! Result: {result}")
        except Exception as e:
            print(f"\nFailed: {e}")
    else:
        print(f"Video not found: {video_file}")

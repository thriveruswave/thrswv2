"""
Instagram Reels Upload - Using tmpfiles.org for Public URL
Uploads video to tmpfiles.org, then uses URL for Instagram API
"""

import os
import sys
import requests
import time
from pathlib import Path

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def upload_to_instagram(video_path, caption):
    """
    Upload video to Instagram Reels via temporary public URL.
    """
    
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials
    access_token = os.getenv('IG_ACCESS_TOKEN')
    user_id = os.getenv('IG_USER_ID')
    
    if not access_token:
        error_msg = "❌ IG_ACCESS_TOKEN not set"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    if not user_id:
        error_msg = "❌ IG_USER_ID not set"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[instagram] ✅ Credentials loaded")
    print(f"[instagram] User ID: {user_id}")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Upload to tmpfiles.org to get public URL
        print(f"[instagram] 📤 Step 1: Uploading to temporary hosting...")
        
        with open(video_path_obj, 'rb') as video_file:
            files = {'file': ('video.mp4', video_file, 'video/mp4')}
            temp_response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files=files,
                timeout=180
            )
        
        if temp_response.status_code != 200:
            error_msg = f"Failed to upload to temporary hosting: {temp_response.status_code}"
            print(f"[instagram] ❌ {error_msg}")
            print(f"[instagram] Response: {temp_response.text[:200]}")
            raise Exception(error_msg)
        
        temp_data = temp_response.json()
        if temp_data.get('status') != 'success':
            error_msg = f"Temporary hosting failed: {temp_data}"
            print(f"[instagram] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # tmpfiles.org returns URL in format: https://tmpfiles.org/12345
        # We need direct download link: https://tmpfiles.org/dl/12345
        temp_url = temp_data.get('data', {}).get('url', '')
        video_url = temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        
        print(f"[instagram] ✅ Temporary URL created: {video_url}")
        
        # Step 2: Create Instagram container with video URL
        print(f"[instagram] 📦 Step 2: Creating Instagram container...")
        
        container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"
        container_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption_limited,
            'share_to_feed': 'false',
            'access_token': access_token
        }
        
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Container creation failed: {error_msg}")
            print(f"[instagram] Full response: {container_response.text[:500]}")
            raise Exception(f"Instagram Container Error: {error_msg}")
        
        container_id = container_response.json().get('id')
        print(f"[instagram] ✅ Container created: {container_id}")
        
        # Step 3: Wait for processing
        print(f"[instagram] ⏳ Step 3: Waiting for video processing...")
        max_wait = 120
        waited = 0
        
        while waited < max_wait:
            status_url = f"https://graph.facebook.com/v18.0/{container_id}"
            status_params = {
                'fields': 'status_code',
                'access_token': access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_data = status_response.json()
            status_code = status_data.get('status_code', 'UNKNOWN')
            
            print(f"[instagram] Status: {status_code} (waited {waited}s)")
            
            if status_code == 'FINISHED':
                print(f"[instagram] ✅ Video processing complete!")
                break
            elif status_code == 'ERROR':
                error_msg = status_data.get('error_message', 'Video processing failed')
                print(f"[instagram] ❌ {error_msg}")
                raise Exception(error_msg)
            
            time.sleep(10)
            waited += 10
        
        if waited >= max_wait:
            error_msg = "Video processing timed out"
            print(f"[instagram] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # Step 4: Publish
        print(f"[instagram] 📤 Step 4: Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Publish failed: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")
        
        media_id = publish_response.json().get('id')
        
        print(f"[instagram] ✅ SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print(f"[instagram] Check your Instagram profile to see the Reel!")
        print("=" * 60)
        
        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }
        
    except Exception as e:
        print(f"[instagram] ❌ ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "Test upload")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")

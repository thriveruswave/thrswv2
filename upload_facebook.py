"""
Facebook Reels Upload

Facebook Graph API for uploading Reels to Facebook Page.
Enhanced with comprehensive debugging and error handling.
"""

import os
import sys
import requests
from pathlib import Path

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def upload_to_facebook(video_path, description, title="История древних женщин"):
    """
    Upload video to Facebook Page.
    
    Returns dict with upload status and details.
    """
    
    print("\n" + "=" * 60)
    print("📘 FACEBOOK UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials
    access_token = os.getenv('FB_ACCESS_TOKEN')
    page_id = os.getenv('FB_PAGE_ID')
    
    if not access_token:
        error_msg = "❌ FB_ACCESS_TOKEN not set in environment variables"
        print(f"[facebook] {error_msg}")
        raise ValueError(error_msg)
    
    if not page_id:
        error_msg = "❌ FB_PAGE_ID not set in environment variables"
        print(f"[facebook] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[facebook] ✅ Credentials loaded")
    print(f"[facebook] Page ID: {page_id}")
    print(f"[facebook] Token: {access_token[:20]}...")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[facebook] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[facebook] ✅ Video file found: {video_path}")
    print(f"[facebook] Video size: {file_size_mb:.2f} MB")
    
    # Upload video
    print(f"[facebook] 🚀 Uploading to Facebook Page...")
    url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
    
    try:
        with open(video_path, 'rb') as video:
            files = {'file': video}
            data = {
                'access_token': access_token,
                'description': description[:500],  # Limit description length
                'title': title[:100],  # Use dynamic title, limit to 100 chars
                'is_explicit_share': True
            }
            
            print(f"[facebook] Sending request to Facebook API...")
            response = requests.post(url, files=files, data=data, timeout=300)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                
                print(f"[facebook] ✅ SUCCESS! Video uploaded!")
                print(f"[facebook] Video ID: {video_id}")
                print(f"[facebook] Check your Facebook Page to see the post!")
                print("=" * 60)
                
                return {
                    'id': video_id,
                    'platform': 'facebook',
                    'status': 'success',
                    'url': f"https://facebook.com/{video_id}"
                }
            else:
                # Handle error response
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', 'N/A')
                
                print(f"[facebook] ❌ UPLOAD FAILED!")
                print(f"[facebook] Status Code: {response.status_code}")
                print(f"[facebook] Error Code: {error_code}")
                print(f"[facebook] Error Message: {error_msg}")
                print(f"[facebook] Full Response: {response.text[:500]}")
                
                # Provide helpful error messages
                if error_code == 190:
                    print(f"[facebook] 💡 Token expired or invalidated!")
                    print(f"[facebook] 💡 Solution: Generate a new access token")
                    print(f"[facebook] 💡 Go to: https://developers.facebook.com/tools/explorer/")
                
                print("=" * 60)
                
                raise Exception(f"Facebook API Error {response.status_code}: {error_msg}")
                
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Upload timed out (video too large or slow connection)"
        print(f"[facebook] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"🌐 Connection error: {str(e)}"
        print(f"[facebook] ❌ {error_msg}")
        print("=" * 60)
        raise Exception(error_msg)
        
    except Exception as e:
        print(f"[facebook] ❌ UNEXPECTED ERROR!")
        print(f"[facebook] Error type: {type(e).__name__}")
        print(f"[facebook] Error message: {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    # Test upload
    from pathlib import Path
    
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        story_file = Path('output/story.txt')
        description = story_file.read_text(encoding='utf-8') if story_file.exists() else "Test upload"
        
        try:
            result = upload_to_facebook(video_file, description)
            print(f"\n✅ Test successful! Result: {result}")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")

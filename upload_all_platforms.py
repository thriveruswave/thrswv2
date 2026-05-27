"""
Multi-Platform Upload Script

Uploads videos to:
- YouTube Shorts
- Instagram Reels
- TikTok
- Facebook Reels

Each platform requires its own API credentials.
"""

import os
import sys
from pathlib import Path
import datetime

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import platform-specific uploaders
from upload_to_youtube import upload_to_youtube
from upload_instagram import upload_to_instagram
from upload_tiktok import upload_to_tiktok
from upload_facebook import upload_to_facebook
from upload_threads import upload_to_threads
from upload_twitter import upload_to_twitter
from upload_vk import upload_to_vk

def main():
    """Upload video to all configured platforms."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[upload] ❌ No video found at output/final_video.mp4")
        return
    
    # Read topic for title
    topic_file = Path('output/topic.txt')
    if topic_file.exists():
        title = topic_file.read_text(encoding='utf-8').strip()
    else:
        title = "История древних женщин"
    
    # Read story for description
    story_file = Path('output/story.txt')
    if story_file.exists():
        story = story_file.read_text(encoding='utf-8')
        
        # Create dynamic description from story
        # Use first 2-3 sentences for description
        sentences = [s.strip() for s in story.split('.') if s.strip()]
        description_text = '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else story[:200]
        
        # Add hashtags
        description = f"""{description_text}

#shorts #историяженщин #древняяистория #историческиефакты #древниймир"""
    else:
        description = f"""Интересный факт из истории древних женщин.

#shorts #историяженщин #древняяистория"""
    
    tags = [
        'История', 'Древние женщины', 'Исторические факты',
        'Shorts', 'Reels', 'ИИ', 'Образование'
    ]
    
    results = {}
    
    # Upload to YouTube
    if all([
        os.getenv('YT_CLIENT_ID'),
        os.getenv('YT_CLIENT_SECRET'),
        os.getenv('YT_REFRESH_TOKEN')
    ]):
        print("\n" + "="*60)
        print("📺 Uploading to YouTube...")
        print("="*60)
        try:
            result = upload_to_youtube(video_file, title, description, tags)
            results['youtube'] = result
            print(f"✅ YouTube: https://youtube.com/shorts/{result['id']}")
        except Exception as e:
            print(f"❌ YouTube failed: {e}")
            results['youtube'] = None
    else:
        print("⏭️  Skipping YouTube (credentials not set)")
    
    # Upload to Instagram
    if all([
        os.getenv('IG_ACCESS_TOKEN'),
        os.getenv('IG_USER_ID')
    ]):
        print("\n" + "="*60)
        print("📸 Uploading to Instagram...")
        print("="*60)
        try:
            result = upload_to_instagram(video_file, description)
            results['instagram'] = result
            print(f"✅ Instagram: Uploaded successfully")
        except Exception as e:
            print(f"❌ Instagram failed: {e}")
            results['instagram'] = None
    else:
        print("⏭️  Skipping Instagram (credentials not set)")
    
    # Upload to TikTok
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        print("\n" + "="*60)
        print("🎵 Uploading to TikTok...")
        print("="*60)
        try:
            result = upload_to_tiktok(video_file, title, description)
            results['tiktok'] = result
            print(f"✅ TikTok: Uploaded successfully")
        except Exception as e:
            print(f"❌ TikTok failed: {e}")
            results['tiktok'] = None
    else:
        print("⏭️  Skipping TikTok (credentials not set)")
    
    # Upload to Facebook
    if all([
        os.getenv('FB_ACCESS_TOKEN'),
        os.getenv('FB_PAGE_ID')
    ]):
        print("\n" + "="*60)
        print("📘 Uploading to Facebook...")
        print("="*60)
        try:
            result = upload_to_facebook(video_file, description, title)
            results['facebook'] = result
            print(f"✅ Facebook: Uploaded successfully")
        except Exception as e:
            print(f"❌ Facebook failed: {e}")
            results['facebook'] = None
    else:
        print("⏭️  Skipping Facebook (credentials not set)")
    
    # Upload to Threads
    print("\n" + "="*60)
    print("🧵 Checking Threads credentials...")
    print("="*60)
    
    threads_token = os.getenv('THREADS_ACCESS_TOKEN')
    threads_user_id = os.getenv('THREADS_USER_ID')
    
    # Debug: Show which credentials are set
    print(f"[threads] Access Token: {'✅ Set' if threads_token else '❌ Not set'}")
    print(f"[threads] User ID: {'✅ Set' if threads_user_id else '❌ Not set'}")
    
    if threads_token and threads_user_id:
        print(f"[threads] ✅ All credentials present!")
        print(f"[threads] 🚀 Starting upload...")
        try:
            result = upload_to_threads(video_file, description)
            results['threads'] = result
            print(f"\n✅ Threads: Upload successful!")
            print(f"   Thread ID: {result.get('id', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Threads upload FAILED!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            results['threads'] = None
    else:
        print(f"[threads] ⏭️  Skipping Threads (credentials not set)")
        print(f"[threads] Missing credentials - add to GitHub Secrets:")
        if not threads_token:
            print(f"   - THREADS_ACCESS_TOKEN")
        if not threads_user_id:
            print(f"   - THREADS_USER_ID")
        results['threads'] = None
    
    # Upload to Twitter/X
    print("\n" + "="*60)
    print("🐦 Checking Twitter/X credentials...")
    print("="*60)
    
    twitter_api_key = os.getenv('TWITTER_API_KEY')
    twitter_api_secret = os.getenv('TWITTER_API_SECRET')
    twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    # Debug: Show which credentials are set
    print(f"[twitter] API Key: {'✅ Set' if twitter_api_key else '❌ Not set'}")
    print(f"[twitter] API Secret: {'✅ Set' if twitter_api_secret else '❌ Not set'}")
    print(f"[twitter] Access Token: {'✅ Set' if twitter_access_token else '❌ Not set'}")
    print(f"[twitter] Access Secret: {'✅ Set' if twitter_access_secret else '❌ Not set'}")
    
    if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_secret]):
        print(f"[twitter] ✅ All credentials present!")
        print(f"[twitter] 🚀 Starting upload...")
        try:
            result = upload_to_twitter(video_file, description)
            results['twitter'] = result
            print(f"\n✅ Twitter: Upload successful!")
            print(f"   Tweet ID: {result.get('id', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Twitter upload FAILED!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            print(f"   Full error: {repr(e)}")
            
            # Show troubleshooting tips
            print(f"\n🔍 Troubleshooting:")
            print(f"   - Check if Twitter credentials are correct in GitHub Secrets")
            print(f"   - Verify Twitter app has 'Read and Write' permissions")
            print(f"   - Check if Access Token was regenerated after permission change")
            print(f"   - Verify video file exists and is valid")
            
            results['twitter'] = None
    else:
        print(f"[twitter] ⏭️  Skipping Twitter (credentials not set)")
        print(f"[twitter] Missing credentials - add to GitHub Secrets:")
        if not twitter_api_key:
            print(f"   - TWITTER_API_KEY")
        if not twitter_api_secret:
            print(f"   - TWITTER_API_SECRET")
        if not twitter_access_token:
            print(f"   - TWITTER_ACCESS_TOKEN")
        if not twitter_access_secret:
            print(f"   - TWITTER_ACCESS_SECRET")
        results['twitter'] = None
    
    # Upload to VK
    print("\n" + "="*60)
    print("🇷🇺 Checking VK credentials...")
    print("="*60)
    
    vk_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    
    # Debug: Show which credentials are set
    print(f"[vk] Access Token: {'✅ Set' if vk_token else '❌ Not set'}")
    print(f"[vk] Group ID: {'✅ Set' if vk_group_id else '❌ Not set'}")
    
    if vk_token and vk_group_id:
        print(f"[vk] ✅ All credentials present!")
        print(f"[vk] 🚀 Starting upload...")
        try:
            result = upload_to_vk(video_file, description, title)
            results['vk'] = result
            print(f"\n✅ VK: Upload successful!")
            print(f"   Post URL: {result.get('post_url', 'N/A')}")
        except Exception as e:
            print(f"\n❌ VK upload FAILED!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            results['vk'] = None
    else:
        print(f"[vk] ⏭️  Skipping VK (credentials not set)")
        print(f"[vk] Missing credentials - add to GitHub Secrets:")
        if not vk_token:
            print(f"   - VK_ACCESS_TOKEN")
        if not vk_group_id:
            print(f"   - VK_GROUP_ID")
        results['vk'] = None

    # Summary
    print("\n" + "="*60)
    print("📊 Upload Summary")
    print("="*60)
    for platform, result in results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"{platform.capitalize()}: {status}")
    print("="*60)

if __name__ == '__main__':
    main()

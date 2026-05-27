"""
Twitter/X Upload Script

Uploads videos to Twitter/X using Twitter API (Free Tier Compatible!)

Requirements:
- Twitter Developer Account (FREE tier works!)
- TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

Free Tier Limits:
- 500-1,500 posts per month
- Video size: max 512 MB
- Video duration: max 140 seconds (2m 20s)
- Format: MP4 (H.264 + AAC audio)
"""

import os
import sys
from pathlib import Path
import tweepy
import time

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def upload_to_twitter(video_file, caption):
    """Upload video to Twitter/X using API v1.1 (media) + v2 (post)."""
    
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    if not all([api_key, api_secret, access_token, access_secret]):
        raise ValueError(
            "Missing Twitter credentials! Set these environment variables:\n"
            "  - TWITTER_API_KEY\n"
            "  - TWITTER_API_SECRET\n"
            "  - TWITTER_ACCESS_TOKEN\n"
            "  - TWITTER_ACCESS_SECRET\n"
            "\nGet these from: https://developer.x.com/en/portal/dashboard"
        )
    
    print("[twitter] 🐦 Uploading to Twitter/X...")
    
    # Check video file exists and size
    video_path = Path(video_file)
    if not video_path.exists():
        raise FileNotFoundError(f"[twitter] ❌ Video file not found: {video_file}")
    
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"[twitter] Video size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 512:
        raise ValueError(f"[twitter] ❌ Video too large ({file_size_mb:.2f} MB). Max: 512 MB")
    
    try:
        # Authenticate with Twitter API v1.1 for media upload
        print("[twitter] Authenticating with API v1.1 (media upload)...")
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret,
            access_token, access_secret
        )
        api_v1 = tweepy.API(auth)
        
        # Authenticate with Twitter API v2 for posting
        print("[twitter] Authenticating with API v2 (posting)...")
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        
        # Upload video (uses v1.1 API - works with FREE tier!)
        print("[twitter] Uploading video (this may take a minute)...")
        media = api_v1.media_upload(
            filename=str(video_file),
            media_category='tweet_video',
            chunked=True  # Use chunked upload for reliability
        )
        
        print(f"[twitter] ✅ Video uploaded! Media ID: {media.media_id}")
        
        # Wait for video processing (X needs time to process video)
        print("[twitter] Waiting for video processing...")
        time.sleep(5)  # Give X time to process the video
        
        # Create tweet with video (uses v2 API)
        print("[twitter] Posting tweet...")
        
        # Twitter has 280 character limit
        tweet_text = caption[:280] if len(caption) > 280 else caption
        
        response = client.create_tweet(
            text=tweet_text,
            media_ids=[media.media_id]
        )
        
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
        
        print(f"[twitter] ✅ Posted to Twitter!")
        print(f"[twitter] Tweet ID: {tweet_id}")
        print(f"[twitter] URL: {tweet_url}")
        
        return {
            'id': tweet_id,
            'url': tweet_url,
            'platform': 'twitter'
        }
        
    except tweepy.errors.Unauthorized as e:
        print(f"[twitter] ❌ Authentication failed!")
        print(f"[twitter] Error: {e}")
        print(f"[twitter] Check your credentials and app permissions at:")
        print(f"[twitter] https://developer.x.com/en/portal/dashboard")
        raise
        
    except tweepy.errors.Forbidden as e:
        print(f"[twitter] ❌ Permission denied!")
        print(f"[twitter] Error: {e}")
        print(f"[twitter] Make sure your app has 'Read and Write' permissions")
        raise
        
    except tweepy.errors.TooManyRequests as e:
        print(f"[twitter] ❌ Rate limit exceeded!")
        print(f"[twitter] Error: {e}")
        print(f"[twitter] Free tier: 500-1,500 posts/month. Wait and try again later.")
        raise
        
    except tweepy.errors.BadRequest as e:
        print(f"[twitter] ❌ Bad request!")
        print(f"[twitter] Error: {e}")
        print(f"[twitter] Possible issues:")
        print(f"[twitter]   - Video format not supported (need MP4 with H.264)")
        print(f"[twitter]   - Video too long (max 140 seconds for free tier)")
        print(f"[twitter]   - Invalid media_id or caption")
        raise
        
    except Exception as e:
        print(f"[twitter] ❌ Unexpected error: {e}")
        print(f"[twitter] Error type: {type(e).__name__}")
        raise

def main():
    """Test upload to Twitter."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[twitter] ❌ No video found at output/final_video.mp4")
        return
    
    # Read story for caption
    story_file = Path('output/story.txt')
    if story_file.exists():
        story = story_file.read_text(encoding='utf-8')
        # Create short caption for Twitter
        first_sentence = story.split('.')[0] if '.' in story else story[:200]
        caption = f"{first_sentence}... 🏛️\n\n#История #ДревниеЖенщины"
    else:
        caption = "История древних женщин 🏛️ #История #ДревниеЖенщины"
    
    try:
        upload_to_twitter(video_file, caption)
    except Exception as e:
        print(f"[twitter] ❌ Upload failed: {e}")
        raise

if __name__ == '__main__':
    main()

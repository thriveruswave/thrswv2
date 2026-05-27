"""
YouTube Upload Script - Updated for 2025

Uses refresh token from GitHub Secrets to upload videos.
"""

import os
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import datetime

# Configure UTF-8 encoding for console output (fixes Russian text display)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def get_authenticated_service():
    """Authenticate using refresh token from environment."""
    
    # Get credentials from GitHub Secrets
    client_id = os.getenv('YT_CLIENT_ID')
    client_secret = os.getenv('YT_CLIENT_SECRET')
    refresh_token = os.getenv('YT_REFRESH_TOKEN')
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing credentials! Set these GitHub Secrets:\n"
            "  - YT_CLIENT_ID\n"
            "  - YT_CLIENT_SECRET\n"
            "  - YT_REFRESH_TOKEN"
        )
    
    # Create credentials from refresh token
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
    
    # Refresh to get access token
    creds.refresh(Request())
    
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_file, title, description, tags, category_id='22'):
    """Upload video to YouTube and return result."""
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }
    
    if '#Shorts' not in body['snippet']['description']:
        body['snippet']['description'] += '\n\n#Shorts'
    
    media = MediaFileUpload(
        str(video_file),
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )
    
    print(f"[youtube] Uploading: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube] Progress: {int(status.progress() * 100)}%")
    
    print(f"[youtube] ✅ Uploaded! Video ID: {response['id']}")
    print(f"[youtube] URL: https://youtube.com/shorts/{response['id']}")
    
    return response

def main():
    """Upload the generated video to YouTube."""
    video_file = Path('output/final_video.mp4')
    
    if not video_file.exists():
        print("[youtube] ❌ No video found at output/final_video.mp4")
        return
    
    # Read the story for a specific, descriptive title
    story_file = Path('output/story.txt')
    
    # Read story with proper UTF-8 encoding
    if story_file.exists():
        # Read with UTF-8 encoding and ensure proper decoding
        with open(story_file, 'r', encoding='utf-8') as f:
            story = f.read().strip()
        
        # Extract first meaningful sentence as title
        sentences = [s.strip() for s in story.split('.') if s.strip()]
        if sentences:
            first_sentence = sentences[0]
            # Create specific, descriptive title (max 60 chars for mobile)
            title = first_sentence[:57] + "..." if len(first_sentence) > 60 else first_sentence
        else:
            title = story[:60] if len(story) > 60 else story
    else:
        title = "История древних женщин"
    
    # Make title more specific and engaging if too short
    if len(title) < 20:
        title = f"{title} | Древняя История"
    
    # Create description from first 2-3 sentences
    if story_file.exists():
        with open(story_file, 'r', encoding='utf-8') as f:
            story = f.read().strip()
        sentences = [s.strip() for s in story.split('.') if s.strip()]
        description_text = '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else story[:200]
        description = f"""{description_text}

#shorts #историяженщин #древняяистория #историческиефакты #древниймир"""
    else:
        description = "#Shorts #ИсторияЖенщин #ДревняяИстория"
    
    tags = [
        'История', 'Древние женщины', 'Исторические факты',
        'Shorts', 'ИИ', 'Образование', 'Древний мир'
    ]
    
    # Upload
    try:
        upload_to_youtube(
            video_file=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id='22'
        )
    except Exception as e:
        print(f"[youtube] ❌ Upload failed: {e}")
        raise

if __name__ == '__main__':
    main()

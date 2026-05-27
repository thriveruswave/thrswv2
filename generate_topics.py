"""
Generate new topics using AI when topics.txt runs low.

This script:
1. Checks if topics.txt has enough topics (< 50 remaining)
2. Generates 100 new unique topics using Pollinations AI PAID API
3. Appends them to topics.txt
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
TEXT_MODEL = "mistral"  # Works great with Russian text

def generate_new_topics(count=100):
    """Generate new Russian topics about ancient women using PAID API."""
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY not set! Get your API key from https://enter.pollinations.ai")
    
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Ты историк, специализирующийся на истории женщин в древних цивилизациях. "
        f"Создай список из {count} уникальных тем на русском языке. "
        "Каждая тема должна быть короткой (5-10 слов), интересной и образовательной. "
        "Темы должны охватывать: законы, обычаи, известных женщин, профессии, религию, культуру, искусство. "
        "Выводи ТОЛЬКО темы, по одной на строку, без номеров и маркеров."
    )
    
    user_prompt = f"Создай {count} уникальных тем о женщинах в древних цивилизациях"
    
    payload = {
        "model": TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 2000
    }
    
    print(f"[topics] Generating {count} new topics with {TEXT_MODEL} (PAID API)...")
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    
    response_data = r.json()
    
    # Extract text from OpenAI-compatible response
    if "choices" in response_data and len(response_data["choices"]) > 0:
        text = response_data["choices"][0]["message"]["content"].strip()
    else:
        raise ValueError("Invalid response format from API")
    
    # Parse topics
    topics = []
    for line in text.strip().split('\n'):
        # Remove numbering and clean
        cleaned = line.strip()
        # Remove common prefixes
        for prefix in ['- ', '* ', '• ']:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        # Remove numbering like "1. " or "1) "
        import re
        cleaned = re.sub(r'^\d+[\.\:\)]\s*', '', cleaned)
        
        if cleaned and len(cleaned) > 5:
            topics.append(cleaned)
    
    print(f"[topics] ✅ Generated {len(topics)} topics")
    return topics[:count]

def check_and_update_topics():
    """Check topics.txt and add more if needed."""
    
    topics_file = Path('topics.txt')
    
    # Read existing topics
    if topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            existing_topics = [line.strip() for line in f if line.strip()]
    else:
        existing_topics = []
    
    print(f"[topics] Current topics: {len(existing_topics)}")
    
    # Check if we need more topics
    if len(existing_topics) < 50:
        print(f"[topics] Low on topics! Generating 100 more...")
        
        new_topics = generate_new_topics(100)
        
        # Append to file
        with open(topics_file, 'a', encoding='utf-8') as f:
            for topic in new_topics:
                f.write(f"{topic}\n")
        
        print(f"[topics] Added {len(new_topics)} new topics!")
        print(f"[topics] Total topics now: {len(existing_topics) + len(new_topics)}")
    else:
        print(f"[topics] Enough topics available ({len(existing_topics)})")

if __name__ == '__main__':
    check_and_update_topics()

"""
AUTOMATED HISTORICAL VIDEO MULTI-PLATFORM UPLOADER
Supports: YouTube, Instagram Reels, Facebook, VK, Telegram, Twitter, Threads, TikTok
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

root = Path(__file__).parent
upload_dir = root / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

uploaders = {}
modules = [
    ("upload_facebook", "upload_to_facebook", "fb"),
    ("upload_instagram", "upload_to_instagram", "ig"),
    ("upload_to_youtube", "upload_to_youtube", "yt"),
    ("upload_vk", "upload_to_vk", "vk"),
    ("upload_telegram", "upload_to_telegram", "tg"),
    ("upload_twitter", "upload_to_twitter", "tw"),
    ("upload_threads", "upload_to_threads", "th"),
    ("upload_tiktok", "upload_to_tiktok", "tk"),
]
for mod_name, func_name, key in modules:
    for prefix in ["upload.", ""]:
        try:
            mod = __import__(prefix + mod_name, fromlist=[func_name])
            uploaders[key] = getattr(mod, func_name)
            break
        except ImportError:
            continue
    if not uploaders.get(key):
        print(f"[!] {mod_name} module not loaded")


def get_latest_video():
    """Find generated video file and metadata."""
    fv = Path("output/final_video.mp4")
    if fv.exists():
        meta = {"story": "", "story_ru": "", "topic": ""}
        
        tp = Path("output/topic.txt")
        if tp.exists():
            meta["topic"] = tp.read_text(encoding="utf-8").strip()
            
        st = Path("output/story.txt")
        if st.exists():
            meta["story_ru"] = st.read_text(encoding="utf-8").strip()
            
        se = Path("output/story_en.txt")
        if se.exists():
            meta["story"] = se.read_text(encoding="utf-8").strip()
            
        return {
            "video_path": str(fv),
            "topic": meta.get("topic") or "Ancient History",
            "metadata": meta
        }
        
    video_dir = Path("output/video")
    if video_dir.exists():
        reels = list(video_dir.glob("*/final_reel.mp4"))
        if reels:
            latest = max(reels, key=lambda p: p.stat().st_mtime)
            meta = {}
            mf = latest.parent / "metadata.json"
            if mf.exists():
                with open(mf, encoding="utf-8") as f:
                    meta = json.load(f)
            return {
                "video_path": str(latest),
                "topic": meta.get("topic", meta.get("category_english", "Ancient History")),
                "metadata": meta
            }
            
    return None


def generate_caption(topic, metadata=None, platform="facebook"):
    """Generate a clean historical video caption with hashtags."""
    topic_str = topic or "Ancient History"
    story_ru = metadata.get("story_ru", "") if metadata else ""
    story_en = metadata.get("story", "") if metadata else ""
    
    base = [f"📜 {topic_str}", ""]
    
    if story_ru:
        base.append(story_ru.strip())
        base.append("")
        
    if story_en and story_en != story_ru:
        base.append("--- English Translation ---")
        base.append("")
        base.append(story_en.strip())
        base.append("")
        
    base.extend([
        "Like & follow for daily history facts! 🏛️✨",
        "",
        "#history #ancienthistory #historyfacts #historylovers #historical #ancient"
    ])
    
    return "\n".join(base)


def upload_to_all_platforms(video_path, caption, topic, metadata=None):
    results = {
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "video": video_path,
        "uploads": {},
        "platforms_attempted": [],
        "platforms_successful": [],
        "platforms_skipped": [],
        "platforms_failed": [],
        "timing": {}
    }
    
    print("\n" + "="*80)
    print(f"HISTORICAL VIDEO MULTI-PLATFORM UPLOADER - Topic: {topic}")
    print("="*80)
    
    if not Path(video_path).exists():
        print(f"❌ Video not found: {video_path}")
        return results
        
    platforms = [
        ("youtube", "yt", "YouTube"),
        ("facebook", "fb", "Facebook"),
        ("instagram", "ig", "Instagram"),
        ("vk", "vk", "VK"),
        ("telegram", "tg", "Telegram"),
        ("twitter", "tw", "Twitter"),
        ("threads", "th", "Threads"),
        ("tiktok", "tk", "TikTok")
    ]
    
    for pname, key, dname in platforms:
        results["platforms_attempted"].append(pname)
        func = uploaders.get(key)
        if func or pname == "youtube":
            try:
                t_start = datetime.now()
                print(f"\n🚀 Uploading to {dname}...")
                
                if pname == "youtube":
                    from upload_to_youtube import upload_to_youtube
                    tags = ["История", "Древний мир", "Женщины в истории", "History", "Ancient History"]
                    r = upload_to_youtube(video_file=video_path, title=topic[:100], description=caption, tags=tags)
                elif pname == "vk":
                    r = func(video_path=video_path, description=caption)
                elif pname == "telegram":
                    r = func(video_path=video_path, caption=caption)
                elif pname == "twitter":
                    r = func(video_file=video_path, caption=caption)
                elif pname == "threads":
                    r = func(video_path=video_path, text=caption)
                elif pname == "tiktok":
                    r = func(video_file=video_path, title=topic[:100], description=caption)
                elif pname == "facebook":
                    r = func(video_path=video_path, description=caption)
                elif pname == "instagram":
                    r = func(video_path=video_path, caption=caption, is_story=False)
                    
                t_end = datetime.now()
                t_sec = round((t_end - t_start).total_seconds())
                results["timing"][pname] = f"{t_sec}s"
                
                if r:
                    results["uploads"][pname] = r
                    results["platforms_successful"].append(pname)
                    print(f"✅ {dname}: SUCCESS")
                else:
                    results["platforms_failed"].append(pname)
                    print(f"❌ {dname}: FAILED")
            except Exception as e:
                results["uploads"][pname] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(pname)
                print(f"❌ {dname}: ERROR ({e})")
        else:
            results["uploads"][pname] = {"status": "skipped"}
            results["platforms_skipped"].append(pname)
            
    s = len(results["platforms_successful"])
    f = len(results["platforms_failed"])
    sk = len(results["platforms_skipped"])
    print(f"\n" + "="*80)
    print(f"SUMMARY: {s} successful, {f} failed, {sk} skipped")
    print("="*80)
    
    rf = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    rf.parent.mkdir(exist_ok=True)
    with open(rf, "w", encoding="utf-8") as f_out:
        json.dump(results, f_out, indent=2, ensure_ascii=False)
        
    return results


def main():
    print("\n" + "="*80)
    print("HISTORICAL VIDEO - AUTOMATED MULTI-PLATFORM UPLOADER")
    print("="*80)
    
    vdata = get_latest_video()
    if not vdata:
        print("❌ No video file found in output/ directory.")
        sys.exit(1)
        
    caption = generate_caption(vdata['topic'], vdata.get('metadata'))
    upload_to_all_platforms(vdata['video_path'], caption, vdata['topic'], vdata.get('metadata'))

if __name__ == "__main__":
    main()

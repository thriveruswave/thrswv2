"""
Diagnostic for the multi-platform uploader.
Prints, for each platform, whether credentials are set, and resolves the
actual Facebook Page name/ID and connected Instagram business account so you
can see exactly where videos are being published.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def _set_or_missing(name):
    return "SET" if os.getenv(name) else "MISSING"


def main():
    print("=" * 70)
    print("PLATFORM DIAGNOSTIC")
    print("=" * 70)

    secrets = [
        "YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN",
        "IG_ACCESS_TOKEN", "IG_USER_ID", "INSTAGRAM_ACCOUNT_ID",
        "FB_ACCESS_TOKEN", "FB_PAGE_ID",
        "THREADS_ACCESS_TOKEN", "THREADS_USER_ID",
        "TWITTER_API_KEY", "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET",
        "VK_ACCESS_TOKEN", "VK_GROUP_ID",
        "TIKTOK_ACCESS_TOKEN",
    ]
    for name in secrets:
        print(f"  {name}: {_set_or_missing(name)}")

    token = (os.getenv("FB_ACCESS_TOKEN") or
             os.getenv("IG_ACCESS_TOKEN") or
             os.getenv("INSTAGRAM_ACCESS_TOKEN"))
    page_id = os.getenv("FB_PAGE_ID") or os.getenv("FACEBOOK_PAGE_ID")

    if not token or not page_id:
        print("\n[diag] No FB token/page id -> cannot resolve target page/account.")
        return

    print("\n--- Resolving Facebook Page ---")
    try:
        r = requests.get(
            f"https://graph.facebook.com/v18.0/{page_id}",
            params={"fields": "name,id,link", "access_token": token},
            timeout=30,
        )
        if r.status_code == 200:
            d = r.json()
            print(f"[diag] Facebook Page: {d.get('name')} (id {d.get('id')})")
            print(f"[diag] Page link: {d.get('link')}")
        else:
            print(f"[diag] Page lookup failed: {r.text}")
    except Exception as e:
        print(f"[diag] Page lookup error: {e}")

    print("\n--- Resolving connected Instagram Business account ---")
    try:
        r = requests.get(
            f"https://graph.facebook.com/v18.0/{page_id}",
            params={
                "fields": "instagram_business_account{username,id}",
                "access_token": token,
            },
            timeout=30,
        )
        if r.status_code == 200:
            ig = r.json().get("instagram_business_account")
            if ig:
                print(f"[diag] Instagram Business: @{ig.get('username')} (id {ig.get('id')})")
            else:
                print("[diag] No Instagram Business account connected to this page.")
        else:
            print(f"[diag] Instagram lookup failed: {r.text}")
    except Exception as e:
        print(f"[diag] Instagram lookup error: {e}")


if __name__ == "__main__":
    main()

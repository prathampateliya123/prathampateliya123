#!/usr/bin/env python3
"""Download the GitHub avatar as a starter source-photo.jpg for the ASCII portrait.

Usage:
  python scripts/fetch_avatar.py
  python scripts/fetch_avatar.py [username] [out.jpg]

Replace source-photo.jpg with your own photo anytime, then:
  python scripts/prep_photo.py
  python scripts/make_ascii_svg.py
"""
import os
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "prathampateliya123"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-photo.jpg")

# hit the API for the current avatar_url (follows redirects to CDN)
api = f"https://api.github.com/users/{USER}"
req = urllib.request.Request(api, headers={"User-Agent": "profile-art-bot", "Accept": "application/vnd.github+json"})
with urllib.request.urlopen(req, timeout=20) as r:
    import json
    avatar = json.loads(r.read())["avatar_url"] + "&s=1024"

req2 = urllib.request.Request(avatar, headers={"User-Agent": "profile-art-bot"})
with urllib.request.urlopen(req2, timeout=30) as r:
    data = r.read()

with open(OUT, "wb") as f:
    f.write(data)
print(f"wrote {OUT} ({len(data)} bytes) from {avatar}")

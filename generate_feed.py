#!/usr/bin/env python3
"""
generate_feed.py — Run this before `git push` to update the RSS feed.

Usage:
    python generate_feed.py

It reads all .md files from the /posts/ directory, parses the YAML
front matter, and writes a fresh /blog/feed.xml.

Requirements: none (uses only Python stdlib)
"""

import os
import re
from datetime import datetime
from email.utils import format_datetime, localtime

SITE_URL    = "https://danalytica.com"
BLOG_URL    = SITE_URL + "/blog/"
FEED_URL    = SITE_URL + "/blog/feed.xml"
POSTS_DIR   = "posts"
FEED_OUT    = "blog/feed.xml"
SITE_TITLE  = "Danalytica Blog"
SITE_DESC   = "Practical writing on AI, ML, data engineering and building AI-native products."

def parse_front_matter(content):
    """Extract YAML-ish front matter between --- delimiters."""
    meta = {}
    body = content
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                key, _, val = line.partition(':')
                meta[key.strip()] = val.strip()
        body = content[m.end():]
    return meta, body

def md_to_plain(text):
    """Very rough Markdown → plain text for RSS descriptions."""
    text = re.sub(r'```[\s\S]*?```', '', text)   # code blocks
    text = re.sub(r'`[^`]+`', '', text)           # inline code
    text = re.sub(r'#{1,6}\s*', '', text)         # headers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text) # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)      # italic
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    text = re.sub(r'^\s*[-*|>]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def escape_xml(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def date_to_rfc822(date_str):
    """Convert YYYY-MM-DD to RFC 822 format for RSS."""
    try:
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        # RFC 822: Mon, 01 Jan 2025 00:00:00 +0000
        return d.strftime("%a, %d %b %Y 00:00:00 +0000")
    except Exception:
        return datetime.utcnow().strftime("%a, %d %b %Y 00:00:00 +0000")

def generate():
    posts = []
    if not os.path.isdir(POSTS_DIR):
        print("ERROR: posts/ directory not found. Run from repo root.")
        return

    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith(".md"):
            continue
        slug = fname[:-3]
        with open(os.path.join(POSTS_DIR, fname), encoding="utf-8") as f:
            content = f.read()
        meta, body = parse_front_matter(content)
        posts.append({
            "slug":     slug,
            "title":    meta.get("title", slug),
            "date":     meta.get("date", "2025-01-01"),
            "category": meta.get("category", ""),
            "excerpt":  meta.get("excerpt", md_to_plain(body)[:200]),
        })

    # Sort newest first
    posts.sort(key=lambda p: p["date"], reverse=True)

    items_xml = ""
    for p in posts:
        url = SITE_URL + "/blog/posts/" + p["slug"] + ".html"
        items_xml += """
    <item>
      <title>{title}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{date}</pubDate>
      <category>{category}</category>
      <description>{desc}</description>
    </item>""".format(
            title    = escape_xml(p["title"]),
            url      = url,
            date     = date_to_rfc822(p["date"]),
            category = escape_xml(p["category"]),
            desc     = escape_xml(p["excerpt"])
        )

    build_date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{title}</title>
    <link>{blog_url}</link>
    <description>{desc}</description>
    <language>en-gb</language>
    <atom:link href="{feed_url}" rel="self" type="application/rss+xml"/>
    <lastBuildDate>{build_date}</lastBuildDate>
{items}
  </channel>
</rss>""".format(
        title      = escape_xml(SITE_TITLE),
        blog_url   = BLOG_URL,
        desc       = escape_xml(SITE_DESC),
        feed_url   = FEED_URL,
        build_date = build_date,
        items      = items_xml
    )

    os.makedirs("blog", exist_ok=True)
    with open(FEED_OUT, "w", encoding="utf-8") as f:
        f.write(feed)

    print("Generated " + FEED_OUT + " with " + str(len(posts)) + " posts:")
    for p in posts:
        print("  - " + p["slug"] + " (" + p["date"] + ")")

if __name__ == "__main__":
    generate()

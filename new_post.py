#!/usr/bin/env python3
"""
new_post.py — Scaffold a new blog post.

Usage:
    python new_post.py "My Post Title"

Creates posts/my-post-title.md with front matter pre-filled.
Then:
  1. Write the post in Markdown
  2. Add the post entry to POSTS array in blog/index.html and blog/post.html
  3. Run: python generate_feed.py
  4. git add . && git commit -m "Add post: My Post Title" && git push
"""

import sys
import re
import os
from datetime import date

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def main():
    if len(sys.argv) < 2:
        print("Usage: python new_post.py \"My Post Title\"")
        sys.exit(1)

    title = " ".join(sys.argv[1:])
    slug  = slugify(title)
    today = date.today().isoformat()
    path  = os.path.join("posts", slug + ".md")

    if os.path.exists(path):
        print("ERROR: " + path + " already exists.")
        sys.exit(1)

    template = """---
title: {title}
date: {date}
category: AI Engineering
tags: [tag1, tag2]
excerpt: One sentence describing this post for the blog listing and RSS feed.
readTime: 5 min
author: Danalytica Team
---

Write your introduction here. This paragraph appears first and should hook the reader.

## First Section

Your content here.

## Second Section

More content.

## Conclusion

Wrap up and include a CTA.

---

*Have questions? Reach us at [hello@danalytica.com](mailto:hello@danalytica.com)*
""".format(title=title, date=today)

    os.makedirs("posts", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(template)

    print("Created: " + path)
    print("")
    print("Next steps:")
    print("  1. Edit " + path)
    print("  2. Add entry to POSTS array in blog/index.html and blog/post.html:")
    print("")
    print("     {")
    print('       slug: "' + slug + '",')
    print('       title: "' + title + '",')
    print('       date: "' + today + '",')
    print('       category: "AI Engineering",')
    print('       tags: ["tag1", "tag2"],')
    print('       excerpt: "Your excerpt here.",')
    print('       emoji: "✍️",')
    print('       featured: false,')
    print('       readTime: "5 min"')
    print("     },")
    print("")
    print("  3. python generate_feed.py")
    print("  4. git add . && git commit -m 'Add post: " + title + "' && git push")

if __name__ == "__main__":
    main()

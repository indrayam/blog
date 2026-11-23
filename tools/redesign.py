#!/usr/bin/env python3
"""One-time conversion of the blog to the shared indrayam.com page layout.

Run from the repository root:  python3 tools/redesign.py

What it changes (post text is never touched):
  * Every page: the old "Segmentation Fault" header and blog nav become the
    shared site nav plus a small blog sub-nav (By Year · By Category), and the
    favicon tags become the ones used across indrayam.com.
  * Posts: the <h2> title and "Posted : ..." line become a centered masthead
    with a Daily Diff-style date; the stale "Viewed: N times" counter is
    dropped; the category link points at the category archive; comments move
    into a <section class="comments">.
  * index.html becomes the year archive (lifted from archives/index.html,
    which is then removed and redirected to /).
  * archives/categories.html gets the masthead and an id per category.
  * aboutme.html and disclaimer.html drop their inline copy of the shared
    styles, which now live in style.css.

The script refuses to touch a page that does not match the expected legacy
template, so running it twice fails loudly instead of corrupting pages.
"""

import glob
import html
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

ICON_TAGS = (
    '<link rel="icon" href="/favicon.ico" sizes="any">\n'
    '    <link rel="apple-touch-icon" href="/apple-touch-icon.png">'
)

SITE_LINKS = [
    ("home", "https://indrayam.com/", "Home"),
    ("aboutme", "https://blog.indrayam.com/aboutme.html", "About Me"),
    ("resume", "https://resume.indrayam.com/", "Resume"),
    ("dailydiff", "https://dailydiff.indrayam.com/", "Daily Diff"),
    ("fieldnotes", "https://fieldnotes.indrayam.com/", "Field Notes"),
    ("sightings", "https://sightings.indrayam.com/", "Sightings"),
    ("writings", "https://blog.indrayam.com/", "Writings"),
]

SUB_LINKS = [
    ("year", "/", "By Year"),
    ("category", "/archives/categories.html", "By Category"),
]


def site_header(current, sub=None, show_sub=True):
    """Shared site nav; blog pages also get the sub-nav row under it."""
    items = []
    for key, href, label in SITE_LINKS:
        cur = ' aria-current="page"' if key == current else ""
        if key == "writings" and show_sub:
            # The blog sub-nav sits inside the Writings item, centered under it.
            items.append(f'      <li class="has-subnav"><a href="{href}"{cur}>{label}</a>')
            items.append('        <ul class="blog-subnav" aria-label="Blog archive">')
            for skey, shref, slabel in SUB_LINKS:
                scur = ' aria-current="page"' if skey == sub else ""
                items.append(f'          <li><a href="{shref}"{scur}>{slabel}</a></li>')
            items.append("        </ul>")
            items.append("      </li>")
        else:
            items.append(f'      <li><a href="{href}"{cur}>{label}</a></li>')
    out = [
        '<header class="site-header">',
        '  <nav class="site-nav" aria-label="Site navigation">',
        "    <ul>",
        *items,
        "    </ul>",
        "  </nav>",
        "</header>",
    ]
    return "\n".join(out)


OLD_HEADER_RE = re.compile(r'<header id="header">.*?</header>\n', re.S)
OLD_ICON_RE = re.compile(r'<link rel="Shortcut Icon" href="/images/favicon\.ico"\s*/?>')
INLINE_CHROME_RE = re.compile(
    r'\n    <style type="text/css">\n        /\* Home-style chrome.*?</style>', re.S
)


def sub_once(pattern, repl, text, where, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        sys.exit(f"{where}: expected exactly one match for {pattern!r}")
    return new


def fix_icons(text, where):
    new, n = OLD_ICON_RE.subn(ICON_TAGS, text)
    if n != 1:
        sys.exit(f"{where}: expected one old favicon link, found {n}")
    return new


def format_date(raw, where):
    """'November 11, 2008 at 12:23 am [America/Los_Angeles]' -> (iso, day, time)."""
    raw = raw.strip()
    m = re.fullmatch(r"(\w+ \d{1,2}, \d{4})(?: at (\d{1,2}:\d{2} [ap]m) \[America/Los_Angeles\])?", raw)
    if not m:
        sys.exit(f"{where}: unexpected dateline {raw!r}")
    day = datetime.strptime(m.group(1), "%B %d, %Y")
    day_text = f"{day:%A}, {day:%B} {day.day}, {day.year}"
    if not m.group(2):
        return day.strftime("%Y-%m-%d"), day_text, None
    t = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%B %d, %Y %I:%M %p").replace(tzinfo=PACIFIC)
    iso = t.isoformat(timespec="minutes")
    zone = "PST" if t.utcoffset().total_seconds() == -8 * 3600 else "PDT"
    time_text = f"{t.hour % 12 or 12}:{t:%M} {t:%p} {zone}"
    return iso, day_text, time_text


POST_HEAD_RE = re.compile(
    r'<div class="post" id="(post-\d+)">\s*'
    r'<h2><a href="[^"]*" rel="bookmark" title="Permanent link to (.*?)">\2</a></h2>\s*'
    r'<p class="post-dateline">Posted : ([^<]*)</p>\s*',
    re.S,
)

POST_TAIL_RE = re.compile(
    r'\s*<p class="postlinks">\s*Category: <b><a href="[^"]*" title="View all posts in [^"]*" '
    r'rel="category tag">(.*?)</a></b>\s*</p>'
    r'(?:\s*<div align="right">\s*<p></p>\s*<font size=-2 color="#000000">Viewed: <b>\d+</b> times</font>\s*</div>)?'
    r"\s*</div>",
    re.S,
)


PENDING = {}


def write(path, text):
    PENDING[path] = text


def convert_post(path):
    text = open(path, encoding="utf-8").read()
    slug = path.split("/")[1]
    text = fix_icons(text, path)
    text = sub_once(OLD_HEADER_RE, lambda m: site_header("writings") + "\n", text, path)

    def head(m):
        post_id, title, dateline = m.groups()
        iso, day_text, time_text = format_date(dateline, path)
        date = f'<time class="post-date-day" datetime="{iso}">{day_text}</time>'
        if time_text:
            date += f'<span class="post-date-time">{time_text}</span>'
        return (
            f'<article class="post" id="{post_id}">\n'
            f'<header class="page-masthead post-masthead">\n'
            f'    <h1 class="page-masthead-name">{title}</h1>\n'
            f'    <p class="post-date">{date}</p>\n'
            f"</header>\n"
        )

    text = sub_once(POST_HEAD_RE, head, text, path)

    def tail(m):
        category = m.group(1)
        return (
            f'\n<p class="postlinks">Filed under '
            f'<a href="/archives/categories.html#{slug}" rel="tag">{category}</a></p>\n'
            f"</article>"
        )

    text = sub_once(POST_TAIL_RE, tail, text, path)

    if '<div class="comment">' in text:
        text = sub_once(
            r'<div class="comment">(.*)</div>(\s*<p></p>\s*</main>)',
            r'<section class="comments" aria-labelledby="comments">\1</section>\2',
            text,
            path,
            re.S,
        )
    text = sub_once(r"\n<p></p>\n</main>", "\n</main>", text, path)
    write(path, text)


def page_head(title, description, canonical, og_title=None):
    og_title = og_title or title
    e = lambda s: html.escape(s, quote=True).replace("&#x27;", "&#x27;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title, quote=False)}</title>
    <meta name="description" content="{e(description)}">
        <link rel="canonical" href="{canonical}">
        <meta property="og:type" content="website">
        <meta property="og:title" content="{e(og_title)}">
        <meta property="og:description" content="{e(description)}">
        <meta property="og:url" content="{canonical}">
        <meta property="og:site_name" content="Anand Sharma&#x27;s Blog">
        <meta property="og:image" content="https://blog.indrayam.com/images/og-blog.png">
        <meta property="og:image:alt" content="{e(og_title)}">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{e(og_title)}">
        <meta name="twitter:description" content="{e(description)}">
        <meta name="twitter:image" content="https://blog.indrayam.com/images/og-blog.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300&amp;family=Lora:wght@400;700;900&amp;family=Newsreader:opsz,wght@6..72,400;6..72,700;6..72,900&amp;family=PT+Serif:wght@400;700&amp;family=Source+Sans+Pro:wght@400;700;900&amp;display=swap">
    <link rel="stylesheet" href="/style.css" media="screen">
    {ICON_TAGS}
    <link rel="alternate" type="application/rss+xml" title="RSS 2.0" href="http://feeds.feedburner.com/indrayam" />
</head>
"""


FOOTER = """<footer class="copyright">
    <a href="https://creativecommons.org/licenses/by-nd-nc/1.0/">Copyright</a> &copy; 2026 Anand Sharma. <a href="/disclaimer.html">Disclaimer</a>
</footer>
<script src="/js/archive.js"></script>
</body>
</html>
"""


def archive_body(path):
    """The legend and <details> groups from an existing archive page."""
    text = open(path, encoding="utf-8").read()
    m = re.search(r'(<p class="archive-legend">.*</details>)\s*</div>\s*<p></p>\s*</main>', text, re.S)
    if not m:
        sys.exit(f"{path}: archive list not found")
    return m.group(1)


def add_category_ids(body):
    def group(m):
        slug = re.search(r'href="/archives/([a-z0-9-]+)/', m.group(2)).group(1)
        return f'<details class="category-group" id="{slug}">{m.group(1)}{m.group(2)}'

    body, n = re.subn(r'<details class="category-group">(\s*<summary>)(.*?</summary>\s*<ul>\s*<li[^>]*><a href="[^"]*")', group, body, flags=re.S)
    if n < 20:
        sys.exit(f"categories.html: only {n} category groups found")
    return body


def build_home():
    body = archive_body("archives/index.html")
    page = page_head(
        "Writings - Anand Sharma's Blog",
        "Everything Anand Sharma has written on his blog, grouped by year: software, technology, life, and the world.",
        "https://blog.indrayam.com/",
    )
    page += f"""<body>
{site_header("writings", sub="year")}

<main>
<div class="post archives-page">
<header class="page-masthead">
    <h1 class="page-masthead-name">Writings</h1>
    <p class="page-masthead-tagline">Segmentation Fault: Core Dumped</p>
</header>
{body}
</div>
</main>
{FOOTER}"""
    write("index.html", page)


def build_categories():
    body = add_category_ids(archive_body("archives/categories.html"))
    page = page_head(
        "Categories - Anand Sharma's Blog",
        "Browse Anand Sharma's Blog by category, from software and networks to politics, humor, and personal notes.",
        "https://blog.indrayam.com/archives/categories.html",
    )
    page += f"""<body>
{site_header("writings", sub="category")}

<main>
<div class="post archives-page">
<header class="page-masthead">
    <h1 class="page-masthead-name">Categories</h1>
    <p class="page-masthead-tagline">Segmentation Fault: Core Dumped</p>
</header>
{body}
</div>
</main>
{FOOTER}"""
    write("archives/categories.html", page)


def convert_static(path):
    """aboutme.html and disclaimer.html: shared styles now come from style.css."""
    text = open(path, encoding="utf-8").read()
    text = fix_icons(text, path)
    text = sub_once(INLINE_CHROME_RE, "", text, path)
    write(path, text)


def convert_404():
    path = "404.html"
    text = open(path, encoding="utf-8").read()
    text = fix_icons(text, path)
    text = sub_once(OLD_HEADER_RE, lambda m: site_header(None) + "\n", text, path)
    text = sub_once(
        r"\n    <h2>404</h2>\n",
        '\n    <header class="page-masthead">\n        <h1 class="page-masthead-name">404</h1>\n    </header>\n',
        text,
        path,
    )
    text = sub_once(r"\n<p></p>\n</main>", "\n</main>", text, path)
    write(path, text)


def main():
    posts = sorted(glob.glob("archives/*/[0-9]*.html"))
    for path in posts:
        convert_post(path)
    build_home()
    build_categories()
    for path in ("aboutme.html", "disclaimer.html"):
        convert_static(path)
    convert_404()
    # Every page converted cleanly; only now touch the files.
    for path, text in PENDING.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    print(f"converted {len(posts)} posts, index.html, categories.html, aboutme.html, disclaimer.html, 404.html")


if __name__ == "__main__":
    main()

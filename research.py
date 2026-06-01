"""
Lightweight web research for the topic mode: search DuckDuckGo's HTML endpoint,
fetch a few result pages, and return their text as notes. Everything fails soft
and returns an empty list, so the caller can fall back to LLM-only knowledge.

No API keys and no heavy dependencies; just requests plus regex extraction.
"""

import re
from urllib.parse import unquote

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 StudyHero/1.0"}


def _search_urls(query, k):
    resp = requests.post("https://html.duckduckgo.com/html/",
                         data={"q": query}, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    raw = re.findall(r'class="result__a"[^>]*href="([^"]+)"', resp.text)
    urls = []
    for href in raw:
        m = re.search(r'uddg=([^&]+)', href)        # DDG wraps links in a redirect
        url = unquote(m.group(1)) if m else href
        if url.startswith("http") and url not in urls:
            urls.append(url)
        if len(urls) >= k:
            break
    return urls


def _fetch_text(url):
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    html = resp.text
    html = re.sub(r'(?is)<(script|style|nav|footer|header|aside).*?</\1>', ' ', html)
    text = re.sub(r'(?s)<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', text).strip()


def gather(topic, max_pages=3):
    """Return up to max_pages text excerpts about the topic, or [] on failure."""
    notes = []
    try:
        urls = _search_urls(topic, max_pages + 2)
    except Exception:
        return notes
    for url in urls:
        if len(notes) >= max_pages:
            break
        try:
            text = _fetch_text(url)
            if len(text) > 400:
                notes.append(text[:2000])
        except Exception:
            continue
    return notes

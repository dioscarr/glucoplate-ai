import urllib.request
from html.parser import HTMLParser
from typing import Optional


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'meta':
            attrd = dict(attrs)
            if 'property' in attrd and 'content' in attrd:
                self.meta[attrd['property'].lower()] = attrd['content']
            if 'name' in attrd and 'content' in attrd:
                self.meta[attrd['name'].lower()] = attrd['content']


def fetch_metadata(url: str, timeout: int = 6) -> dict:
    """Fetch basic meta tags (og:*, twitter:*) from a page. Returns empty dict on error."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GlucoPlateAI/0.1'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(64 * 1024).decode('utf-8', errors='ignore')
    except Exception:
        return {}
    p = _MetaParser()
    try:
        p.feed(data)
    except Exception:
        pass
    return p.meta


def discover_facebook(urls: list[str]) -> Optional[str]:
    """Return first facebook.com URL found in provided URLs or meta tags list."""
    for u in urls:
        if 'facebook.com' in (u or '').lower():
            return u
    return None

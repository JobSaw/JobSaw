"""Simple scraper utilities used by the orchestrator.

Functions:
- fetch(urls): fetch each URL and return a list of dicts with extracted text.
- save_manual_input(url, text): return a dict with pasted text for a URL (no file writes).

This module will use BeautifulSoup when available for more robust extraction.
If BeautifulSoup is not installed it falls back to a minimal html.parser-based
extractor. The network fetch uses urllib so there are no mandatory external
dependencies unless you opt to install BeautifulSoup and lxml for better results.
"""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Optional BeautifulSoup import; if available we'll use it for cleaner output.
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


class ScrapeError(Exception):
    """Raised when scraping a URL fails in a way the caller should handle."""
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._in_ignored = False
        self._ignored_tags = set(["script", "style", "noscript"])

    def handle_starttag(self, tag, attrs):
        if tag in self._ignored_tags:
            self._in_ignored = True

    def handle_endtag(self, tag):
        if tag in self._ignored_tags:
            self._in_ignored = False

    def handle_data(self, data):
        if not self._in_ignored:
            text = data.strip()
            if text:
                self._texts.append(text)

    def get_text(self):
        # join with line breaks; parser already splits on significant blocks
        return "\n".join(self._texts)


def fetch(urls):
    """Fetch each URL, extract visible text, and return a list of dicts.

    Returns list of objects {'url': url, 'text': extracted_text}.
    Raises ScrapeError on the first unrecoverable fetch/parse error.
    """
    pages = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobSaw/1.0)"}

    for url in urls:
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                raw = resp.read()
                try:
                    text = raw.decode('utf-8')
                except Exception:
                    # fallback to latin1
                    text = raw.decode('latin1')

            # Prefer BeautifulSoup extraction when available for better results
            if BeautifulSoup is not None:
                try:
                    # prefer lxml if installed, otherwise fall back to Python's parser
                    parser_name = "lxml" if "lxml" in BeautifulSoup().builder.modules else "html.parser"
                except Exception:
                    parser_name = "html.parser"

                try:
                    soup = BeautifulSoup(text, parser_name)
                    # remove common unwanted tags
                    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                        tag.decompose()
                    # prefer main/article content when available
                    main = soup.select_one("main, article, #main, .main, .content, .main-content")
                    if main:
                        body = main.get_text(separator="\n", strip=True)
                    else:
                        body = soup.get_text(separator="\n", strip=True)
                except Exception:
                    # on any BS parsing error, fall back to the simple parser below
                    parser = _VisibleTextParser()
                    parser.feed(text)
                    body = parser.get_text()
            else:
                # parse visible text with the fallback simple parser
                parser = _VisibleTextParser()
                parser.feed(text)
                body = parser.get_text()

            if not body.strip():
                raise ScrapeError(f"No visible text extracted from {url}")

            pages.append({'url': url, 'text': body})

        except (HTTPError, URLError, TimeoutError) as e:
            raise ScrapeError(f"Failed to fetch {url}: {e}")
        except ScrapeError:
            raise
        except Exception as e:
            raise ScrapeError(f"Unexpected error scraping {url}: {e}")

    return pages


def save_manual_input(url: str, text: str) -> dict:
    """Return a dict containing the pasted text for a URL (no file writes).

    Caller may choose to persist this dict if desired. Returns {'url': url, 'text': text}.
    """
    return {'url': url, 'text': text}

"""Extract question cards from a student's authorized Newton School pages.

The caller owns authentication. Pass any short-lived authorization headers to
fetch_newton_page; this module never stores portal passwords or session data.
"""
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import re

from source_sync import SourceAdapter

ALLOWED_HOSTS = {"my.newtonschool.co", "newtonschool.co", "www.newtonschool.co"}
CARD_WORDS = ("question", "problem", "exercise", "assignment", "quiz", "contest")
BLOCK_TAGS = {"p", "div", "li", "br", "pre", "blockquote"}


class _NoOffsiteRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old, new = urlsplit(req.full_url), urlsplit(newurl)
        if new.scheme != "https" or new.hostname not in ALLOWED_HOSTS:
            raise URLError("Blocked redirect outside the Newton School host allowlist.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_newton_page(url, headers=None, timeout=20):
    """Fetch one authorized Newton page; caller-supplied headers are transient."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Only HTTPS Newton School pages are supported.")
    request = Request(url, headers={"User-Agent": "SchedulePlanner/0.1", **(headers or {})})
    opener = build_opener(_NoOffsiteRedirect())
    with opener.open(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError("The selected Newton page is not HTML.")
        return response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")


class _QuestionCards(HTMLParser):
    def __init__(self, source_url, subject, chapter_hint, language_hint):
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self.subject = subject
        self.chapter = chapter_hint or "Unsorted chapter"
        self.language = language_hint
        self.card = None
        self.depth = 0
        self.heading = None
        self.heading_level = None
        self.heading_text = []
        self.records = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class", "") + " " + attrs.get("id", "")).casefold()
        if self.card is None and tag in {"article", "section", "div", "li"} and any(word in classes for word in CARD_WORDS):
            self.card = {
                "external_id": attrs.get("data-id") or attrs.get("id") or "",
                "title": attrs.get("data-title") or "",
                "language": attrs.get("data-language") or self.language,
                "text": [],
            }
            self.depth = 1
        elif self.card is not None and tag in {"article", "section", "div", "li"}:
            self.depth += 1
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading = tag
            self.heading_level = int(tag[1])
            self.heading_text = []
        if self.card is not None and tag in BLOCK_TAGS:
            self.card["text"].append("\n")

    def handle_endtag(self, tag):
        if self.heading == tag:
            heading = " ".join("".join(self.heading_text).split())
            if self.card is None and heading:
                if re.search(r"\b(chapter|unit|module|week)\b", heading, re.I):
                    self.chapter = heading
            elif self.card is not None and not self.card["title"] and heading:
                self.card["title"] = heading
            self.heading = None
            self.heading_text = []
        if self.card is not None and tag in {"article", "section", "div", "li"}:
            self.depth -= 1
            if self.depth <= 0:
                text = "\n".join(line.strip() for line in "".join(self.card["text"]).splitlines() if line.strip())
                title = self.card["title"].strip() or "Python problem"
                if text and self.card["language"].casefold() in {"python", "python 3", "py"}:
                    external_id = self.card["external_id"] or f"{self.source_url}#problem-{len(self.records) + 1}"
                    self.records.append({
                        "external_id": external_id,
                        "kind": "problem",
                        "title": title,
                        "subject": self.subject,
                        "chapter": self.chapter,
                        "language": "python",
                        "content": text,
                        "url": self.source_url,
                    })
                self.card = None
                self.depth = 0

    def handle_data(self, data):
        if self.heading is not None:
            self.heading_text.append(data)
        if self.card is not None:
            self.card["text"].append(data)


def extract_python_problem_cards(html, source_url, subject, chapter=None, language="python"):
    """Return chapter-tagged problem records from marked question elements."""
    parser = _QuestionCards(source_url, subject, chapter, language)
    parser.feed(html)
    parser.close()
    return parser.records


class NewtonProblemAdapter(SourceAdapter):
    """Scrape explicitly configured, student-authorized Newton course pages."""

    provider = "newton_school"

    def __init__(self, pages, headers_provider=None):
        self.pages = pages
        self.headers_provider = headers_provider or (lambda page: {})

    def fetch_items(self):
        results = []
        for page in self.pages:
            url = page["url"]
            html = fetch_newton_page(url, self.headers_provider(page))
            results.extend(extract_python_problem_cards(
                html, url, page.get("subject", "Python"),
                page.get("chapter"), page.get("language", "python"),
            ))
        return results

import calendar
import hashlib
import re
from datetime import UTC, datetime
from time import struct_time
from typing import Any

from bs4 import BeautifulSoup

_STRIP_HTML_ATTRIBUTES_RE = re.compile(
    r"\s+(?:class|style)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    flags=re.IGNORECASE,
)


def clean_html_attributes(content: Any) -> str | None:
    """
    Remove class/style attributes from HTML content, handling arbitrary attribute values.

    Args:
        content (Any): HTML content or attribute value to sanitize.

    Returns:
        str | None: Sanitized HTML content with class and style attributes removed.
    """

    if content is None:
        return None

    if isinstance(content, list):
        content = " ".join(str(value) for value in content)
    else:
        content = str(content)

    return _STRIP_HTML_ATTRIBUTES_RE.sub("", content)


def strip_html_attributes(content: str | None) -> str | None:
    """
    Remove class/style attributes from HTML content.

    Args:
        content (str | None): HTML content to sanitize.

    Returns:
        str | None: Sanitized HTML content with class and style attributes removed.
    """

    if content is None:
        return None

    return _STRIP_HTML_ATTRIBUTES_RE.sub("", content)


def sanitize_html(content: str | None) -> str | None:
    """
    Sanitize HTML content from feeds to defend against XSS.

    This removes dangerous tags and attributes, including script/style tags,
    event handlers, and URI-based attacks such as javascript: or data: URLs.
    """

    if content is None:
        return None

    soup = BeautifulSoup(content, "html.parser")

    dangerous_tags = [
        "script",
        "style",
        "iframe",
        "object",
        "embed",
        "link",
        "meta",
        "form",
        "input",
        "button",
    ]

    for tag in soup.find_all(dangerous_tags):
        tag.decompose()

    for tag in soup.find_all(True):
        attrs = dict(tag.attrs)
        for name, value in attrs.items():
            name_lower = name.lower()
            if name_lower.startswith("on") or name_lower == "style":
                del tag.attrs[name]
                continue

            if name_lower in (
                "href",
                "src",
                "srcset",
                "xlink:href",
                "formaction",
                "poster",
                "background",
            ):
                value_str = " ".join(value) if isinstance(value, list) else str(value)
                if re.match(r"^\s*(javascript|vbscript|data):", value_str, flags=re.I):
                    del tag.attrs[name]

    output = soup.body.decode_contents() if soup.body is not None else str(soup)
    return output


def extract_raw_content(entry: Any) -> str | None:
    """
    Extracts the raw content from a feed entry, preferring the 'content' field if available, and falling back to 'summary' if not.

    Args:
        entry (Any): The feed entry from which to extract content.

    Returns:
        str | None: The extracted content, or None if no content is available.
    """

    content_list = entry.get("content")
    if content_list:
        return content_list[0].get("value")

    return entry.get("summary")


def extract_image(entry: Any) -> str | None:
    """
    Extracts an image URL from a feed entry, checking for media content and enclosures.

    Args:
        entry (Any): The feed entry from which to extract an image URL.

    Returns:
        str | None: The extracted image URL, or None if no image is available.
    """

    if media := entry.get("media_content"):
        if media and (url := media[0].get("url")):
            return url

    if enclosures := entry.get("enclosures"):
        for enc in enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("url")

    return None


def parse_struct_time(t: struct_time | None) -> datetime | None:
    """
    Parses a struct_time object into a timezone-aware datetime object in UTC.

    Args:
        t (struct_time | None): The struct_time object to parse.

    Returns:
        datetime | None: The parsed datetime object in UTC, or None if the input was None.
    """

    if t is None:
        return None

    return datetime.fromtimestamp(calendar.timegm(t), tz=UTC)


def compute_content_hash(
    title: str | None,
    content: str | None,
    summary: str | None,
) -> str:
    """
    Computes a hash of the feed entry's content for change detection. Combines the title, content, and summary into a single string and returns a SHA-256 hash.

    Args:
        title (str | None): The title of the feed entry.
        content (str | None): The full content of the feed entry.
        summary (str | None): A short summary of the feed entry.

    Returns:
        str: A SHA-256 hash of the combined content, truncated to 64 characters.
    """

    payload = f"{title or ''}{content or ''}{summary or ''}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]

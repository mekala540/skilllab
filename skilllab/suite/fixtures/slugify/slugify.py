import re
import unicodedata


def slugify(text, max_length=50, separator="-"):
    """Turn `text` into a URL slug.

    - accents are removed ("café" -> "cafe")
    - the result is lowercase
    - every run of characters that are not a-z or 0-9 becomes one `separator`
    - there is no separator at the start or end
    - the result is at most `max_length` characters, cut so it does not end in a separator
    - max_length below 1 raises ValueError
    """
    if max_length < 1:
        raise ValueError("max_length must be >= 1")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", separator, text)
    text = text.strip(separator)
    if len(text) > max_length:
        text = text[:max_length].rstrip(separator)
    return text

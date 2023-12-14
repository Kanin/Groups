import re


def pagify(text: str, delims: list = None, shorten_by=8, page_length=1900):
    delims = delims or ["\n"]
    in_text = text
    page_length -= shorten_by
    while len(in_text) > page_length:
        closest_delim = max(in_text.rfind(d, 0, page_length) for d in delims)
        closest_delim = closest_delim if closest_delim != -1 else page_length
        yield in_text[:closest_delim]
        in_text = in_text[closest_delim:]
    yield in_text


def readable_list(before: list):
    return f"{', '.join(before[:-1])}, and {before[-1]}" if len(before) > 2 else " and ".join(before)


def normalize_text(text: str):
    normalized = re.sub(r"<a?:\w+:\d+>", "", text)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "", normalized)
    return normalized.lower()

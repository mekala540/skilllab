def paginate(items, page, per_page):
    """Return the items on 1-indexed `page`, with `per_page` items per page.

    A page past the end returns an empty list.
    """
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = page * per_page
    return items[start:start + per_page]


def page_count(items, per_page):
    """Number of pages needed to show every item (0 for no items)."""
    if per_page < 1:
        raise ValueError("per_page must be >= 1")
    return len(items) // per_page

"""
Search books and retrieve details through the Open Library API.

The public endpoints used here do not require an API key.
"""

import requests

BASE_URL = "https://openlibrary.org/search.json"
TIMEOUT_SECONDS = 30


class ApiError(Exception):
    """Raised when Open Library cannot be reached or returns an invalid response."""


def parse_book(item):
    """
    Keep only the fields we need from one search result.

    Parameters
    ----------
    item : dict
        One element of the API's docs list.

    Returns
    -------
    dict
        Book identifier, title, authors, first publication year,
        edition count and cover identifier.
    """
    return {
        "open_library_id": item.get("key"),
        "title": item.get("title", ""),
        "authors": item.get("author_name") or [],
        "first_publish_year": item.get("first_publish_year"),
        "edition_count": item.get("edition_count"),
        "cover_id": item.get("cover_i"),
    }


def search_books(query, max_results=10):
    """
    Search books by title or author on Open Library.

    Parameters
    ----------
    query : str
        Search text, such as a book title or author name.
    max_results : int, optional
        Maximum number of results. Defaults to 10.

    Returns
    -------
    list of dict
        Books in the format produced by parse_book.
        The list is empty if nothing matches.

    Raises
    ------
    ValueError
        If the query is empty or max_results is invalid.
    ApiError
        If the request fails or the response is invalid.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Enter a book title or author.")

    if (
        isinstance(max_results, bool)
        or not isinstance(max_results, int)
        or max_results < 1
    ):
        raise ValueError("max_results must be a positive integer.")

    params = {
        "q": query.strip(),
        "limit": max_results,
        "fields": (
            "key,title,author_name,first_publish_year,"
            "edition_count,cover_i"
        ),
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as error:
        raise ApiError(
            "Open Library did not answer in time. Please retry."
        ) from error
    except requests.exceptions.RequestException as error:
        raise ApiError("Could not reach Open Library.") from error

    try:
        data = response.json()
    except ValueError as error:
        raise ApiError("Open Library returned invalid JSON.") from error

    if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
        raise ApiError("Open Library returned an unexpected response.")

    return [parse_book(item) for item in data["docs"]]


def get_book_details(work_id):
    """
    Retrieve information about an Open Library work.

    Parameters
    ----------
    work_id : str
        Work identifier, such as "/works/OL66554W".

    Returns
    -------
    dict
        Book title, description and subjects.

    Raises
    ------
    ApiError
        If the request fails or the response is invalid.
    """
    url = f"https://openlibrary.org{work_id}.json"

    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.exceptions.Timeout as error:
        raise ApiError(
            "Open Library did not answer in time. Please retry."
        ) from error
    except requests.exceptions.RequestException as error:
        raise ApiError("Could not retrieve book details.") from error

    try:
        data = response.json()
    except ValueError as error:
        raise ApiError("Open Library returned invalid JSON.") from error

    if not isinstance(data, dict):
        raise ApiError("Open Library returned an unexpected response.")

    # Descriptions can be plain text or a dictionary.
    description = data.get("description") or ""
    if isinstance(description, dict):
        description = description.get("value", "")

    return {
        "title": data.get("title", ""),
        "description": description,
        "subjects": data.get("subjects") or [],
    }

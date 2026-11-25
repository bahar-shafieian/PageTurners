"""Functions for loading and preparing the project's datasets."""

import os
from urllib.error import URLError

import pandas as pd


def load_books(path):
    """
    Load book records from a CSV file.

    Parameters
    ----------
    path : str
        Path to the books CSV file.

    Returns
    -------
    pandas.DataFrame
        The loaded book records.

    Raises
    ------
    FileNotFoundError
        If the path does not point to an existing file.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Books CSV not found: {path}")

    return pd.read_csv(path)


def prepare_books(books):
    """
    Prepare publication years while preserving the input data.

    Parameters
    ----------
    books : pandas.DataFrame
        Book records containing original_publication_year.

    Returns
    -------
    pandas.DataFrame
        A copy with publication years stored as nullable integers.
    """
    books_clean = books.copy()

    books_clean["original_publication_year"] = (
        books_clean["original_publication_year"].astype("Int64")
    )

    return books_clean


def load_tag_data(tags_source, book_tags_source):
    """
    Load the tag dictionary and book-tag links from CSV sources.

    Parameters
    ----------
    tags_source : str or os.PathLike
        Local path or URL of tags.csv.
    book_tags_source : str or os.PathLike
        Local path or URL of book_tags.csv.

    Returns
    -------
    tuple of pandas.DataFrame
        The tag dictionary followed by the book-tag links.

    Raises
    ------
    FileNotFoundError
        If a local file cannot be found.
    ConnectionError
        If a URL cannot be reached or returns an HTTP error.
    OSError
        If another file-access or connection problem occurs.
    ValueError
        If a CSV cannot be parsed or lacks required columns.
    """
    sources = [
        (tags_source, ["tag_id", "tag_name"]),
        (book_tags_source, ["goodreads_book_id", "tag_id", "count"])
    ]

    tables = []

    for source, required_columns in sources:
        # Load each table and explain failures clearly.
        try:
            table = pd.read_csv(source, encoding="utf-8")

        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Tag CSV not found: {source}"
            ) from error

        except URLError as error:
            raise ConnectionError(
                f"Could not download tag CSV: {source}"
            ) from error

        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError
        ) as error:
            raise ValueError(
                f"Could not parse tag CSV: {source}"
            ) from error

        except OSError as error:
            raise OSError(
                f"Could not read tag CSV: {source}"
            ) from error

        # Check that the columns needed for our joins exist.
        missing_columns = sorted(
            set(required_columns) - set(table.columns)
        )

        if missing_columns:
            raise ValueError(
                f"Tag CSV {source} is missing required columns: "
                f"{', '.join(missing_columns)}"
            )

        tables.append(table)

    return tables[0], tables[1]

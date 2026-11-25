"""Functions for exploring book ratings."""

import numpy as np
import pandas as pd


def top_books(books, sort_by, n=10):
    """
    Return the first n books after sorting in descending order.

    Parameters
    ----------
    books : pandas.DataFrame
        The book records to explore.
    sort_by : str
        Name of the column used for sorting.
    n : int, optional
        Number of books to return. Defaults to 10.

    Returns
    -------
    pandas.DataFrame
        The selected books, retaining all columns.
    """
    return books.sort_values(
        by=sort_by,
        ascending=False
    ).head(n)


def popularity_correlation(books):
    """
    Calculate Spearman correlation between rating count and average score.

    Parameters
    ----------
    books : pandas.DataFrame
        Book records containing ratings_count and average_rating.

    Returns
    -------
    float
        Spearman correlation coefficient.
    """
    return books["ratings_count"].corr(
        books["average_rating"],
        method="spearman"
    )


def publication_period_analysis(books):
    """
    Group books by publication period and summarise their ratings.

    Parameters
    ----------
    books : pandas.DataFrame
        Records containing original_publication_year, book_id
        and average_rating. Books without a year are excluded.

    Returns
    -------
    tuple
        A copy of the dated book records with a period column,
        and a table of book counts, mean ratings and medians.
        Each book contributes equally to the rating summaries.
    """
    period_books = books.dropna(
        subset=["original_publication_year"]
    ).copy()

    period_books["period"] = pd.cut(
        period_books["original_publication_year"],
        bins=[-float("inf"), 1900, 1950, 2000, float("inf")],
        labels=[
            "Before 1900",
            "1900–1949",
            "1950–1999",
            "2000 onwards"
        ],
        right=False
    )

    summary = (
        period_books.groupby("period", observed=True)
        .agg(
            book_count=("book_id", "size"),
            mean_rating=("average_rating", "mean"),
            median_rating=("average_rating", "median")
        )
        .reset_index()
    )

    return period_books, summary


def author_rating_summary(books, min_books=5):
    """
    Summarise book ratings by the first listed author.

    Parameters
    ----------
    books : pandas.DataFrame
        Book records containing authors, book_id and average_rating.
    min_books : int, optional
        Minimum number of books per author. Defaults to 5.

    Returns
    -------
    pandas.DataFrame
        Authors meeting the threshold, with book counts, mean ratings
        and median ratings, sorted by mean rating in descending order.
        Anonymous works are excluded. Each book contributes equally.
    """
    author_books = books.copy()

    # Use the first listed name to group different contributor combinations.
    author_books["primary_author"] = (
        author_books["authors"]
        .str.split(",")
        .str[0]
        .str.strip()
    )

    # "Anonymous" represents unidentified authors, not one individual.
    author_books = author_books.loc[
        author_books["primary_author"] != "Anonymous"
    ]

    summary = (
        author_books.groupby("primary_author")
        .agg(
            book_count=("book_id", "size"),
            mean_rating=("average_rating", "mean"),
            median_rating=("average_rating", "median")
        )
        .reset_index()
    )

    # Keep authors represented by enough books for this comparison.
    summary = summary.loc[
        summary["book_count"] >= min_books
    ]

    return summary.sort_values(
        by=["mean_rating", "book_count"],
        ascending=[False, False]
    ).reset_index(drop=True)


def genre_rating_analysis(books, book_tags, tags, genre_map):
    """
    Assign selected genres to books and summarise their ratings.

    Parameters
    ----------
    books : pandas.DataFrame
        Records containing goodreads_book_id, book_id and average_rating.
    book_tags : pandas.DataFrame
        Book-tag links with goodreads_book_id, tag_id and count.
    tags : pandas.DataFrame
        Tag dictionary containing tag_id and tag_name.
    genre_map : dict
        Mapping from selected tag names to genre category names.

    Returns
    -------
    tuple
        Book-genre records and a summary containing book counts,
        mean ratings and median ratings for each category.
        Each book contributes once per category.
    """
    # Match selected tag names to our genre categories.
    selected_tags = tags.loc[
        tags["tag_name"].isin(genre_map)
    ].copy()

    selected_tags["genre"] = selected_tags["tag_name"].map(
        genre_map
    )

    # Attach genre names to book-tag links with positive counts.
    genre_links = book_tags.loc[book_tags["count"] > 0].merge(
        selected_tags[["tag_id", "genre"]],
        on="tag_id",
        how="inner",
        validate="many_to_one"
    )

    # Multiple synonymous tags must not count the same book twice.
    genre_links = genre_links[
        ["goodreads_book_id", "genre"]
    ].drop_duplicates()

    # Connect the genre assignments to the book ratings.
    genre_books = genre_links.merge(
        books[["goodreads_book_id", "book_id", "average_rating"]],
        on="goodreads_book_id",
        how="inner",
        validate="many_to_one"
    )

    summary = (
        genre_books.groupby("genre", as_index=False)
        .agg(
            book_count=("book_id", "nunique"),
            mean_rating=("average_rating", "mean"),
            median_rating=("average_rating", "median")
        )
        .sort_values("mean_rating", ascending=False)
        .reset_index(drop=True)
    )

    return genre_books, summary


def rating_disagreement(books):
    """
    Calculate the mean and standard deviation of each book's ratings.

    Parameters
    ----------
    books : pandas.DataFrame
        Records containing ratings_1 through ratings_5.
        Counts must be nonnegative with a positive total per book.

    Returns
    -------
    pandas.DataFrame
        A copy with rating_total, rating_mean and rating_std.
        Standard deviations describe the supplied rating distributions,
        using the total count as the denominator.
    """
    result = books.copy()

    rating_columns = [
        "ratings_1", "ratings_2", "ratings_3",
        "ratings_4", "ratings_5"
    ]

    # Each row contains the counts for the five possible star scores.
    counts = result[rating_columns].to_numpy(dtype=float)
    stars = np.arange(1, 6)
    totals = counts.sum(axis=1)

    if (counts < 0).any() or (totals <= 0).any():
        raise ValueError(
            "Rating counts must be nonnegative with positive totals."
        )

    # Weight each star score by how many readers assigned it.
    means = (counts * stars).sum(axis=1) / totals

    # Measure squared distances from each book's own mean.
    deviations = stars - means[:, np.newaxis]
    variances = (
        counts * deviations ** 2
    ).sum(axis=1) / totals

    result["rating_total"] = totals.astype(int)
    result["rating_mean"] = means
    result["rating_std"] = np.sqrt(variances)

    return result

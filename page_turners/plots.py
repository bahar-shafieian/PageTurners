"""Functions for visualising book ratings."""

import matplotlib.pyplot as plt


def plot_popularity_vs_rating(books):
    """
    Plot the number of ratings against the average rating.

    Parameters
    ----------
    books : pandas.DataFrame
        Book records containing ratings_count and average_rating.
        Rating counts must be positive for the logarithmic axis.

    Returns
    -------
    tuple
        The matplotlib Figure and Axes containing the scatter plot.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        books["ratings_count"],
        books["average_rating"],
        alpha=0.2,
        s=12
    )

    ax.set_xscale("log")
    ax.set_xlabel("Number of ratings (log scale)")
    ax.set_ylabel("Average rating")
    ax.set_title("Do more popular books receive higher ratings?")

    fig.tight_layout()

    return fig, ax


def plot_ratings_by_period(period_books):
    """
    Compare book-rating distributions across publication periods.

    Parameters
    ----------
    period_books : pandas.DataFrame
        Records containing period and average_rating, as returned
        by publication_period_analysis.

    Returns
    -------
    tuple
        The matplotlib Figure and Axes containing the box plot.
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    period_books.boxplot(
        column="average_rating",
        by="period",
        ax=ax,
        grid=False
    )

    fig.suptitle("")
    ax.set_title("Book ratings across publication periods")
    ax.set_xlabel("Publication period")
    ax.set_ylabel("Average book rating")

    fig.tight_layout()

    return fig, ax


def plot_top_authors(author_summary, n=10):
    """
    Plot authors with the highest mean book ratings.

    Parameters
    ----------
    author_summary : pandas.DataFrame
        Summary containing primary_author, book_count and mean_rating.
        Any minimum-book threshold must already have been applied.
    n : int, optional
        Maximum number of authors to display. Defaults to 10.

    Returns
    -------
    tuple
        The matplotlib Figure and Axes containing the bar chart.
    """
    # Select the highest means, then order bars for horizontal display.
    top_authors = (
        author_summary.nlargest(n, "mean_rating")
        .sort_values("mean_rating")
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.barh(
        top_authors["primary_author"],
        top_authors["mean_rating"],
        color="steelblue"
    )

    # Label each bar with the number of books behind the mean.
    for position, row in enumerate(
        top_authors.itertuples(index=False)
    ):
        ax.text(
            row.mean_rating + 0.03,
            position,
            f"n={row.book_count}",
            va="center",
            fontsize=9
        )

    # Start bars at zero so their lengths represent ratings faithfully.
    ax.set_xlim(0, 5)
    ax.set_xlabel("Mean book rating")
    ax.set_ylabel("First listed author")
    ax.set_title(
        f"Top {len(top_authors)} authors by mean book rating"
    )

    fig.tight_layout()

    return fig, ax


def plot_ratings_by_genre(genre_books):
    """
    Compare distributions of average book ratings across genres.

    Parameters
    ----------
    genre_books : pandas.DataFrame
        Records containing genre and average_rating.
        Each book must appear at most once per genre.

    Returns
    -------
    tuple
        The matplotlib Figure and Axes containing the box plot.
    """
    fig, ax = plt.subplots(figsize=(9, 6))

    # Draw one horizontal box for each genre's book ratings.
    genre_books.boxplot(
        column="average_rating",
        by="genre",
        vert=False,
        ax=ax,
        grid=False
    )

    # Replace the automatic pandas titles with descriptive labels.
    fig.suptitle("")
    ax.set_title("Distribution of book ratings across genres")
    ax.set_xlabel("Average book rating")
    ax.set_ylabel("Genre")
    ax.set_xlim(1, 5)

    fig.tight_layout()

    return fig, ax


def plot_star_distributions(selected_books):
    """
    Plot star-rating percentages for two selected books.

    Parameters
    ----------
    selected_books : pandas.DataFrame
        Exactly two book records containing book_id, rating_mean,
        rating_std and ratings_1 through ratings_5.

    Returns
    -------
    tuple
        The matplotlib Figure and array of Axes.
        Book IDs identify the records shown in the accompanying table.
    """
    if len(selected_books) != 2:
        raise ValueError("Select exactly two books.")

    rating_columns = [
        "ratings_1", "ratings_2", "ratings_3",
        "ratings_4", "ratings_5"
    ]

    fig, axes = plt.subplots(
        1, 2,
        figsize=(10, 4),
        sharey=True
    )

    for ax, (_, book) in zip(axes, selected_books.iterrows()):
        counts = book[rating_columns].to_numpy(dtype=float)

        # Normalise counts to compare books with different rating totals.
        percentages = counts / counts.sum() * 100

        ax.bar(range(1, 6), percentages, color="steelblue")
        ax.set_xticks(range(1, 6))
        ax.set_ylim(0, 100)
        ax.set_xlabel("Star rating")

        ax.set_title(
            f"Book ID {int(book['book_id'])}\n"
            f"Mean: {book['rating_mean']:.2f}, "
            f"SD: {book['rating_std']:.2f}"
        )

    axes[0].set_ylabel("Percentage of ratings")
    fig.tight_layout()

    return fig, axes

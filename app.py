"""Streamlit interface for the existing Page Turners analysis modules."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from page_turners import analysis, api, data, plots, scoring


PROJECT_DIR = Path(__file__).resolve().parent
BOOKS_PATH = PROJECT_DIR / "books.csv"
TAG_DATA_URL = "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master"
STAR_COLUMNS = [f"ratings_{star}" for star in range(1, 6)]
RANKING_COLUMNS = [
    "title", "authors", "rating_total", "rating_mean", "rating_std",
    "adjusted_score", "raw_rank", "adjusted_rank", "rank_change",
]
GENRE_MAP = {
    "fantasy": "Fantasy",
    "romance": "Romance",
    "science-fiction": "Science fiction",
    "sci-fi": "Science fiction",
    "mystery": "Mystery",
    "thriller": "Thriller",
    "horror": "Horror",
    "historical-fiction": "Historical fiction",
    "non-fiction": "Nonfiction",
    "nonfiction": "Nonfiction",
}


@st.cache_data(show_spinner=False)
def load_dataset(csv_path, modified_ns):
    """
    Load and prepare book statistics using the saved project functions.

    Parameters
    ----------
    csv_path : str
        Path to books.csv.
    modified_ns : int
        File modification time, included in the cache key to detect changes.

    Returns
    -------
    pandas.DataFrame
        Prepared records with rating means, counts and disagreement statistics.
    """
    books = data.load_books(csv_path)
    required = {
        "book_id", "title", "authors", "original_publication_year",
        "goodreads_book_id", "average_rating", "ratings_count",
        "work_ratings_count", *STAR_COLUMNS,
    }
    missing = sorted(required - set(books.columns))
    if missing:
        raise ValueError(f"Missing columns in books.csv: {', '.join(missing)}")
    if books.empty or books["book_id"].isna().any() or books["book_id"].duplicated().any():
        raise ValueError("Book records must be nonempty and have unique book IDs.")
    counts = books[STAR_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(counts).all() or (counts < 0).any() or (counts.sum(axis=1) <= 0).any():
        raise ValueError("Star counts must be finite, nonnegative and have positive totals.")
    return analysis.rating_disagreement(data.prepare_books(books))


@st.cache_data(show_spinner=False, max_entries=12)
def build_ranking(books, prior_count):
    """Return the saved scoring function's ranking, baseline and adjustment strength."""
    return scoring.adjusted_book_ranking(books, prior_count=prior_count)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=50)
def search_online(query):
    """Return up to ten Open Library search results for query; cache successful calls."""
    return api.search_books(query, max_results=10)


@st.cache_data(show_spinner=False, ttl=3600, max_entries=100)
def online_details(work_id):
    """Return a work's description and subjects using the saved API function."""
    return api.get_book_details(work_id)


@st.cache_data(show_spinner=False)
def load_genre_tables():
    """Load local tag CSVs when available, or the original dataset's online copies."""
    tag_path = PROJECT_DIR / "data" / "tags.csv"
    links_path = PROJECT_DIR / "data" / "book_tags.csv"
    tags_source = str(tag_path) if tag_path.is_file() else f"{TAG_DATA_URL}/tags.csv"
    links_source = str(links_path) if links_path.is_file() else f"{TAG_DATA_URL}/book_tags.csv"
    return data.load_tag_data(tags_source, links_source)


def display_table(table, filename, key):
    """Display table and offer exactly its displayed rows and columns as a UTF-8 CSV."""
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button(
        "Download this table as CSV",
        data=table.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        key=key,
        on_click="ignore",
    )


def display_plot(plot_function, *args, **kwargs):
    """Render a Figure returned by an existing plots function, then close it."""
    fig, _ = plot_function(*args, **kwargs)
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def search_dataset(books, query):
    """Return records whose title or authors contain the literal search text."""
    if not query.strip():
        return books
    query = query.strip()
    mask = (
        books["title"].str.contains(query, case=False, regex=False, na=False)
        | books["authors"].str.contains(query, case=False, regex=False, na=False)
    )
    return books.loc[mask]


def book_labels(books):
    """Map book IDs to title-and-author labels for selection widgets."""
    return {
        row.book_id: f"{row.title} — {row.authors}"
        for row in books.itertuples(index=False)
    }


def show_online_lookup(default_query, context):
    """Display an optional online search for this context, with safe per-session results."""
    with st.expander("Find descriptions and subjects on Open Library"):
        st.caption("Online records are separate from the ratings in the local dataset.")
        if st.session_state.get("online_context") != context:
            st.session_state["online_context"] = context
            st.session_state["online_results"] = []
            st.session_state["online_details"] = None

        with st.form(f"online_search_{context}"):
            query = st.text_input("Online title or author", value=default_query)
            submitted = st.form_submit_button("Search Open Library")

        if submitted:
            st.session_state["online_results"] = []
            st.session_state["online_details"] = None
            if not query.strip():
                st.info("Enter a title or author to search online.")
            else:
                try:
                    with st.spinner("Searching Open Library…"):
                        st.session_state["online_results"] = search_online(query.strip())
                    if not st.session_state["online_results"]:
                        st.info("No online books found.")
                except (api.ApiError, ValueError) as error:
                    st.warning(str(error))

        hits = st.session_state["online_results"]
        if not hits:
            return

        choice = st.selectbox(
            "Choose an online result",
            options=list(range(len(hits))),
            format_func=lambda index: (
                f"{hits[index]['title']} — {', '.join(hits[index]['authors'])} "
                f"({hits[index].get('first_publish_year') or 'year unknown'})"
            ),
            key=f"online_choice_{context}",
        )
        selected = hits[choice]
        work_id = selected.get("open_library_id")
        if st.button("Load book details", key=f"online_details_button_{context}"):
            st.session_state["online_details"] = None
            if not work_id:
                st.info("This result has no work identifier for a details lookup.")
            else:
                try:
                    with st.spinner("Loading book details…"):
                        details = online_details(work_id)
                    st.session_state["online_details"] = (work_id, details)
                except api.ApiError as error:
                    st.warning(str(error))

        saved = st.session_state["online_details"]
        if saved is not None and saved[0] == work_id:
            details = saved[1]
            cover, text = st.columns([1, 4])
            if selected.get("cover_id"):
                cover.image(
                    f"https://covers.openlibrary.org/b/id/{int(selected['cover_id'])}-M.jpg"
                )
            with text:
                st.subheader(details["title"])
                st.write(details["description"] or "No description available.")
                if details["subjects"]:
                    st.write("Subjects: " + ", ".join(details["subjects"][:10]))
                st.link_button("View on Open Library", f"https://openlibrary.org{work_id}")


def show_book_explorer(ranked):
    """Search local records and display a selected book's existing rating statistics."""
    st.header("Find a book")
    query = st.text_input(
        "Search by title or author", placeholder="For example: Pride and Prejudice",
        key="book_query",
    )
    matches = search_dataset(ranked, query)
    st.caption(f"{len(matches):,} matching books in the dataset")
    if matches.empty:
        st.info("No local match. Try another title or author, or search online below.")
        show_online_lookup(query, f"unmatched_{query}")
        return

    labels = book_labels(matches)
    book_id = st.selectbox(
        "Choose a book", options=matches["book_id"].tolist(),
        format_func=labels.get, key="book_selection",
    )
    selected = ranked.loc[ranked["book_id"].eq(book_id)].iloc[0]
    st.subheader(selected["title"])
    year = selected["original_publication_year"]
    year_text = "Year unknown" if pd.isna(year) else f"First published: {int(year)}"
    st.caption(f"{selected['authors']} · {year_text}")

    columns = st.columns(4)
    columns[0].metric("Mean star rating", f"{selected['rating_mean']:.3f} / 5")
    columns[1].metric("Star ratings", f"{int(selected['rating_total']):,}")
    columns[2].metric("Adjusted score", f"{selected['adjusted_score']:.3f} / 5")
    columns[3].metric(
        "Adjusted rank", f"{int(selected['adjusted_rank']):,}",
        delta=f"{int(selected['rank_change']):+,} places",
    )
    st.caption(
        f"Original rank: {int(selected['raw_rank']):,}. "
        f"Rating standard deviation: {selected['rating_std']:.3f}; "
        "a larger value means more disagreement among readers."
    )

    counts = selected[STAR_COLUMNS].to_numpy(dtype=float)
    distribution = pd.DataFrame({
        "Stars": [str(star) for star in range(1, 6)],
        "Ratings": counts.astype(int),
        "Percentage": counts / counts.sum() * 100,
    })
    st.subheader("How readers rated this book")
    st.bar_chart(distribution.set_index("Stars")["Percentage"], color="#2D6A73")
    st.caption("Bar heights are percentages of the book's supplied star ratings.")
    display_table(
        ranked.loc[ranked["book_id"].eq(book_id), ["book_id", *RANKING_COLUMNS]],
        "selected_book.csv", "selected_book_download",
    )
    with st.expander("Star counts and percentages"):
        display_table(distribution, "star_distribution.csv", "star_distribution_download")
    show_online_lookup(selected["title"], f"book_{book_id}")


def show_rankings(ranked):
    """Filter the existing global rankings and offer the displayed table as CSV."""
    st.header("Book rankings")
    query = st.text_input("Filter by title or author", key="ranking_query")
    minimum = st.number_input("Minimum star ratings", min_value=0, value=0, step=1000)
    order = st.selectbox(
        "Order by", ["Adjusted score", "Original mean rating", "Number of star ratings"],
        key="ranking_order",
    )
    limit = st.selectbox("Rows to display", [10, 25, 50, 100, 500], key="ranking_limit")
    filtered = search_dataset(ranked, query)
    filtered = filtered.loc[filtered["rating_total"] >= minimum]
    if filtered.empty:
        st.info("No books meet these filters.")
        return
    sort_column = {
        "Adjusted score": "adjusted_score", "Original mean rating": "rating_mean",
        "Number of star ratings": "rating_total",
    }[order]
    shown = filtered.sort_values(
        [sort_column, "book_id"], ascending=[False, True]
    ).head(limit)
    st.caption(
        f"Showing {len(shown):,} of {len(filtered):,} matching books. "
        "Ranks refer to the full dataset and are calculated before filtering."
    )
    display_table(shown[["book_id", *RANKING_COLUMNS]], "book_rankings.csv", "rankings_download")


def show_analysis(books):
    """Render the notebook's comparisons through the existing analysis and plot functions."""
    st.header("Explore the dataset")
    view = st.selectbox(
        "Choose an analysis",
        ["Popularity", "Publication periods", "Authors", "Genres", "Reader disagreement"],
        key="analysis_view",
    )
    if view == "Popularity":
        rho = analysis.popularity_correlation(books)
        st.metric("Spearman correlation", f"{rho:.4f}")
        st.caption("Association between ratings_count and average_rating; it does not establish causation.")
        display_plot(plots.plot_popularity_vs_rating, books)
        popular = analysis.top_books(books, "work_ratings_count", n=20)
        display_table(
            popular[["title", "authors", "work_ratings_count", "average_rating"]],
            "most_rated_books.csv", "popularity_download",
        )
    elif view == "Publication periods":
        period_books, summary = analysis.publication_period_analysis(books)
        st.caption("Each book contributes equally. Records with missing publication years are excluded.")
        if summary.empty:
            st.info("No publication years are available for this comparison.")
            return
        display_plot(plots.plot_ratings_by_period, period_books)
        display_table(summary, "publication_periods.csv", "period_download")
    elif view == "Authors":
        minimum = st.number_input("Minimum books per author", min_value=1, max_value=100, value=5)
        summary = analysis.author_rating_summary(books, min_books=minimum)
        st.caption("Grouped by the first listed contributor; Anonymous is excluded. Each book contributes equally.")
        if summary.empty:
            st.info("No authors meet this minimum-book threshold.")
            return
        display_plot(plots.plot_top_authors, summary, n=10)
        display_table(summary.head(20), "author_ratings.csv", "author_download")
    elif view == "Genres":
        st.caption("Selected reader-assigned genre tags overlap; each book contributes once per genre.")
        st.caption("Load tag data to enable this view. Local data/tags.csv and data/book_tags.csv are used when available.")
        if st.button("Load genre data", key="load_genres"):
            st.session_state["genres_enabled"] = True
        if not st.session_state.get("genres_enabled", False):
            return
        try:
            with st.spinner("Loading genre tags…"):
                tags, book_tags = load_genre_tables()
                genre_books, summary = analysis.genre_rating_analysis(books, book_tags, tags, GENRE_MAP)
        except (OSError, ValueError) as error:
            st.session_state["genres_enabled"] = False
            st.warning(f"Genre data could not be loaded: {error}")
            return
        if summary.empty:
            st.info("No selected genre tags match the book records.")
            return
        display_plot(plots.plot_ratings_by_genre, genre_books)
        display_table(summary, "genre_ratings.csv", "genre_download")
    else:
        st.caption("Compare the star-rating distributions of two books. Higher standard deviation means more spread.")
        if len(books) < 2:
            st.info("At least two books are needed for a comparison.")
            return
        ordered = books.sort_values("rating_std", ascending=False)
        labels = book_labels(ordered)
        first = st.selectbox("First book", ordered["book_id"].tolist(), format_func=labels.get, key="first_comparison")
        other_ids = ordered.loc[ordered["book_id"].ne(first), "book_id"].tolist()
        second = st.selectbox(
            "Second book", other_ids, index=len(other_ids) - 1,
            format_func=labels.get, key="second_comparison",
        )
        selected = books.set_index("book_id", drop=False).loc[[first, second]]
        display_plot(plots.plot_star_distributions, selected)
        display_table(
            selected[["book_id", "title", "rating_total", "rating_mean", "rating_std"]],
            "reader_disagreement.csv", "disagreement_download",
        )


def main():
    """Load the existing dataset and render the selected Streamlit page."""
    st.set_page_config(page_title="Page Turners", page_icon="📚", layout="wide")
    st.title("Page Turners")
    st.caption("Explore books, reader opinions and the effect of rating counts.")
    try:
        books = load_dataset(str(BOOKS_PATH), BOOKS_PATH.stat().st_mtime_ns)
    except (OSError, ValueError, TypeError) as error:
        st.error(f"Could not load books.csv: {error}")
        st.info("Keep app.py, books.csv and the page_turners package together in the project folder.")
        st.stop()

    with st.sidebar:
        st.header("Your bookshelf of data")
        st.caption(f"{len(books):,} books · goodbooks-10k")
        page = st.radio("Open a page", ["Find a book", "Rankings", "Analysis"], key="page")
        st.divider()
        factor = st.selectbox(
            "Adjustment strength", [0.1, 0.25, 0.5, 1.0, 2.0, 5.0], index=3,
            format_func=lambda value: f"{value:g} × median rating count",
            key="adjustment_factor",
            help="Larger values pull scores more strongly toward the dataset mean. The default is a chosen rule, not an optimised value.",
        )
        prior_count = float(books["rating_total"].median()) * factor
        st.caption(f"m = {prior_count:,.2f}")
        with st.expander("How adjusted scores work"):
            st.markdown("The score combines a book's mean rating with the mean across books. Books with more ratings receive less adjustment.")
            st.latex(r"S = \frac{vR + mC}{v + m}")
            st.caption("R: book mean · v: star-rating count · C: mean of book means · m: adjustment strength")
        st.caption("[Dataset](https://github.com/zygmuntz/goodbooks-10k) · [Open Library](https://openlibrary.org)")

    ranked, _, _ = build_ranking(books, prior_count)
    if page == "Find a book":
        show_book_explorer(ranked)
    elif page == "Rankings":
        show_rankings(ranked)
    else:
        show_analysis(books)


if __name__ == "__main__":
    main()

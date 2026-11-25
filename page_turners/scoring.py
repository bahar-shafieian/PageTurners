"""Scoring rules and book rankings for Page Turners."""


def adjusted_book_ranking(books, prior_count=None):
    """
    Compare mean-rating ranks with ranks adjusted for rating counts.

    Parameters
    ----------
    books : pandas.DataFrame
        Records containing book_id, rating_mean and rating_total,
        as returned by analysis.rating_disagreement.
    prior_count : float or None, optional
        Positive adjustment strength. If None, use the median
        rating_total.

    Returns
    -------
    tuple
        Adjusted ranking, baseline mean and adjustment strength.
        Positive rank_change indicates movement toward rank 1.
        Tied scores receive the same minimum rank.

    Raises
    ------
    ValueError
        If the adjustment strength is not positive.
    """
    result = books.copy()

    # Each book contributes equally to the baseline mean.
    baseline = result["rating_mean"].mean()

    if prior_count is None:
        prior_count = result["rating_total"].median()

    if prior_count <= 0:
        raise ValueError("Adjustment strength must be positive.")

    # Combine observed ratings with the baseline contribution.
    result["adjusted_score"] = (
        result["rating_total"] * result["rating_mean"]
        + prior_count * baseline
    ) / (result["rating_total"] + prior_count)

    # Rank 1 represents the highest score.
    result["raw_rank"] = (
        result["rating_mean"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    result["adjusted_rank"] = (
        result["adjusted_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    # Positive values indicate movement toward rank 1.
    result["rank_change"] = (
        result["raw_rank"] - result["adjusted_rank"]
    )

    result = result.sort_values(
        ["adjusted_score", "book_id"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return result, baseline, prior_count

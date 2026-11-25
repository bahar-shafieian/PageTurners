# Page Turners

> **Draft version:** the project is under development and this README will be updated.

Page Turners is a book-analysis project built for a Python course. It explores
book popularity, reader appreciation, and agreement using the goodbooks-10k
dataset. A Streamlit application lets users search books, explore their ratings,
and compare original and adjusted rankings.

## Objectives

- Compare ratings across genres, authors, and publication periods.
- Investigate the relationship between rating counts and average ratings.
- Measure reader disagreement using the distribution of star ratings.
- Explore how accounting for rating counts changes book rankings.

## Data

The main source is the [goodbooks-10k dataset](https://github.com/zygmuntz/goodbooks-10k).

| Data input | Contents | Use |
| --- | --- | --- |
| `books.csv` | 10,000 books with titles, authors, publication years, average ratings, rating counts, and counts of 1- to 5-star ratings | Main analysis and rankings |
| `tags.csv` and `book_tags.csv` | Tag names and links between books and tags | Comparisons across selected genres |
| [Open Library API](https://openlibrary.org/dev/docs/api/search) | Online search results and book details returned as JSON | Optional descriptions, subjects, and cover images |

`books.csv` is included in the repository. In the app, genre data is downloaded
when requested, unless `data/tags.csv` and `data/book_tags.csv` are available locally.
The notebook downloads the tag tables from the dataset repository.

Internet access is needed for online lookups and downloading genre data. The
Open Library endpoints used by this project do not require an API key.

## How it works

**User input**

- Book title or author to search the local dataset.
- A book to inspect or two books to compare for reader disagreement.
- Ranking controls: minimum number of star ratings, sorting criterion, and number of rows.
- Analysis selection: popularity, publication periods, authors, genres, or reader disagreement.
- Minimum books per author for the author comparison.
- Adjustment strength for the ranking, from 0.1 to 5 times the median star-rating count.
- An optional online search phrase to retrieve Open Library results and select a book for details.

**Processing**

- Load CSV data and prepare publication years while retaining missing values and ancient dates.
- Filter, sort, group, and join tables using pandas.
- Calculate summary statistics, Spearman correlation, and rating disagreement.
- Compute adjusted scores and compare them with the original mean-rating ranks.

The app checks required columns, book identifiers, and star counts. Data-loading
and API functions report problems such as missing files, failed requests, and
invalid responses.

**Output**

- Book statistics: mean star rating, number of star ratings, disagreement, adjusted score, and ranking changes.
- Tables of book rankings and comparisons across authors, genres, and publication periods.
- Charts showing popularity versus rating, rating comparisons, and star-rating distributions.
- Optional online descriptions, subjects, and available cover images, including for books outside the local dataset.
- CSV downloads of the displayed analysis and ranking tables.

Local ratings and rankings come from `books.csv`. Online search results remain
separate and do not receive local rating statistics automatically. Ranking filters
change the displayed books; rank numbers still refer to the full dataset.

## Scoring and reader disagreement

Reader disagreement is measured by the standard deviation of the star ratings,
calculated from `ratings_1` through `ratings_5`. A larger value means readers'
scores are more spread out.

The adjusted score combines a book's mean star rating with the dataset baseline:

```text
adjusted_score = (v * R + m * C) / (v + m)
```

- `R`: the book's mean, calculated from its star counts.
- `v`: the sum of its 1- to 5-star rating counts.
- `C`: the mean of these book means across the dataset.
- `m`: adjustment strength; the default is the median of `v`.

Books with fewer ratings receive a stronger adjustment toward the baseline.
This is a chosen scoring rule, rather than a definitive measure of book quality.
The supplied `average_rating` and `ratings_count` fields are used for the
popularity analysis; disagreement and adjusted rankings use the star-count fields.

## Project structure

| File or folder | Purpose |
| --- | --- |
| `page_turners/data.py` | CSV loading and data preparation |
| `page_turners/analysis.py` | Summaries, comparisons, correlation, and disagreement |
| `page_turners/scoring.py` | Adjusted scores and rankings |
| `page_turners/plots.py` | Reusable Matplotlib plots |
| `page_turners/api.py` | Open Library search and book details |
| `notebooks/analysis.ipynb` | Analysis, results, and interpretation |
| `app.py` | Streamlit interface |
| `books.csv` | Main dataset |
| `requirements.txt` | Required libraries and version ranges |

Both the notebook and the app import the reusable functions in `page_turners`.

## Getting started

Clone the repository and enter its folder:

```bash
git clone https://github.com/bahar-shafieian/PageTurners.git
cd PageTurners
```

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

The project uses pandas, NumPy, SciPy, Matplotlib, requests, and Streamlit.

**Run the app**

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal if the browser does not open
automatically. Keep the terminal running while using the app; press `Control+C`
to stop it.

**Run the notebook**

Install Jupyter Notebook separately if needed, then open the analysis:

```bash
python -m pip install notebook
python -m notebook notebooks/analysis.ipynb
```

Run the cells in order. Keep `books.csv` and the `page_turners` package in the
project root.

## Next steps

- [ ] Review the code and documentation.
- [ ] Write tests for data preparation and scoring.
- [ ] Refine the application design.

## Author

[Bahar](https://github.com/bahar-shafieian), project for the Python course.

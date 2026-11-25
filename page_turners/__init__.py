"""
Page Turners - tools for exploring book popularity and reader ratings.

The package uses the goodbooks-10k dataset to compare ratings across
authors, selected genres and publication periods, measure reader
disagreement, and investigate rankings adjusted for rating counts.

The package is organised into five modules:

- ``data``     : load CSV datasets and prepare book records
- ``analysis`` : calculate summaries, correlations and reader disagreement
- ``plots``    : create visualisations using Matplotlib
- ``api``      : search Open Library and retrieve book details
- ``scoring``  : calculate adjusted book scores and rankings
"""

__version__ = "0.1.0"

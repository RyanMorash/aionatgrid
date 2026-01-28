# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------

project = "aionatgrid"
copyright = "2026, Ryan Morash"
author = "Ryan Morash"
release = "0.3.1"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

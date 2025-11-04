# Configuration file for the Sphinx documentation builder.

# -- Project information

project = "dx-job-controller"
copyright = "2025, Interlegis / Senado Federal"
author = "Interlegis"

release = "1.0.0"
version = "1.0"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

language = "en"
locale_dirs = ["locale/"]
gettext_compact = False
figure_language_filename = "{path}{language}/{basename}{ext}"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"

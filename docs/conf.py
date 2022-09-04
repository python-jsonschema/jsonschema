from pathlib import Path
import importlib.metadata
import re

ROOT = Path(__file__).parent.parent
PACKAGE_SRC = ROOT / "jsonschema"

# -- Project information -----------------------------------------------------

project = "jsonschema"
author = "Julian Berman"
copyright = "2013, " + author

# version: The short X.Y version
# release: The full version, including alpha/beta/rc tags.
release = importlib.metadata.version("jsonschema")
version = release.partition("-")[0]


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = "1.0"

default_role = "any"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",

    "autoapi.extension",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_json_schema_spec",
    "sphinxcontrib.spelling",
    "sphinxext.opengraph",
]

cache_path = "_cache"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = [".rst", ".md"]
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ""
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = "%B %d, %Y"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "_cache", "_static", "_templates"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "lovelace"
pygments_dark_style = "one-dark"

doctest_global_setup = """
from jsonschema import *
"""

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "ujs": ("https://json-schema.org/understanding-json-schema/", None),
}


# -- Options for HTML output -----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "jsonschemadoc"


# -- Options for LaTeX output ------------------------------------------------

latex_documents = [
    ("index", "jsonschema.tex", "jsonschema Documentation", author, "manual"),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "jsonschema", "jsonschema Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "jsonschema",
        "jsonschema Documentation",
        author,
        "jsonschema",
        "One line description of project.",
        "Miscellaneous",
    ),
]

# -- Options for the linkcheck builder --------------------------------------


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("img.shields.io"),
    "https://github.com/python-jsonschema/jsonschema/actions",
    "https://github.com/python-jsonschema/jsonschema/workflows/CI/badge.svg",
]

# -- Options for sphinxcontrib-autosectionlabel ---------------------------

autosectionlabel_prefix_document = True

# -- Options for sphinxcontrib-spelling -----------------------------------

spelling_word_list_filename = "spelling-wordlist.txt"

# -- Options for autoapi ----------------------------------------------------

suppress_warnings = [
    "autoapi.python_import_resolution",
    "autoapi.toc_reference",
]
autoapi_root = "api"
autoapi_ignore = [
    "*/_[a-z]*.py",
    "*/__main__.py",
    "*/benchmarks/*",
    "*/cli.py",
    "*/tests/*",
]
autoapi_options = [
    "members",
    "undoc-members",
    "show-module-summary",
    "imported-members",
]

autoapi_type = "python"
autoapi_dirs = [PACKAGE_SRC]

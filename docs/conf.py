from pathlib import Path
import importlib.metadata
import re

ROOT = Path(__file__).parent.parent
PACKAGE_SRC = ROOT / "jsonschema"

project = "jsonschema"
author = "Julian Berman"
copyright = "2013, " + author

release = importlib.metadata.version("jsonschema")
version = release.partition("-")[0]

language = "en"
default_role = "any"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_json_schema_spec",
    "sphinxcontrib.spelling",
    "sphinxext.opengraph",
]

cache_path = "_cache"

pygments_style = "lovelace"
pygments_dark_style = "one-dark"

html_theme = "furo"

# See sphinx-doc/sphinx#10785
_TYPE_ALIASES = {
    "jsonschema._format._F",  # format checkers
}


def _resolve_type_aliases(app, env, node, contnode):
    if (
        node["refdomain"] == "py"
        and node["reftype"] == "class"
        and node["reftarget"] in _TYPE_ALIASES
    ):
        return app.env.get_domain("py").resolve_xref(
            env,
            node["refdoc"],
            app.builder,
            "data",
            node["reftarget"],
            node,
            contnode,
        )


def setup(app):
    app.connect("missing-reference", _resolve_type_aliases)


# = Builders =

doctest_global_setup = """
from jsonschema import *
import jsonschema.validators
"""


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("img.shields.io"),
    "https://github.com/python-jsonschema/jsonschema/actions",
    "https://github.com/python-jsonschema/jsonschema/workflows/CI/badge.svg",
]

# = Extensions =

# -- autoapi --

suppress_warnings = [
    "autoapi.python_import_resolution",
    "autoapi.toc_reference",
    "epub.duplicated_toc_entry",
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

# -- autosectionlabel --

autosectionlabel_prefix_document = True

# -- intersphinx --

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "ujs": ("https://json-schema.org/understanding-json-schema/", None),
}

# -- sphinxcontrib-spelling --

spelling_word_list_filename = "spelling-wordlist.txt"
spelling_show_suggestions = True

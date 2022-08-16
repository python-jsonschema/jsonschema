from contextlib import suppress
from datetime import datetime
from importlib import metadata
from pathlib import Path
from urllib.parse import urljoin
import urllib.request

from docutils import nodes
from lxml import html
import certifi

__version__ = "2.0.0"

BASE_URL = "https://json-schema.org/draft/2020-12/"
VOCABULARIES = {
    "core": urljoin(BASE_URL, "json-schema-core.html"),
    "validation": urljoin(BASE_URL, "json-schema-validation.html"),
}
HARDCODED = {
    "$ref": "https://json-schema.org/draft/2020-12/json-schema-core.html#ref",
    "$schema": "https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-schema-keyword",                # noqa: E501
    "format": "https://json-schema.org/draft/2020-12/json-schema-validation.html#name-implementation-requirements",  # noqa: E501
}


def setup(app):
    """
    Install the plugin.

    Arguments:

        app (sphinx.application.Sphinx):

            the Sphinx application context
    """

    app.add_config_value("cache_path", "_cache", "")

    CACHE = Path(app.config.cache_path)
    CACHE.mkdir(exist_ok=True)

    documents = {
        url: fetch_or_load(vocabulary_path=CACHE / f"{name}.html", url=url)
        for name, url in VOCABULARIES.items()
    }
    app.add_role("kw", docutils_does_not_allow_using_classes(documents))

    return dict(version=__version__, parallel_read_safe=True)


def fetch_or_load(vocabulary_path, url):
    """
    Fetch a new specification or use the cache if it's current.

    Arguments:

        vocabulary_path:

            the local path to a cached vocabulary document

        url:

            the URL of the vocabulary document
    """

    headers = {
        "User-Agent": "python-jsonschema v{} - documentation build v{}".format(
            metadata.version("jsonschema"),
            __version__,
        ),
    }

    with suppress(FileNotFoundError):
        modified = datetime.utcfromtimestamp(vocabulary_path.stat().st_mtime)
        date = modified.strftime("%a, %d %b %Y %I:%M:%S UTC")
        headers["If-Modified-Since"] = date

    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request, cafile=certifi.where())

    if response.code == 200:
        with vocabulary_path.open("w+b") as spec:
            spec.writelines(response)
            spec.seek(0)
            return html.parse(spec).getroot()

    return html.parse(vocabulary_path.read_bytes()).getroot()


def docutils_does_not_allow_using_classes(vocabularies):
    """
    Yeah.

    It doesn't allow using a class because it does annoying stuff like
    try to set attributes on the callable object rather than just
    keeping a dict.
    """

    def keyword(name, raw_text, text, lineno, inliner):
        """
        Link to the JSON Schema documentation for a keyword.

        Arguments:

            name (str):

                the name of the role in the document

            raw_source (str):

                the raw text (role with argument)

            text (str):

                the argument given to the role

            lineno (int):

                the line number

            inliner (docutils.parsers.rst.states.Inliner):

                the inliner

        Returns:

            tuple:

                a 2-tuple of nodes to insert into the document and an
                iterable of system messages, both possibly empty
        """

        hardcoded = HARDCODED.get(text)
        if hardcoded is not None:
            return [nodes.reference(raw_text, text, refuri=hardcoded)], []

        # find the header in the validation spec containing matching text
        for vocabulary_url, spec in vocabularies.items():
            header = spec.get_element_by_id(f"name-{text.lower()}", None)

            if header is not None:
                uri = urljoin(vocabulary_url, header.find("a").attrib["href"])
                break
        else:
            inliner.reporter.warning(
                "Didn't find a target for {0}".format(text),
            )
            uri = BASE_URL

        reference = nodes.reference(raw_text, text, refuri=uri)
        return [reference], []

    return keyword

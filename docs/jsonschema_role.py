from contextlib import suppress
from datetime import datetime
from importlib import metadata
from urllib.parse import urljoin
import os
import urllib.request

from docutils import nodes
from lxml import html
import certifi

__version__ = "1.2.0"

BASE_URL = "https://json-schema.org/draft-07/"
VALIDATION_SPEC = urljoin(BASE_URL, "json-schema-validation.html")
REF_URL = urljoin(BASE_URL, "json-schema-core.html#rfc.section.8.3")
SCHEMA_URL = urljoin(BASE_URL, "json-schema-core.html#rfc.section.7")


def setup(app):
    """
    Install the plugin.

    Arguments:

        app (sphinx.application.Sphinx):

            the Sphinx application context
    """

    app.add_config_value("cache_path", "_cache", "")

    os.makedirs(app.config.cache_path, exist_ok=True)

    path = os.path.join(app.config.cache_path, "spec.html")
    spec = fetch_or_load(path)
    app.add_role("validator", docutils_does_not_allow_using_classes(spec))

    return dict(version=__version__, parallel_read_safe=True)


def fetch_or_load(spec_path):
    """
    Fetch a new specification or use the cache if it's current.

    Arguments:

        cache_path:

            the path to a cached specification
    """

    headers = {
        "User-Agent": "python-jsonschema v{} - documentation build v{}".format(
            metadata.version("jsonschema"),
            __version__,
        ),
    }

    with suppress(FileNotFoundError):
        modified = datetime.utcfromtimestamp(os.path.getmtime(spec_path))
        date = modified.strftime("%a, %d %b %Y %I:%M:%S UTC")
        headers["If-Modified-Since"] = date

    request = urllib.request.Request(VALIDATION_SPEC, headers=headers)
    response = urllib.request.urlopen(request, cafile=certifi.where())

    if response.code == 200:
        with open(spec_path, "w+b") as spec:
            spec.writelines(response)
            spec.seek(0)
            return html.parse(spec)

    with open(spec_path) as spec:
        return html.parse(spec)


def docutils_does_not_allow_using_classes(spec):
    """
    Yeah.

    It doesn't allow using a class because it does annoying stuff like
    try to set attributes on the callable object rather than just
    keeping a dict.
    """

    def validator(name, raw_text, text, lineno, inliner):
        """
        Link to the JSON Schema documentation for a validator.

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

        if text == "$ref":
            return [nodes.reference(raw_text, text, refuri=REF_URL)], []
        elif text == "$schema":
            return [nodes.reference(raw_text, text, refuri=SCHEMA_URL)], []

        # find the header in the validation spec containing matching text
        header = spec.xpath("//h1[contains(text(), '{0}')]".format(text))

        if len(header) == 0:
            inliner.reporter.warning(
                "Didn't find a target for {0}".format(text),
            )
            uri = VALIDATION_SPEC
        else:
            if len(header) > 1:
                inliner.reporter.info(
                    "Found multiple targets for {0}".format(text),
                )

            # get the href from link in the header
            uri = urljoin(VALIDATION_SPEC, header[0].find("a").attrib["href"])

        reference = nodes.reference(raw_text, text, refuri=uri)
        return [reference], []

    return validator

from datetime import datetime
from docutils import nodes
import errno
import os

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib

import certifi
import jsonschema
from lxml import html


__version__ = "1.1.0"
VALIDATION_SPEC = "https://json-schema.org/draft-07/json-schema-validation.html"


def setup(app):
    """
    Install the plugin.

    Arguments:

        app (sphinx.application.Sphinx):

            the Sphinx application context
    """

    app.add_config_value("cache_path", "_cache", "")

    try:
        os.makedirs(app.config.cache_path)
    except OSError as error:
        if error.errno != errno.EEXIST:
            raise

    path = os.path.join(app.config.cache_path, "spec.html")
    spec = fetch_or_load(path)
    app.add_role("validator", docutils_sucks(spec))

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
            jsonschema.__version__, __version__,
        ),
    }

    try:
        modified = datetime.utcfromtimestamp(os.path.getmtime(spec_path))
        date = modified.strftime("%a, %d %b %Y %I:%M:%S UTC")
        headers["If-Modified-Since"] = date
    except OSError as error:
        if error.errno != errno.ENOENT:
            raise

    request = urllib.Request(VALIDATION_SPEC, headers=headers)
    response = urllib.urlopen(request, cafile=certifi.where())

    if response.code == 200:
        with open(spec_path, "w+b") as spec:
            spec.writelines(response)
            spec.seek(0)
            return html.parse(spec)

    with open(spec_path) as spec:
        return html.parse(spec)


def docutils_sucks(spec):
    """
    Yeah.

    It doesn't allow using a class because it does stupid stuff like try to set
    attributes on the callable object rather than just keeping a dict.
    """

    base_url = VALIDATION_SPEC
    ref_url = "https://json-schema.org/draft-07/json-schema-core.html#rfc.section.8.3"
    schema_url = "https://json-schema.org/draft-07/json-schema-core.html#rfc.section.7"

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
            return [nodes.reference(raw_text, text, refuri=ref_url)], []
        elif text == "$schema":
            return [nodes.reference(raw_text, text, refuri=schema_url)], []

        # find the header in the validation spec containing matching text
        header = spec.xpath("//h1[contains(text(), '{0}')]".format(text))

        if len(header) == 0:
            inliner.reporter.warning(
                "Didn't find a target for {0}".format(text),
            )
            uri = base_url
        else:
            if len(header) > 1:
                inliner.reporter.info(
                    "Found multiple targets for {0}".format(text),
                )

            # get the href from link in the header
            uri = base_url + header[0].find("a").attrib["href"]

        reference = nodes.reference(raw_text, text, refuri=uri)
        return [reference], []

    return validator

from datetime import datetime
from docutils import nodes
import errno
import os

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib

from lxml import html


VALIDATION_SPEC = "http://json-schema.org/latest/json-schema-validation.html"


def setup(app):
    """
    Install the plugin.

    :argument sphinx.application.Sphinx app: the Sphinx application context

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


def fetch_or_load(spec_path):
    """
    Fetch a new specification or use the cache if it's current.

    :argument cache_path: the path to a cached specification

    """

    headers = {}

    try:
        modified = datetime.utcfromtimestamp(os.path.getmtime(spec_path))
        date = modified.strftime("%a, %d %b %Y %I:%M:%S UTC")
        headers["If-Modified-Since"] = date
    except OSError as error:
        if error.errno != errno.ENOENT:
            raise

    request = urllib.Request(VALIDATION_SPEC, headers=headers)
    response = urllib.urlopen(request)

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
    ref_url = "http://json-schema.org/latest/json-schema-core.html#anchor25"
    schema_url = "http://json-schema.org/latest/json-schema-core.html#anchor22"

    def validator(name, raw_text, text, lineno, inliner):
        """
        Link to the JSON Schema documentation for a validator.

        :argument str name: the name of the role in the document
        :argument str raw_source: the raw text (role with argument)
        :argument str text: the argument given to the role
        :argument int lineno: the line number
        :argument docutils.parsers.rst.states.Inliner inliner: the inliner

        :returns: 2-tuple of nodes to insert into the document and an iterable
            of system messages, both possibly empty

        """

        if text == "$ref":
            return [nodes.reference(raw_text, text, refuri=ref_url)], []
        elif text == "$schema":
            return [nodes.reference(raw_text, text, refuri=schema_url)], []

        xpath = "//h3[re:match(text(), '(^|\W)\"?{0}\"?($|\W,)', 'i')]"
        header = spec.xpath(
            xpath.format(text),
            namespaces={"re": "http://exslt.org/regular-expressions"},
        )

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
            uri = base_url + "#" + header[0].getprevious().attrib["name"]

        reference = nodes.reference(raw_text, text, refuri=uri)
        return [reference], []

    return validator

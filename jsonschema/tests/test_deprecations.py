from unittest import TestCase

from jsonschema.validators import RefResolver


class TestDeprecations(TestCase):
    def test_version(self):
        """
        As of v4.0.0, __version__ is deprecated in favor of importlib.metadata.
        """

        with self.assertWarns(DeprecationWarning) as w:
            from jsonschema import __version__  # noqa

        self.assertTrue(
            str(w.warning).startswith(
                "Accessing jsonschema.__version__ is deprecated",
            ),
        )

    def test_validators_ErrorTree(self):
        """
        As of v4.0.0, importing ErrorTree from jsonschema.validators is
        deprecated in favor of doing so from jsonschema.exceptions.
        """

        with self.assertWarns(DeprecationWarning) as w:
            from jsonschema.validators import ErrorTree  # noqa

        self.assertTrue(
            str(w.warning).startswith(
                "Importing ErrorTree from jsonschema.validators is deprecated",
            ),
        )

    def test_RefResolver_in_scope(self):
        """
        As of v4.0.0, RefResolver.in_scope is deprecated.
        """

        resolver = RefResolver.from_schema({})
        with self.assertWarns(DeprecationWarning) as w:
            with resolver.in_scope("foo"):
                pass

        self.assertTrue(
            str(w.warning).startswith(
                "jsonschema.RefResolver.in_scope is deprecated ",
            ),
        )

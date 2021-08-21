from unittest import TestCase


class TestDeprecations(TestCase):
    def test_jsonschema_version(self):
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

    def test_jsonschema_validators_ErrorTree(self):
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

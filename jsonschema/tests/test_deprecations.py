from unittest import TestCase

import jsonschema


class TestDeprecations(TestCase):
    def test_jsonschema_version(self):
        """
        As of v4.0.0, __version__ is deprecated in favor of importlib.metadata.
        """

        with self.assertWarns(DeprecationWarning) as w:
            jsonschema.__version__

        self.assertTrue(
            str(w.warning).startswith(
                "Accessing jsonschema.__version__ is deprecated",
            ),
        )

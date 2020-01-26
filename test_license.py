#!/usr/bin/env python3

"""Test that this package's license file is properly detected by pip-licenses.

This file assumes that pip-licenses has already been run (in a tox env) and
generated license_report.json.
"""

import json
from pathlib import Path


def main():
    packages = json.loads(
        (Path(__file__).resolve().parent / 'license_report.json').read_text())
    for package in packages:
        if package['Name'] == 'jsonschema':
            assert package['LicenseFile'] != 'UNKNOWN'


if __name__ == '__main__':
    main()

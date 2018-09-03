from setuptools import setup


def local_scheme(*args, **kwargs):
    return ''

setup(use_scm_version={'local_scheme': local_scheme})

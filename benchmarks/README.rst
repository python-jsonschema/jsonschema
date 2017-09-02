Performance benchmarks
======================

These benchmark scripts make use of `Perf
<https://perf.readthedocs.io>`_ to benchmark ``jsonschema`` validation.

Basic usage
-----------

To benchmark the package ``perf`` is required (as is ``jsonschema`` itself):

.. code-block:: bash

    $ pip install perf jsonschema
    
To run the test-suite benchmarks,

.. code-block:: bash

    $ python test_suite.py -o perf.json

To compare against a reference run use,

.. code-block:: bash

    $ python -m perf compare_to --table reference.json perf.json

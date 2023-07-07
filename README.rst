=====
Dycco
=====

Dycco is a(nother) Python port of `Docco`_, the original quick-and-dirty,
hundred-line-long, literate-programming-style documentation generator. For an
example and more information on Dycco, see `its self-generated docs`_.

This version allows output to a markdown file or to an asciidoc3 file, as well
as adding a option to sanitize internal HTML (which is handy if your code
includes html fragments).  Dycco can generate documentation for Python files and nothing
else.

You can use `Pycco`_ (or a `new_version`_) instead, for other types of file,
that uses Dycco's code internally to handle Python files.


Installation
============

Use `pip`_ to install::

    pip install git+https://github.com/rojalator/dycco


Usage
=====

Command Line Usage
------------------

Just pass ``dycco`` a list of files and it will generate documentation for each
of them. By default, the generated documentation is put in a ``docs/``
subdirectory::

    $ dycco my_python_file.py

Dycco can generate docs for multiple files at once::

    $ dycco my_package/*.py

And you can control the output location::

    $ dycco --output-dir=/path/to/docs my_package/*.py

All command line options are given below::

    $ dycco --help

Outputs::


    usage: dycco [-h] [-o OUTPUT_DIR] [-a] [-e] [-f] source_file [source_file ...]

    Literate-style documentation generator.

    positional arguments:
      source_file           Source files to document

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Output directory (will be created if necessary)
      -a, --asciidoc3       Process with asciidoc3 instead of markdown (you will have to install asciidoc3, of course)
      -e, --escape-html     Run the documentation through html.escape() before markdown or asciidoc3
      -f, --single-file     Just produce a .md or .adoc file in single-column to be processed externally



Library Usage
-------------

Dycco can also be used as a plain old Python library::

    >>> import dycco
    >>> dycco.document('my_python_file.py', 'my_output_dir')


Credits
=======

Dycco is just a simple re-implementation of `Docco`_, with some inspiration and
template code from its primary Python port `Pycco`_ (`and an updated version`_)

.. _Docco: https://ashkenas.com/docco/
.. _Pycco: https://github.com/pycco-docs/pycco
.. _pip: http://www.pip-installer.org/
.. _its self-generated docs: https://github.com/rojalator/dycco/tree/master/docs/dycco.html
.. _new_version : https://github.com/rojalator/pycco
.. _and an updated version : https://github.com/rojalator/pycco

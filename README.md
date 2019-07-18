MyHDL 0.11 (fixbv development branch)
=====================================

[![Join the chat at https://gitter.im/myhdl/myhdl](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/myhdl/myhdl?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Documentation Status](https://readthedocs.org/projects/myhdl/badge/?version=stable)](http://docs.myhdl.org/en/stable/manual/)
[![Documentation Status](https://readthedocs.org/projects/myhdl/badge/?version=latest)](http://docs.myhdl.org/en/latest/manual)
[![Build Status](https://travis-ci.org/myhdl/myhdl.svg?branch=master)](https://travis-ci.org/myhdl/myhdl)

What is MyHDL?
--------------
MyHDL is a free, open-source package for using Python as a hardware
description and verification language.

To find out whether MyHDL can be useful to you, please read:

   - http://www.myhdl.org/start/why.html

License
-------
MyHDL is available under the LGPL license.  See ``LICENSE.txt``.

Website
-------
The main project website is located at http://www.myhdl.org
This development branch implements a fixbv and is hosted at: https://github.com/imec-myhdl/myhdl


Documentation
-------------
The manual is available on-line:

   - http://docs.myhdl.org/en/stable/manual

The documentation for this developent branch can be read online from: https://github.com/imec-myhdl/myhdl/blob/master/doc/MyHDL.pdf
alternatively you can build it yourself:

```
cd doc
make <target>

where <target> is any of:
  html       to make standalone HTML files
  livehtml   to make continuously updating standalone HTML files
  web        to make files usable by Sphinx.web
  htmlhelp   to make HTML files and a HTML help project
  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
  latexpdf   to make LaTeX files and run them through pdflatex
  text       to make text files
  man        to make manual pages
  texinfo    to make Texinfo files
  info       to make Texinfo files and run them through makeinfo
  gettext    to make PO message catalogs
  changes    to make an overview of all changed/added/deprecated items
  linkcheck  to check all external links for integrity
  doctest    to run all doctests embedded in the documentation (if enabled)
```

What's new
----------
To find out what's new in this release, please read:

   - http://docs.myhdl.org/en/stable/whatsnew/0.11.html

    - This development branch implements a fixbv class that is intended for fixed point arithmetic.
    Simulation is fully supported, conversion to Verilog is supported for a limited feature set.
    VHDL is not (yet) supported. Any help welcome.

    - Vcd files now support real (float) values when using floats or fixbv in as Signals. That allows 
    GTKWave to display the signals as 'analog' waves


Installation
------------
It is recommended to install MyHDL (and your project's other dependencies) in
a virtualenv.

Installing the latest stable release:

```
pip install myhdl
```

To install the development version from github:
```
pip install -e 'git+https://github.com/myhdl/myhdl#egg=myhdl
```

To install a local clone of the repository:
```
pip install -e path/to/dir
```

To install a specific commit hash, tag or branch from git:
```
pip install -e 'git+https://github.com/myhdl/myhdl@f696b8#egg=myhdl
```


You can test the proper installation as follows:

```
cd myhdl/test/core
py.test
```

To install co-simulation support:

Go to the directory ``cosimulation/<platform>`` for your target platform
and following the instructions in the ``README.txt`` file.

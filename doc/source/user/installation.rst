Installation
============

Installation via packages
*************************

TBD

Instalation from pip
********************

ooi can be installed via pip from OpenStack Kilo onwards. If you are running
Juno, the code will still work, but there are some dependencies that may be in
conflict with the existing Python modules in your system, as long as missing
dependencies (``oslo.log`` is not available in Juno)::

    $ pip install ooi

Installation
============

Installation via packages
*************************

ooi packages are released through the EGI's `AppDB`_. In the `ooi`_ middleware
page you will find the latest production and release candidates, as long as the
repositories for the major GNU/Linux distributions.

.. _AppDB: https://appdb.egi.eu/
.. _ooi: https://appdb.egi.eu/store/software/ooi

Instalation from pip
********************

ooi can be installed via pip from OpenStack Kilo onwards. If you are running
Juno, the code will still work, but there are some dependencies that may be in
conflict with the existing Python modules in your system, as long as missing
dependencies (``oslo.log`` is not available in Juno)::

    $ pip install ooi

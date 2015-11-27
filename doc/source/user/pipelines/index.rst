.. _pipeline-examples:

Pipeline examples
=================

For your convenience, find below some example pipelines to be used with the
corresponding OpenStack Compute version. These are to be **added** into your
``/etc/nova/api-paste.ini`` configuration file.

.. include:: juno.rst
.. include:: kilo.rst

.. # NOTE(aloga): We are including the pipelines, so we are not adding them to
   # any TOC and sphinx will complain.
.. toctree::
    :hidden:

    juno
    kilo
    liberty
    mitaka

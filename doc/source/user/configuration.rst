Configuration
=============

Once installed it is needed to add it to your OpenStack installation. Edit your
``/etc/nova/api-paste.ini``.

First it is needed to add a the OCCI filter like this::

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2

``openstack_version`` can be configured to any of the supported OpenStack API
versions, as indicated in Table :ref:`api-versions`. If it is not configured, by
default it will take the ``/v2.1`` value.

.. _api-versions:

.. table:: Supported OpenStack API versions

    ===================== ===================== =============================================
    OpenStack API version ``openstack_version`` corresponding OpenStack ``composite`` section
    ===================== ===================== =============================================
    v2                    ``/v2``               ``[composite:openstack_compute_api_v2]``
    v2.1                  ``/v2.1``             ``[composite:openstack_compute_api_v21]``
    ===================== ===================== =============================================

The next step is to create a ``composite`` section for the OCCI interface. It
is needed to duplicate the :ref:`corresponding OpenStack API ``composite``<api-versions>` section,
renaming it to ``occi_api_v11``. Once duplicated, the ``occi`` middleware needs
to be added just before the last component of the pipeline. So, in the example
above where ``/v2`` has been configured, we need to duplicate the
``[composite:openstack_compute_api_v2]`` as follows::

    [composite:occi_api_v11]
    use = call:nova.api.auth:pipeline_factory
    noauth = compute_req_id faultwrap sizelimit noauth ratelimit occi osapi_compute_app_v2
    keystone = compute_req_id faultwrap sizelimit occi authtoken keystonecontext ratelimit occi osapi_compute_app_v2
    keystone_nolimit = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v2

The last step is to add it to the ``[composite:osapi_compute]`` section::

    [composite:osapi_compute]
    # (...)
    /occi1.1: occi_api_11

You can find more detailed examples regarding the pipeline configuration in the
:ref:`pipeline-examples` section.

If everything is OK, after rebooting the ``nova-api`` service you should be able
to access your OCCI endpoint at::

    $ nova credentials
    # Grab the token
    $ export KID=<token>
    $ curl -H "x-auth-token: $KID" http://localhost:8774/occi1.1/-/


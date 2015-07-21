============
Installation
============

Note that ooi is still under development, so documentation is a bit naive. In
order to install and test ooi, perform the steps below.

Get the latest source code::

    $ git clone https://github.com/stackforge/ooi.git

Install it::

    $ cd ooi
    $ pip install .

Add it to your OpenStack installation. Edit your ``/etc/nova/api-paste.ini``.
In the ``[composite:osapi_compute]`` add the following::

    [composite:osapi_compute]
    # (...)
    /occi1.1: occi_11

Afterwards, add the OCCI filter like this::

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2

Substitute ``openstack_version`` with the API version that you are going to
use, taken from the ``[composite:osapi_compute]`` section.  So far we have
tested it with the ``v2`` version, so the correct value should be ``/v2``.

The last step is to duplicate the ``composite`` section corresponding to the
configured version, rename it to the configured value above (in this case
we have used ``occi_11`` above), and adding the ``occi`` filter just before the
``osapi_compute_app`` component of the pipeline. So, in this case where ``v2``
has been configured, the ``[composite:openstack_compute_api_v2]`` should be
duplicated as follows::

    [composite:occi_11]
    use = call:nova.api.auth:pipeline_factory
    noauth = compute_req_id faultwrap sizelimit noauth ratelimit occi osapi_compute_app_v2
    keystone = compute_req_id faultwrap sizelimit occi authtoken keystonecontext ratelimit occi osapi_compute_app_v2
    keystone_nolimit = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v2

If everything is OK, after rebooting the ``nova-api`` service you should be able
to access your OCCI endpoint at::

    $ nova credentials
    # Grab the token
    $ export KID=<token>
    $ curl -H "x-auth-token: $KID" http://localhost:8774/occi1.1/-/

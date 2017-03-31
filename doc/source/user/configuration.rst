Configuration
=============

ooi configuration
*****************

ooi needs to be enabled in the OpenStack Compute configuration file. Append
``ooi`` to your ``enabled_apis`` option::

    enabled_apis=ec2,osapi_compute,metadata,ooi

Moreover, the following options are available:

 * ``ooi_listen``: IP address where ooi will listen. Defaults to ``0.0.0.0``
 * ``ooi_listen_port``: Port ooi will bind to. Defaults to ``8787``.
 * ``ooi_workers``: Number of workers to spawn, by default it is set to the
   number of CPUs in the node.
 * ``neutron_ooi_endpoint``: Neutron endpoint, configures the network
   management by using neutron. If this is not set, the system will use
   nova-network.
 * ``ooi_secure_proxy_ssl_header``: when ooi is served behind a SSL termination
   proxy, this variable defines the HTTP header that contains the protocol
   scheme for the original request. Possible values:

   * None (default) - the request scheme is not influenced by any HTTP headers.
   * Valid HTTP header, like ``HTTP_X_FORWARDED_PROTO`` - ooi will return
     URLs of objects matching the URL scheme defined in the header.

Paste Configuration
*******************
.. _paste-configuration:

TL;DR.
------

Add the corresponding Paste configuration according to your OpenStack version
from :ref:`pipeline-examples` into your Paste configuration file
(usually ``/etc/nova/api-paste.ini``).

Detailed instructions
---------------------

Once installed it is needed to add it to your OpenStack installation. Edit your
``/etc/nova/api-paste.ini``.

First it is needed to add the OCCI filter like this::

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2

``openstack_version`` can be configured to any of the supported OpenStack API
versions, as indicated in Table :ref:`api-versions`. If it is not configured,
by default it will take the ``/v2.1`` value.

.. _api-versions:

.. table:: Supported OpenStack API versions

    ===================== ===================== =============================================
    OpenStack API version ``openstack_version`` reference OpenStack ``composite`` section
    ===================== ===================== =============================================
    v2                    ``/v2``               ``[composite:openstack_compute_api_v2]``
    v2.1                  ``/v2.1``             ``[composite:openstack_compute_api_v21]``
    ===================== ===================== =============================================

The next step is to create a ``composite`` section for the OCCI interface. It
is needed to duplicate the :ref:`corresponding OpenStack API ``composite``<api-versions>` section,
renaming it to ``occi_api_v12``. Once duplicated, the ``occi`` middleware needs
to be added just before the last component of the pipeline. So, in the example
above where ``/v2`` has been configured, we need to duplicate the
``[composite:openstack_compute_api_v2]`` as follows::

    [composite:occi_api_12]
    use = call:nova.api.auth:pipeline_factory
    noauth = compute_req_id faultwrap sizelimit noauth ratelimit occi osapi_compute_app_v2
    keystone = compute_req_id faultwrap sizelimit occi authtoken keystonecontext ratelimit occi osapi_compute_app_v2
    keystone_nolimit = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v2

The last step regarding the API configuration is to add it to create the
``[composite:ooi]`` section::

    [composite:ooi]
    use = call:nova.api.openstack.urlmap:urlmap_factory
    /occi1.1: occi_api_12
    /occi1.2: occi_api_12

Finally, you need to enable it in the OpenStack nova configuration, so that it
is loaded properly. Add ``ooi`` to the ``enabled_apis`` option in the
configuration file and adapt the port if needed, via the ``ooi_listen_port``
(by default it listens in the ``8787`` port). On the other hand, network management
by using neutron can be configure via the ``neutron_ooi_endpoint`` option
(if it is not set, the system will use nova-network)::

    enabled_apis=ec2,osapi_compute,metadata,ooi
    ooi_listen_port=8787
    neutron_ooi_endpoint=http://127.0.0.1:9696/v2.0

OpenStack has two components to support network management. On one side, nova-network
provides a simple network management which creates, lists, shows information for, and deletes networks.
Admin permissions are required to create and delete networks. On the other side, the neutron component
allows to manage and configure advanced network features. OOI implements the OCCI interface to simple
network management by using either nova-network or neutron.
``neutron_ooi_endpoint`` configures the neutron endpoint. It is an optional parameter that configures
the network management by using neutron. If this is not set, the system will use nova-network.

If everything is OK, after rebooting the ``nova-api`` service you should be able
to access your OCCI endpoint at::

    $ nova credentials
    # Grab the token
    $ export KID=<token>
    $ curl -H "x-auth-token: $KID" http://localhost:8787/occi1.1/-/


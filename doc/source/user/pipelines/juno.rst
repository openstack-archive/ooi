Juno (2014.2)
-------------

Using V2.1:

.. code:: ini

    [composite:ooi]
    use = call:nova.api.openstack.urlmap:urlmap_factory
    /occi1.1: occi_api_11

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2.0

    [composite:occi_api_11]
    [composite:openstack_compute_api_v2]
    use = call:nova.api.auth:pipeline_factory
    noauth = compute_req_id faultwrap sizelimit noauth ratelimit occi osapi_compute_app_v2
    keystone = compute_req_id faultwrap sizelimit authtoken keystonecontext ratelimit occi osapi_compute_app_v2
    keystone_nolimit = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v2

Using V2.0:

.. code:: ini

    [composite:ooi]
    use = call:nova.api.openstack.urlmap:urlmap_factory
    /occi1.1: occi_api_11

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2.1

    [composite:occi_api_11]
    use = call:nova.api.auth:pipeline_factory_v21
    noauth = compute_req_id faultwrap sizelimit noauth occi osapi_compute_app_v21
    keystone = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v21

Kilo (2015.1)
-------------

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
    noauth2 = compute_req_id faultwrap sizelimit noauth2 occi osapi_compute_app_v21
    keystone = compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v21

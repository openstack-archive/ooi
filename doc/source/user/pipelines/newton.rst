Netwon (14)
-----------

.. code:: ini

    [composite:ooi]
    use = call:nova.api.openstack.urlmap:urlmap_factory
    /occi1.2: occi_api_12
    /occi1.1: occi_api_12

    [filter:occi]
    paste.filter_factory = ooi.wsgi:OCCIMiddleware.factory
    openstack_version = /v2.1

    [composite:occi_api_12]
    use = call:nova.api.auth:pipeline_factory_v21
    noauth2 = cors http_proxy_to_wsgi compute_req_id faultwrap sizelimit noauth2 occi osapi_compute_app_v21
    keystone = cors http_proxy_to_wsgi compute_req_id faultwrap sizelimit authtoken keystonecontext occi osapi_compute_app_v21

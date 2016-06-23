Usage documentation
=======================

Discovery
*****************
In order to discover the available resources in the system, OOI provide a view of the relevant resources for its usage::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/-/

It will show the OCCI and OpenStack resources related to OOI.

Network
*****************

Network management provides list, show, create and delete networks to a specific tenant.

List networks
------
It lists all networks available for connecting virtual machines of a tenant::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/network


It returns a HTTP 200 with output::

    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/network/2c9868b4-f71a-45d2-ba8c-dbf42f0b3120
    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/network/4213c7ef-68d4-42e8-a3cd-1c5bab3abe6
    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/network/PUBLIC

Show network
------
It shows the network features::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/network/b8a3d813-65da-4910-a80c-f97b4ba31fd4


It returns a HTTP 200 with output::

    Category: network; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"; title="network resource";
     rel="http://schemas.ogf.org/occi/core#resource"; location="http://127.0.0.23:8787/occi1.1/network/"
    Category: ipnetwork; scheme="http://schemas.ogf.org/occi/infrastructure/network#"; class="mixin";
     title="IP Networking Mixin"
    Category: osnetwork; scheme="http://schemas.openstack.org/infrastructure/network#"; class="mixin";
     title="openstack network"
    X-OCCI-Attribute: occi.network.address="20.0.0.0/24"
    X-OCCI-Attribute: occi.network.state="active"
    X-OCCI-Attribute: occi.core.title="CommandLineOCCI"
    X-OCCI-Attribute: occi.network.gateway="20.0.0.1"
    X-OCCI-Attribute: occi.core.id="4a7dc666-33d2-495e-93fe-ccd224c98c11"
    Link: <http://127.0.0.23:8787/occi1.1/network/4a7dc666-33d2-495e-93fe-ccd224c98c11?action=up>;
     rel="http://schemas.ogf.org/occi/infrastructure/network/action#up"
    Link: <http://127.0.0.23:8787/occi1.1/network/4a7dc666-33d2-495e-93fe-ccd224c98c11?action=down>;
    rel="http://schemas.ogf.org/occi/infrastructure/network/action#down"

Create network
------
It shows the network features::

    curl -X POST http://127.0.0.23:8787/occi1.1/network/ -H 'X-Auth-Token: '$OS_TOKEN
    -H 'Category: network; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind",
    ipnetwork; scheme="http://schemas.ogf.org/occi/infrastructure/network#"; class="mixin"'
    -H 'Content-Type: text/occi'
    -H 'X-OCCI-Attribute: occi.core.title="OCCI_NET", occi.network.address="15.0.0.0/24"'

It returns a HTTP 201 with output::

    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/network/4a7dc666-33d2-495e-93fe-ccd224c98c11

Delete network
------
It deletes a network link::

    curl -X DELETE -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/network/cb94496e-7e8e-4cb6-841d-30f38bc375e6

It returns a 204 empty response.

Network Link
*****************
OOI allow to link virtual machines to private networks, and request for public floating IPs.

List network links
------
It lists links between VMs and networks::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/networklink

It returns a HTTP 200 with output::

    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/networklink/9524a622-5d1a-4c7c-bb83-e0d539e2c69b_PUBLIC_192.168.1.132
    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87

Show network link
------
It shows the network link features. It could be with a private or public network:
In case of private network::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87
It returns a HTTP 200 with output::

    curl  -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87
    Category: networkinterface; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind";
     title="network link resource"; rel="http://schemas.ogf.org/occi/core#link"; location="http://127.0.0.23:8787/occi1.1/networklink/"
    Category: ipnetworkinterface; scheme="http://schemas.ogf.org/occi/infrastructure/networkinterface#";
     class="mixin"; title="IP Network interface Mixin"
    X-OCCI-Attribute: occi.networkinterface.mac="fa:16:3e:20:14:f2"
    X-OCCI-Attribute: occi.networkinterface.interface="eth0"
    X-OCCI-Attribute: occi.networkinterface.state="active"
    X-OCCI-Attribute: occi.networkinterface.allocation="dynamic"
    X-OCCI-Attribute: occi.networkinterface.address="12.0.0.87"
    X-OCCI-Attribute: occi.core.source="http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624"
    X-OCCI-Attribute: occi.core.target="http://127.0.0.23:8787/occi1.1/network/cd48b7dd-9ac8-44fc-aec0-5ea679941ced"
    X-OCCI-Attribute: occi.core.id="703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87"

In case of public network::

    curl -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/networklink/4f11383c-b104-40d4-a17c-d223e450d15d_b8a3d813-65da-4910-a80c-f97b4ba31fd4_20.0.0.5
It returns a HTTP 200 with output::

    Category: networkinterface; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind";
     title="network link resource"; rel="http://schemas.ogf.org/occi/core#link";
      location="http://127.0.0.23:8787/occi1.1/networklink/"
    Category: ipnetworkinterface; scheme="http://schemas.ogf.org/occi/infrastructure/networkinterface#"; class="mixin"; title="IP Network interface Mixin"
    X-OCCI-Attribute: occi.networkinterface.mac="fa:16:3e:81:52:b9"
    X-OCCI-Attribute: occi.networkinterface.interface="eth0"
    X-OCCI-Attribute: occi.networkinterface.state="active"
    X-OCCI-Attribute: occi.networkinterface.allocation="dynamic"
    X-OCCI-Attribute: occi.networkinterface.address="20.0.0.5"
    X-OCCI-Attribute: occi.core.source="http://127.0.0.23:8787/occi1.1/compute/4f11383c-b104-40d4-a17c-d223e450d15d"
    X-OCCI-Attribute: occi.core.target="http://127.0.0.23:8787/occi1.1/network/b8a3d813-65da-4910-a80c-f97b4ba31fd4"
    X-OCCI-Attribute: occi.core.id="4f11383c-b104-40d4-a17c-d223e450d15d_b8a3d813-65da-4910-a80c-f97b4ba31fd4_20.0.0.5"

Create network link
------
It allows to create link between VMs and networks. It could be with a private or public network:
In case of private network::

    curl -X POST http://127.0.0.23:8787/occi1.1/networklink/ -H 'X-Auth-Token: '$OS_TOKEN
    -H 'Category: networkinterface; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"'
    -H 'Content-Type: text/occi'
    -H 'X-OCCI-Attribute: occi.core.target=http://127.0.0.23:8787/occi1.1/network/PUBLIC,
    occi.core.source=http://127.0.0.23:8787/occi1.1/compute/cb83a70a-5202-4b9e-a525-649c72005300'

In case of private network::

    curl -X POST http://127.0.0.23:8787/occi1.1/networklink/ -H 'X-Auth-Token: '$OS_TOKEN
    -H 'Category: networkinterface; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"'
    -H 'Content-Type: text/occi'
    -H 'X-OCCI-Attribute: occi.core.target=http://127.0.0.23:8787/occi1.1/network/d856c264-1999-489d-888e-f84db9093979,
    occi.core.source=http://127.0.0.23:8787/occi1.1/compute/cb83a70a-5202-4b9e-a525-649c72005300'


Delete network link
------
It deletes a network link::

    curl -X DELETE -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87
It returns a 204 empty response.

Compute
*****************

It allows to create, list, show and delete VMs.

List Computes
------
It allows to create VM::

    curl  -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/compute

It returns a HTTP 200 with output::

    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624
    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/compute/0ce5df96-7e61-4a8e-b821-9ebb88e77e07

Show Compute
------

It shows details of a VM::

    curl  -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624

It returns a HTTP 200 with output::

    Category: compute; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind"; title="compute resource"; rel="http://schemas.ogf.org/occi/core#resource"; location="http://127.0.0.23:8787/occi1.1/compute/"
    Category: 5f4311da-2ee2-47a6-913b-5d8496486c62; scheme="http://schemas.openstack.org/template/os#"; class="mixin"; title="cirros-0.3.4-x86_64-uec"; rel="http://schemas.ogf.org/occi/infrastructure#os_tpl"; location="http://127.0.0.23:8787/occi1.1/os_tpl/5f4311da-2ee2-47a6-913b-5d8496486c62"
    Category: 42; scheme="http://schemas.openstack.org/template/resource#"; class="mixin"; title="Flavor: m1.nano"; rel="http://schemas.ogf.org/occi/infrastructure#resource_tpl"; location="http://127.0.0.23:8787/occi1.1/resource_tpl/42"
    X-OCCI-Attribute: occi.core.title="vm_assig_2"
    X-OCCI-Attribute: occi.compute.state="inactive"
    X-OCCI-Attribute: occi.compute.memory=64
    X-OCCI-Attribute: occi.compute.cores=1
    X-OCCI-Attribute: occi.compute.hostname="vm_assig_2"
    X-OCCI-Attribute: occi.core.id="703910d7-97f7-4e3e-9243-30830591f624"
    Link: <http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624?action=start>; rel="http://schemas.ogf.org/occi/infrastructure/compute/action#start"
    Link: <http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624?action=stop>; rel="http://schemas.ogf.org/occi/infrastructure/compute/action#stop"
    Link: <http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624?action=restart>; rel="http://schemas.ogf.org/occi/infrastructure/compute/action#restart"
    Link: <http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624?action=suspend>; rel="http://schemas.ogf.org/occi/infrastructure/compute/action#suspend"
    Link: <http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87>;
    rel="http://schemas.ogf.org/occi/infrastructure#network";
    self="http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87";
    occi.networkinterface.mac="fa:16:3e:20:14:f2"; occi.networkinterface.interface="eth0"; occi.networkinterface.state="active";
    occi.networkinterface.allocation="dynamic"; occi.networkinterface.address="12.0.0.87";
    occi.core.source="http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624";
    occi.core.target="http://127.0.0.23:8787/occi1.1/network/cd48b7dd-9ac8-44fc-aec0-5ea679941ced";
    occi.core.id="703910d7-97f7-4e3e-9243-30830591f624_cd48b7dd-9ac8-44fc-aec0-5ea679941ced_12.0.0.87"
    Link: <http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_PUBLIC_11.0.0.44>;
    rel="http://schemas.ogf.org/occi/infrastructure#network"; self="http://127.0.0.23:8787/occi1.1/networklink/703910d7-97f7-4e3e-9243-30830591f624_PUBLIC_11.0.0.44";
    occi.networkinterface.mac="fa:16:3e:20:14:f2"; occi.networkinterface.interface="eth0"; occi.networkinterface.state="active"; occi.networkinterface.allocation="dynamic";
    occi.networkinterface.address="11.0.0.44"; occi.core.source="http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624";
    occi.core.target="http://127.0.0.23:8787/occi1.1/network/PUBLIC"; occi.core.id="703910d7-97f7-4e3e-9243-30830591f624_PUBLIC_11.0.0.44"

Create Compute
------

It creates a full VM using the default resources, including links to storage and private networks::

    curl -X POST http://127.0.0.23:8787/occi1.1/compute/ -H 'X-Auth-Token: '$OS_TOKEN
    -H 'Category: compute; scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind", 5f4311da-2ee2-47a6-913b-5d8496486c62;
    scheme="http://schemas.openstack.org/template/os#"; class="mixin", 2; scheme="http://schemas.openstack.org/template/resource#";
    class="mixin"' -H 'Content-Type: text/occi' -H 'X-OCCI-Attribute: occi.core.title="OOI_VM_1"'

Also we can specify the network to be linked::

    curl -X POST http://127.0.0.23:8787/occi1.1/compute/ -H 'X-Auth-Token: '$OS_TOKEN -H 'Category: compute;
    scheme="http://schemas.ogf.org/occi/infrastructure#"; class="kind", 5f4311da-2ee2-47a6-913b-5d8496486c62;
    scheme="http://schemas.openstack.org/template/os#"; class="mixin",
    2; scheme="http://schemas.openstack.org/template/resource#"; class="mixin"' -H
    'Link: </bar>; rel="http://schemas.ogf.org/occi/infrastructure#network";
    occi.core.target="http://127.0.0.23:8787/occi1.1/network/f8186fda-a389-468b-9c13-24b8eda65d77"'
    -H 'Content-Type: text/occi' -H 'X-OCCI-Attribute: occi.core.title="OOI_VM_1"'

It returns a HTTP 201 with output::

    X-OCCI-Location: http://127.0.0.23:8787/occi1.1/compute/4a7dc666-33d2-495e-93fe-ccd224c98c11

Delete Compute
------
It deletes a VMs, including all the links associated to it::

    curl -X DELETE -H "X-Auth-token: "$OS_TOKEN http://127.0.0.23:8787/occi1.1/compute/703910d7-97f7-4e3e-9243-30830591f624

It returns a 204 empty response.
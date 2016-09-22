# ooi: OpenStack OCCI Interface

ooi is an implementation the Open Grid Forum's
[Open Cloud Computing Interface (OCCI)](http://www.occi-wg.org)
for [OpenStack](http://www.openstack.org).

The documentation for OOI is available at
    http://ooi.readthedocs.org/en/latest

In the unfortunate event that bugs are discovered, they should
be reported to the bug tracker available at:

   http://bugs.launchpad.net/ooi

Developers wishing to work on the ooi project should always base their work on
the latest ooi code, available from the master GIT repository at:

   https://git.openstack.org/cgit/openstack/ooi

## ooi in INDIGO-DataCloud project

ooi is part of INDIGO-DataCloud's IaaS stack, exposing an OCCI interface for VM
management in OpenStack frameworks. As such, PaaS layer applications in the
INDIGO-DataCloud architecture model are able to interact with OpenStack
infrastructures using an open standard.

ooi was delivered as part of INDIGO-1 release, available for the two
distributions supported by the project: Ubuntu 14.04 and CentOS7, and aligned
with OpenStack Liberty release. Please follow the
[official deployment guidelines](https://indigo-dc.gitbooks.io/indigo-datacloud-releases/content/generic_installation_and_configuration_guide_1.html)
to enable the INDIGO-DataCloud's repositories and install them using:

    # CentOS7
    yum -y install python-ooi

    # Ubuntu14.04
    apt-get -y install python-ooi

depending on your distribution of choice.

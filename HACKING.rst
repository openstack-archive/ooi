ooi hacking guidelines
======================

Read the OpenStack Style Commandments http://docs.openstack.org/developer/hacking/

Code style is enforced and unit and functional testing
are required. To run all of them , just execute:

    $ tox

with no arguments.

If you wish to execute only functional (note that this is not integration so we
are only using test doubles here) testing, run:

    $ tox -e functional

Syntax checks can be run with:

    $ tox -e pep8

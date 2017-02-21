# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ooi API Server
"""

import sys

from nova import objects

from ooi import config
from ooi.log import log as logging
from ooi import service

LOG = logging.getLogger(__name__)

CONF = config.cfg.CONF


def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, 'ooi')
    objects.register_all()

    server = service.WSGIService('ooi', max_url_len=16384)
    service.serve(server, workers=server.workers)
    service.wait()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#


def make_body(resource, parameters):
        body = {resource: {}}
        for key in parameters.keys():
            body[resource][key] = parameters[key]

        return body


def get_query_string(parameters):
        query_string = ""
        if parameters is None:
            return None

        for key in parameters.keys():
            query_string = ("%s%s=%s&" %
                            (query_string, key, parameters[key]))

        # delete last character
        return query_string[:-1]


def translate_parameters(translation, parameters):
    if not parameters:
        return parameters
    out = {}
    for key in parameters.keys():
        if key in translation:
            out[translation[key]] = parameters[key]
    return out


def network_status(neutron_status):
    if neutron_status == "ACTIVE":
        return "active"
    elif neutron_status == "SUSPENDED":
        return "suspended"
    else:
        return "inactive"


def process_parameters(req):
    param = None
    parser = req.get_parser()(req.headers, req.body)
    if 'Category' in req.headers:
        param = parser.parse()
    else:
        attrs = parser.parse_attributes(req.headers)
        if attrs.__len__():
            param = {"attributes": attrs}
    if 'X_PROJECT_ID' in req.headers:
        project_id = req.headers["X_PROJECT_ID"]
        if param:
            param["attributes"]["X_PROJECT_ID"] = (
                project_id)
        else:
            param = {"attributes": {"X_PROJECT_ID": project_id}
                     }
    return param

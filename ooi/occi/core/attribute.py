# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
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

import abc
import collections
import copy

import six


@six.add_metaclass(abc.ABCMeta)
class Attribute(object):
    def __init__(self, name, value):
        self._name = name
        self._value = value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value


class MutableAttribute(Attribute):
    @Attribute.value.setter
    def value(self, value):
        self._value = value


class InmutableAttribute(Attribute):
    pass


class AttributeCollection(object):
    def __init__(self, attributes=None):
        if attributes is not None:
            if isinstance(attributes, collections.Mapping):
                if not all([isinstance(a, Attribute)
                            for a in attributes.values()]):
                    raise TypeError('mapping keys must be of class Attribute')
                self.attributes = dict(attributes)
            elif isinstance(attributes, collections.Sequence):
                self.attributes = dict.fromkeys(attributes)
            else:
                raise TypeError('attributes must be a sequence or mapping.')
        else:
            self.attributes = {}

    def __getitem__(self, key):
        ret = self.attributes[self.__keytransform__(key)]
        if ret is None:
            raise AttributeError("attribute %s is not set" % key)
        return ret

    def __setitem__(self, key, value):
        self.attributes[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.attributes[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def __keytransform__(self, key):
        return key

    def update(self, col):
        if not isinstance(col, AttributeCollection):
            raise TypeError('cannot update AttributeCollection with %s' %
                            type(col))
        return self.attributes.update(col.attributes)

    def copy(self):
        return copy.deepcopy(self)

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
import numbers

import enum
import six


@enum.unique
class AttributeType(enum.Enum):
    number_type = 1
    string_type = 2
    boolean_type = 3
    object_type = 4
    list_type = 5
    hash_type = 6

    def __init__(self, attr_type):
        self.attr_type = attr_type

    @classmethod
    def check_number_type(cls, value):
        if isinstance(value, bool) or not isinstance(value, numbers.Number):
            raise TypeError("Expecting numeric value")

    @classmethod
    def check_string_type(cls, value):
        if not isinstance(value, six.string_types):
            raise TypeError("Expecting string type")

    @classmethod
    def check_boolean_type(cls, value):
        if not isinstance(value, bool):
            raise TypeError("Expecting boolean value")

    @classmethod
    def check_object_type(cls, value):
        # object type can handle anything
        return

    @classmethod
    def check_list_type(cls, value):
        if not isinstance(value, list):
            raise TypeError("Expecting list type")

    @classmethod
    def check_hash_type(cls, value):
        if not isinstance(value, dict):
            raise TypeError("Expecting hash type")

    def check_type(self, value):
        py_types_map = {
            AttributeType.number_type.value: AttributeType.check_number_type,
            AttributeType.boolean_type.value: AttributeType.check_boolean_type,
            AttributeType.string_type.value: AttributeType.check_string_type,
            AttributeType.object_type.value: AttributeType.check_object_type,
            AttributeType.list_type.value: AttributeType.check_list_type,
            AttributeType.hash_type.value: AttributeType.check_hash_type,
        }
        # do not mess with uninitialized values
        if value is None:
            return
        py_types_map[self.attr_type](value)


@six.add_metaclass(abc.ABCMeta)
class Attribute(object):
    def __init__(self, name, value=None, required=False, default=None,
                 description=None, attr_type=None):
        self._name = name
        self.required = required
        self.default = default
        self.description = description
        if not attr_type:
            self.attr_type = AttributeType.object_type
        elif not isinstance(attr_type, AttributeType):
            raise TypeError("Unexpected attribute type")
        else:
            self.attr_type = attr_type
        self.attr_type.check_type(value)
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
        self.attr_type.check_type(value)
        self._value = value


class InmutableAttribute(Attribute):
    @classmethod
    def from_attr(cls, attr, value=None):
        return cls(attr.name, value=value, required=attr.required,
                   default=attr.default, description=attr.description,
                   attr_type=attr.attr_type)


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

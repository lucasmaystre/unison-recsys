#!/usr/bin/env python

import re

from storm.variables import Variable
from storm.properties import SimpleProperty


class PointVariable(Variable):
    PATTERN = re.compile("\((?P<x>.+?),(?P<y>.+?)\)")
    __slots__ = ()

    def parse_set(self, value, from_db):
        if from_db:
            if value is None:
                return None
            if not isinstance(value, (str, unicode)):
                raise TypeError("Expected point, found %s" % repr(value))
            try:
                coords = self.PATTERN.match(value).groupdict()
                return (float(coords['x']), float(coords['y']))
            except:
                raise TypeError("Expected point, found %s" % repr(value))
        else:
            if not isinstance(value, tuple) or len(value) != 2:
                raise TypeError("Expected point, found %s" % repr(value))
            for coordinate in value:
                if type(coordinate) not in (int, long, float):
                    raise TypeError("Expected point, found %s" % repr(value))
            return value

    def parse_get(self, value, to_db):
        if to_db:
            return unicode(value)
        return value


class Point(SimpleProperty):
    variable_class = PointVariable

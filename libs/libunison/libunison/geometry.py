#!/usr/bin/env python
"""Geometrical stuff."""

import collections

from math import atan2, cos, pi, sin, sqrt

# Mean earth radius in meters, according to
# http://en.wikipedia.org/wiki/Earth_radius#Mean_radius
EARTH_RADIUS = 6371009


# Simple data structure to represent a point.
Point = collections.namedtuple('Point', 'lat lon')


def distance(a, b, radius=EARTH_RADIUS):
    """Compute the great-circle distance between two points.

    The two points are to be given in degrees, i.e. the standartd latitude /
    longitude notation. By default, we assume the radius of the sphere is the
    earth's average radius. The distance is returned in meters.
    """
    # Implementation note: this is the haversine formula.
    delta_lat = deg_to_rad(b.lat - a.lat)
    delta_lon = deg_to_rad(b.lon - a.lon)
    a_lat = deg_to_rad(a.lat)
    b_lat = deg_to_rad(b.lat)
    x = (sin(delta_lat / 2.0)**2
            + sin(delta_lon / 2.0)**2 * cos(a_lat) * cos(b_lat))
    return radius * (2 * atan2(sqrt(x), sqrt(1 - x)))


def deg_to_rad(angle):
    """Convert an angle from degree to radians."""
    return (2 * pi / 360) * angle

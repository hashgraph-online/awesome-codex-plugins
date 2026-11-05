#!/usr/bin/env python3
"""Where the sun is, for a light reference or a light prompt. NOAA solar calculator equations, standard library only.

  sun.py --lat 38.72 --lon -9.14 --date 2026-11-03 [--time 07:30]

Date and time are UTC. Prints JSON: sunrise, sunset and civil dawn and dusk for the local solar day, with the azimuth at
sunrise and sunset. With --time, also altitude, azimuth and shadow length as a multiple of object height.

Degrees. Azimuth runs clockwise from north. Altitude is geometric, with no refraction. Sunrise and sunset use the
standard -0.833 degrees. A null means the sun does not cross that height that day.
"""
import argparse
import datetime
import json
import math

RISE, CIVIL = -0.833, -6.0


def position(moment, lat, lon):
    """(altitude, azimuth) of the sun at a UTC datetime."""
    sin, cos, tan, rad = math.sin, math.cos, math.tan, math.radians
    t = (moment.timestamp() / 86400 + 2440587.5 - 2451545) / 36525  # Julian centuries since J2000
    mean_long = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    anomaly = rad(357.52911 + t * (35999.05029 - 0.0001537 * t))
    eccentricity = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    centre = (sin(anomaly) * (1.914602 - t * (0.004817 + 0.000014 * t))
              + sin(2 * anomaly) * (0.019993 - 0.000101 * t) + sin(3 * anomaly) * 0.000289)
    node = rad(125.04 - 1934.136 * t)
    apparent_long = rad(mean_long + centre - 0.00569 - 0.00478 * sin(node))
    seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
    obliquity = rad(23 + (26 + seconds / 60) / 60 + 0.00256 * cos(node))
    declination = math.asin(sin(obliquity) * sin(apparent_long))
    y, long2 = tan(obliquity / 2) ** 2, rad(mean_long) * 2
    equation_of_time = 4 * math.degrees(
        y * sin(long2) - 2 * eccentricity * sin(anomaly) + 4 * eccentricity * y * sin(anomaly) * cos(long2)
        - 0.5 * y * y * sin(2 * long2) - 1.25 * eccentricity * eccentricity * sin(2 * anomaly))
    minutes = moment.hour * 60 + moment.minute + moment.second / 60
    hour_angle = rad(((minutes + equation_of_time + 4 * lon) % 1440) / 4 - 180)
    phi = rad(lat)
    altitude = math.asin(sin(phi) * sin(declination) + cos(phi) * cos(declination) * cos(hour_angle))
    azimuth = math.atan2(-cos(declination) * sin(hour_angle),
                         sin(declination) * cos(phi) - cos(declination) * sin(phi) * cos(hour_angle))
    return math.degrees(altitude), math.degrees(azimuth) % 360


def crossing(start, end, height, lat, lon):
    """The moment the sun crosses this height between two datetimes, by bisection, or None."""
    above = position(start, lat, lon)[0] >= height
    if (position(end, lat, lon)[0] >= height) == above:
        return None
    while end - start > datetime.timedelta(seconds=1):
        middle = start + (end - start) / 2
        if (position(middle, lat, lon)[0] >= height) == above:
            start = middle
        else:
            end = middle
    return start


def clock(moment, date):
    """HH:MM rounded to the minute, with the date if it falls on another UTC day."""
    if moment is None:
        return None
    moment = (moment + datetime.timedelta(seconds=30)).replace(second=0, microsecond=0)
    return moment.strftime("%H:%M") if moment.date() == date else moment.strftime("%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--date", required=True, type=datetime.date.fromisoformat, help="YYYY-MM-DD, UTC")
    ap.add_argument("--time", type=datetime.time.fromisoformat, help="HH:MM, UTC")
    a = ap.parse_args()
    if not -90 <= a.lat <= 90 or not -180 <= a.lon <= 180:
        ap.error("--lat runs from -90 to 90 and --lon from -180 to 180")

    utc = datetime.timezone.utc
    midnight = datetime.datetime.combine(a.date, datetime.time(), utc)
    noon = midnight + datetime.timedelta(hours=12 - a.lon / 15)  # within minutes of solar noon: enough to split the day
    half_day = datetime.timedelta(hours=12)

    def event(height, morning):
        return (crossing(noon - half_day, noon, height, a.lat, a.lon) if morning
                else crossing(noon, noon + half_day, height, a.lat, a.lon))

    def azimuth(moment):
        return round(position(moment, a.lat, a.lon)[1], 1) if moment else None

    sunrise, sunset = event(RISE, True), event(RISE, False)
    result = {"lat": a.lat, "lon": a.lon, "date": a.date.isoformat(),
              "civil_dawn_utc": clock(event(CIVIL, True), a.date),
              "sunrise_utc": clock(sunrise, a.date), "sunrise_azimuth": azimuth(sunrise),
              "sunset_utc": clock(sunset, a.date), "sunset_azimuth": azimuth(sunset),
              "civil_dusk_utc": clock(event(CIVIL, False), a.date)}
    if a.time:
        moment = datetime.datetime.combine(a.date, a.time.replace(tzinfo=None), utc)
        altitude, direction = position(moment, a.lat, a.lon)
        result.update(time_utc=a.time.strftime("%H:%M"), altitude=round(altitude, 1), azimuth=round(direction, 1),
                      shadow_x_height=round(1 / math.tan(math.radians(altitude)), 1) if altitude > 0 else None)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()

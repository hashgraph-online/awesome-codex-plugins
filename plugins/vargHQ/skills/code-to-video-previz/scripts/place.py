#!/usr/bin/env python3
"""Turn picture coordinates into world coordinates, for staging from a painting, a still or a video frame.

World: x right, y into the picture, z up, metres. The camera is level, at x = 0, y = 0, eye metres high.
(u, v) are fractions of the frame, top-left origin. Read them from a frame with a grid (grid.py).

    from place import Frame
    F = Frame(1000, 1028, lens=35, eye=1.37)       # add vp=(.58, .45) if the vanishing point isn't the centre
    F.depth_of(.38, .93, 1.75)     # how far away is someone 1.75 m tall, top of head at v=.38, soles at v=.93 -> 3.1 m
    F.eye_from(.93, 3.1)           # feet at v=.93, 3.1 m away: how high is the camera -> 1.37 m
    F.world(.79, .415, 3.1)        # the point at (.79, .415), 3.1 m away -> [.90, 3.1, 1.64]
    F.floor_depth(.93)             # how far away is a point on the floor at v=.93 -> 3.1 m
"""
from dataclasses import dataclass


@dataclass
class Frame:
    w: int
    h: int
    lens: float = 35
    eye: float = 1.5
    sensor: float = 36
    vp: tuple = (.5, .5)     # where lines going straight into the picture meet. Copy it to the shot's "vp"

    @property
    def fpx(self):
        return self.lens / self.sensor * max(self.w, self.h)    # the sensor spans the longer side

    def world(self, u, v, depth):
        return [round((u - self.vp[0]) * self.w * depth / self.fpx, 3), round(depth, 3),
                round(self.eye - (v - self.vp[1]) * self.h * depth / self.fpx, 3)]

    def depth_of(self, v_top, v_bottom, height_m):
        return round(self.fpx * height_m / ((v_bottom - v_top) * self.h), 3)

    def floor_depth(self, v):
        return round(self.eye * self.fpx / ((v - self.vp[1]) * self.h), 3)

    def eye_from(self, v_floor, depth):
        return round((v_floor - self.vp[1]) * self.h * depth / self.fpx, 3)

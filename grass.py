# grass.py
from pico2d import *
import os

BASE = os.path.dirname(__file__)

GROUND_TOP_Y = 90
CAVE_GROUND_DROP = 20


def kenny_path(*names):
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', *names)


class Grass:
    def __init__(self):
        self.tile = load_image(kenny_path('Ground', 'Grass', 'grass.png'))

        self.top = GROUND_TOP_Y
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h

        y = (self.bottom + self.top) / 2

        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w




class CaveGround:
    def __init__(self):
        self.tile = load_image(os.path.join(BASE, 'cave', 'cave_tile.png'))
        self.bottom_tile = load_image(os.path.join(BASE, 'cave', 'cave2_title.png'))

        self.visual_top = GROUND_TOP_Y
        self.top = self.visual_top - CAVE_GROUND_DROP
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()

        bw, bh = self.bottom_tile.w, self.bottom_tile.h
        y = bh // 2
        while y < self.visual_top:
            x = bw // 2
            while x < cw + bw:
                self.bottom_tile.draw(x, y)
                x += bw
            y += bh

        w, h = self.tile.w, self.tile.h
        y = self.visual_top - h // 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w


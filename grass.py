from pico2d import *
import os

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)

class Grass:
    def __init__(self):
        self.tile = load_image(p('EnvironmentTiles', 'Tile_1.png'))

    def get_bb(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h
        left = 0
        bottom = 0
        right = cw
        top = h
        return left, bottom, right, top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h
        y = h // 2
        x = w // 2
        while x < cw:
            self.tile.draw(x, y)
            x += w

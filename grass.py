
from pico2d import *

IMG_TILE = 'Tile_1.png'

class Grass:
    def __init__(self):
        try:
            self.tile = load_image(IMG_TILE)
        except:
            self.tile = None

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        if self.tile:
            w, h = self.tile.w, self.tile.h
            y = h // 2
            x = w // 2
            while x < cw:
                self.tile.draw(x, y)
                x += w
        else:
            draw_rectangle(0, 0, cw, 40)

from pico2d import *
import os

BASE = os.path.dirname(__file__)

def kenny_bg(*names):

    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', 'Backgrounds', *names)


class Stage1Background:
    def __init__(self):

        self.image = load_image(kenny_bg('colored_land.png'))

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2)


class Stage2Background:
    def __init__(self):
        self.image = load_image(os.path.join(BASE, 'cave', 'cave_background.png'))

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2)

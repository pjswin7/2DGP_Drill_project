from pico2d import *
import os

BASE = os.path.dirname(__file__)

def kenny_bg(*names):
    # 실제 폴더 구조: kenney_platformer-pack-redux / PNG / Backgrounds / ...
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', 'Backgrounds', *names)


class Stage1Background:
    def __init__(self):
        # 1스테이지 배경: colored_land.png
        self.image = load_image(kenny_bg('colored_land.png'))

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2)
